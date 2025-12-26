"""
app.py - Main Flask Application for Clinical Decision Support System

AI Assistance Disclosure:
This project was started during Week 6 of CS50 and developed over approximately
two months. I used AI tools (Claude / Gemini) as a support resource during
development.

PROJECT OWNERSHIP:
- I designed the overall structure of the project
- I chose which features to build and how they should behave
- I made the key technical decisions throughout development

HOW AI WAS USED:
- Helping troubleshoot errors and unexpected behaviour
- Assisting when I was stuck on specific problems
- Providing examples or suggestions that I then worked from

All code included in this repository was either written by me or reviewed,
adapted, and implemented by me as part of the final system.

"""
from flask import Flask, render_template, request, session, redirect, jsonify, flash, send_file
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import helpers (your existing file)
from helpers import (
    login_required, admin_required, apology,
    format_timestamp, format_differential, sanitize_input,
    log_audit, check_disclaimer_acceptance, record_disclaimer_acceptance,
    calculate_user_stats, calculate_system_stats, format_relative_time
)

# Try to import enhanced engine, fall back to basic if not available
try:
    from engine import get_engine, DiagnosticEngine
    logger.info("✓ Enhanced engine loaded")
    ENHANCED_ENGINE = True
except ImportError:
    logger.warning("⚠️  Enhanced engine not found - using basic mode")
    ENHANCED_ENGINE = False
    # We'll define a basic fallback below

# Try to import vital signs module
try:
    from vital_signs import VitalSigns, VitalSignsAnalyzer
    logger.info("✓ Vital signs module loaded")
    VITALS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  Vital signs module not available")
    VITALS_AVAILABLE = False

# Try to import risk scores module
try:
    from risk_scores import RiskScoreCalculator
    logger.info("✓ Risk scores module loaded")
    RISK_SCORES_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  Risk scores module not available")
    RISK_SCORES_AVAILABLE = False



if not ENHANCED_ENGINE:
    class BasicEngine:
        """Basic fallback engine using old approach"""
        def __init__(self):
            logger.info("Loading basic diagnostic engine")
            try:
                with open('trained_model.json', 'r') as f:
                    self.model = json.load(f)
                self.symptom_to_disease = self.model.get('symptom_to_disease', {})
                self.disease_priors = self.model.get('priors', {})
                logger.info(f"✓ Basic engine loaded: {len(self.disease_priors)} diseases")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.model = {}
                self.symptom_to_disease = {}
                self.disease_priors = {}

        def diagnose(self, query, return_full=True, user_id=None):
            """Basic diagnosis - returns dict format"""
            try:
                # Simple keyword matching for now
                symptoms = []
                query_lower = query.lower()

                # Extract symptoms from query (basic)
                for symptom in self.symptom_to_disease.keys():
                    if symptom.replace('_', ' ') in query_lower:
                        symptoms.append(symptom)

                if not symptoms:
                    return {
                        'success': False,
                        'error': 'No symptoms detected',
                        'query': query
                    }

                # Calculate probabilities (simple Bayesian)
                posteriors = {}
                for disease in self.disease_priors:
                    prob = self.disease_priors[disease]
                    for symptom in symptoms:
                        if disease in self.symptom_to_disease.get(symptom, {}):
                            prob *= self.symptom_to_disease[symptom][disease]
                    if prob > 0:
                        posteriors[disease] = prob

                # Normalize
                total = sum(posteriors.values())
                if total > 0:
                    posteriors = {d: p/total for d, p in posteriors.items()}

                # Sort
                sorted_diseases = sorted(posteriors.items(), key=lambda x: x[1], reverse=True)

                if not sorted_diseases:
                    return {
                        'success': False,
                        'error': 'Unable to generate diagnosis',
                        'query': query
                    }

                top_disease, top_prob = sorted_diseases[0]

                # Build differential
                differential = []
                for rank, (disease, prob) in enumerate(sorted_diseases[:10], 1):
                    differential.append({
                        'rank': rank,
                        'disease': disease,
                        'probability': round(prob, 4),
                        'confidence': 'MODERATE' if prob > 0.3 else 'LOW'
                    })

                return {
                    'success': True,
                    'query': query,
                    'symptoms_detected': len(symptoms),
                    'symptoms_list': symptoms,
                    'top_diagnosis': top_disease,
                    'top_probability': round(top_prob, 4),
                    'confidence': 0.6,
                    'confidence_level': 'MODERATE',
                    'differential_diagnosis': differential,
                    'recommendations': [
                        '⚠️  Using basic engine - install enhanced engine for better accuracy',
                        '✓ Clinical correlation required',
                        '📋 Confirmatory testing recommended'
                    ],
                    'is_urgent': False,
                    'is_critical': False,
                    'urgency_score': 3,
                    'warnings': [],
                    'timestamp': datetime.utcnow().isoformat()
                }

            except Exception as e:
                logger.error(f"Diagnosis error: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'query': query
                }

    def get_engine():
        """Return basic engine instance"""
        global _basic_engine
        if '_basic_engine' not in globals():
            _basic_engine = BasicEngine()
        return _basic_engine



app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure database
db = SQL("sqlite:///cdss.db")

# Initialize engine
try:
    engine = get_engine()
    logger.info("✓ Diagnostic engine initialized")
except Exception as e:
    logger.error(f"Failed to initialize engine: {e}")
    engine = None

# Initialize vital signs analyzer if available
if VITALS_AVAILABLE:
    try:
        vital_analyzer = VitalSignsAnalyzer()
        logger.info("✓ Vital signs analyzer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize vital analyzer: {e}")
        vital_analyzer = None
        VITALS_AVAILABLE = False
else:
    vital_analyzer = None

# Initialize risk calculator if available
if RISK_SCORES_AVAILABLE:
    try:
        risk_calculator = RiskScoreCalculator()
        logger.info("✓ Risk score calculator initialized")
    except Exception as e:
        logger.error(f"Failed to initialize risk calculator: {e}")
        risk_calculator = None
        RISK_SCORES_AVAILABLE = False
else:
    risk_calculator = None

# Disclaimer version
DISCLAIMER_VERSION = "2.0"


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



@app.route("/")
def index():
    """Landing page"""
    if session.get("user_id"):
        return redirect("/chat")
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email")
        full_name = request.form.get("full_name")
        institution = request.form.get("institution")
        license_number = request.form.get("license_number")

        # Validate inputs
        if not username:
            return apology("must provide username", 400)
        if len(username) < 3:
            return apology("username must be at least 3 characters", 400)
        if not password:
            return apology("must provide password", 400)
        if len(password) < 6:
            return apology("password must be at least 6 characters", 400)
        if not confirmation:
            return apology("must confirm password", 400)
        if password != confirmation:
            return apology("passwords don't match", 400)
        if not email:
            return apology("must provide email", 400)
        if not full_name:
            return apology("must provide full name", 400)

        # Hash password
        hash_pw = generate_password_hash(password)

        # Insert user
        try:
            user_id = db.execute(
                "INSERT INTO users (username, password_hash, email, full_name, institution, license_number) VALUES (?, ?, ?, ?, ?, ?)",
                username, hash_pw, email, full_name, institution, license_number
            )

            # Log registration
            log_audit(db, user_id, "register", {"username": username}, request.remote_addr, request.user_agent.string)

            # Auto-login
            session["user_id"] = user_id
            session["username"] = username
            session["role"] = "doctor"
            session["full_name"] = full_name

            flash("Registration successful! Please review the disclaimer.", "success")
            return redirect("/disclaimer")

        except Exception as e:
            return apology("username or email already exists", 400)

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("must provide username", 403)
        if not password:
            return apology("must provide password", 403)

        # Query database
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], password):
            return apology("invalid username and/or password", 403)

        # Check if account is active
        if not rows[0]["is_active"]:
            return apology("account is disabled", 403)

        # Remember user
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        session["role"] = rows[0]["role"]
        session["full_name"] = rows[0]["full_name"]

        # Update last login
        db.execute("UPDATE users SET last_login = ? WHERE id = ?",
                   datetime.now(), rows[0]["id"])

        # Log login
        log_audit(db, rows[0]["id"], "login", None, request.remote_addr, request.user_agent.string)

        # Check disclaimer
        if rows[0]["must_accept_disclaimer"]:
            flash("Please review and accept the disclaimer to continue.", "warning")
            return redirect("/disclaimer")

        flash(f"Welcome back, {rows[0]['full_name']}!", "success")
        return redirect("/chat")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        log_audit(db, user_id, "logout", None, request.remote_addr, request.user_agent.string)

    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/")


@app.route("/disclaimer", methods=["GET", "POST"])
@login_required
def disclaimer():
    if request.method == "POST":
        accept = request.form.get("accept")

        if accept == "yes":
            record_disclaimer_acceptance(db, session["user_id"], request.remote_addr)
            log_audit(db, session["user_id"], "accept_disclaimer",
                     {"version": DISCLAIMER_VERSION}, request.remote_addr, request.user_agent.string)

            flash("Disclaimer accepted. You may now use the system.", "success")
            return redirect("/chat")
        else:
            flash("You must accept the disclaimer to use the system.", "warning")
            return redirect("/disclaimer")

    else:
        return render_template("disclaimer.html", version=DISCLAIMER_VERSION)


@app.route("/chat")
@login_required
def chat():
    """Main chat interface"""
    # Check disclaimer
    if not check_disclaimer_acceptance(db, session["user_id"]):
        flash("Please accept the disclaimer first.", "warning")
        return redirect("/disclaimer")

    # Pass feature flags to template
    features = {
        'enhanced_engine': ENHANCED_ENGINE,
        'vitals_input': VITALS_AVAILABLE,
        'risk_scores': RISK_SCORES_AVAILABLE,
    }

    return render_template("chat.html", features=features)



@app.route("/api/diagnose", methods=["POST"])
@login_required
def api_diagnose():

    try:
        data = request.get_json()
        query = data.get("query", "")

        if not query:
            return jsonify({"success": False, "error": "No query provided"}), 400

        # Sanitize input
        query = sanitize_input(query)

        # Check if engine is available
        if engine is None:
            return jsonify({
                "success": False,
                "error": "Diagnostic engine not available"
            }), 500

        # Get diagnosis
        result = engine.diagnose(query, return_full=False, user_id=session["user_id"])

        # Handle both dict and object returns
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
        else:
            result_dict = result

        if not result_dict.get('success'):
            return jsonify(result_dict), 400

        # Analyze vital signs if provided and available
        vitals_data = data.get("vitals", {})
        if vitals_data and VITALS_AVAILABLE and vital_analyzer:
            try:
                vitals = VitalSigns(
                    temperature_c=vitals_data.get('temperature_c'),
                    heart_rate_bpm=vitals_data.get('heart_rate_bpm'),
                    respiratory_rate_bpm=vitals_data.get('respiratory_rate_bpm'),
                    systolic_bp_mmhg=vitals_data.get('systolic_bp_mmhg'),
                    diastolic_bp_mmhg=vitals_data.get('diastolic_bp_mmhg'),
                    spo2_percent=vitals_data.get('spo2_percent'),
                    gcs_score=vitals_data.get('gcs_score'),
                    age_years=vitals_data.get('age_years')
                )

                vitals_analysis = vital_analyzer.analyze(vitals)
                result_dict['vitals_analysis'] = vitals_analysis.to_dict()

                # Escalate if critical vitals
                if vitals_analysis.red_flags:
                    critical_flags = [rf for rf in vitals_analysis.red_flags
                                     if rf.level.value in ['critical', 'emergency']]
                    if critical_flags:
                        result_dict['is_critical'] = True
                        result_dict['urgency_score'] = 10
                        if 'warnings' not in result_dict:
                            result_dict['warnings'] = []
                        result_dict['warnings'].insert(0,
                            f"🚨 CRITICAL VITAL SIGNS: {len(critical_flags)} emergency alerts")

            except Exception as e:
                logger.error(f"Vitals analysis error: {e}")

        # Save to database
        try:
            consultation_id = db.execute(
                """INSERT INTO consultations
                   (user_id, session_id, query, symptoms_detected, symptom_count,
                    response, differential_diagnosis, top_diagnosis, top_probability,
                    confidence_score, confidence_level, is_urgent, is_critical,
                    urgency_score, duration_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                session["user_id"],
                session.get("session_id", ""),
                query,
                json.dumps(result_dict.get('symptoms_list', [])),
                result_dict.get('symptoms_detected', 0),
                json.dumps(result_dict),
                json.dumps(result_dict.get('differential_diagnosis', [])),
                result_dict.get('top_diagnosis', ''),
                result_dict.get('top_probability', 0),
                result_dict.get('confidence', 0),
                result_dict.get('confidence_level', 'LOW'),
                result_dict.get('is_urgent', False),
                result_dict.get('is_critical', False),
                result_dict.get('urgency_score', 0),
                result_dict.get('processing_time_ms', 0)
            )

            result_dict['consultation_id'] = consultation_id

        except Exception as e:
            logger.error(f"Database error: {e}")

        # Log query
        log_audit(db, session["user_id"], "diagnostic_query",
                 {"query": query[:100], "top_diagnosis": result_dict.get('top_diagnosis', '')},
                 request.remote_addr, request.user_agent.string)

        return jsonify(result_dict)

    except Exception as e:
        logger.error(f"Diagnosis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/system/status")
def api_system_status():
    status = {
        "engine": {
            "type": "enhanced" if ENHANCED_ENGINE else "basic",
            "status": "operational" if engine else "unavailable"
        },
        "vitals": {
            "available": VITALS_AVAILABLE,
            "status": "operational" if vital_analyzer else "unavailable"
        },
        "risk_scores": {
            "available": RISK_SCORES_AVAILABLE,
            "status": "operational" if risk_calculator else "unavailable"
        },
        "database": {
            "connected": True,
            "status": "operational"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

    return jsonify(status)


@app.route("/history")
@login_required
def history():
    consultations = db.execute(
        """SELECT id, query, top_diagnosis, confidence_score, top_probability,
                  confidence_level, is_urgent, is_critical, timestamp
           FROM consultations
           WHERE user_id = ?
           ORDER BY timestamp DESC
           LIMIT 50""",
        session["user_id"]
    )

    for c in consultations:
        c['timestamp_formatted'] = format_timestamp(c['timestamp'])
        c['confidence_formatted'] = f"{c['confidence_score'] * 100:.1f}%"

    return render_template("history.html", consultations=consultations)


@app.route("/consultation/<int:consultation_id>")
@login_required
def view_consultation(consultation_id):
    consultation = db.execute(
        "SELECT * FROM consultations WHERE id = ? AND user_id = ?",
        consultation_id, session["user_id"]
    )

    if not consultation:
        return apology("consultation not found", 404)

    consultation = consultation[0]

    # Parse JSON fields
    try:
        consultation['response_data'] = json.loads(consultation['response'])
        consultation['differential'] = format_differential(
            consultation['response_data'].get('differential_diagnosis', [])
        )
    except Exception as e:
        logger.error(f"JSON parse error: {e}")
        consultation['response_data'] = {}
        consultation['differential'] = []

    consultation['timestamp_formatted'] = format_timestamp(consultation['timestamp'])

    return render_template("consultation.html", consultation=consultation)


@app.route("/admin")
@admin_required
def admin():
    stats = calculate_system_stats(db)

    top_diagnoses = db.execute(
        """SELECT top_diagnosis, COUNT(*) as count
           FROM consultations
           GROUP BY top_diagnosis
           ORDER BY count DESC
           LIMIT 10"""
    )

    recent = db.execute(
        """SELECT c.id, c.query, c.top_diagnosis, c.timestamp, u.username, u.full_name
           FROM consultations c
           JOIN users u ON c.user_id = u.id
           ORDER BY c.timestamp DESC
           LIMIT 20"""
    )

    for r in recent:
        r['timestamp_formatted'] = format_timestamp(r['timestamp'])

    audit_logs = db.execute(
        """SELECT a.action, a.timestamp, a.ip_address, u.username, u.full_name
           FROM audit_log a
           LEFT JOIN users u ON a.user_id = u.id
           ORDER BY a.timestamp DESC
           LIMIT 30"""
    )

    for log in audit_logs:
        log['timestamp_formatted'] = format_timestamp(log['timestamp'])

    return render_template("admin.html",
                          stats=stats,
                          top_diagnoses=top_diagnoses,
                          recent=recent,
                          audit_logs=audit_logs)


@app.route("/admin/users")
@admin_required
def admin_users():
    users = db.execute(
        """SELECT id, username, email, full_name, role, institution,
                  created_at, last_login, is_active
           FROM users
           ORDER BY created_at DESC"""
    )

    for user in users:
        user['created_formatted'] = format_timestamp(user['created_at'])
        user['last_login_formatted'] = format_timestamp(user['last_login']) if user['last_login'] else "Never"

    return render_template("admin_users.html", users=users)


@app.route("/admin/toggle_user/<int:user_id>", methods=["POST"])
@admin_required
def toggle_user(user_id):
    """Toggle user active status"""
    if user_id == session["user_id"]:
        flash("Cannot disable your own account", "danger")
        return redirect("/admin/users")

    user = db.execute("SELECT is_active FROM users WHERE id = ?", user_id)
    if user:
        new_status = not user[0]['is_active']
        db.execute("UPDATE users SET is_active = ? WHERE id = ?", new_status, user_id)

        action = "enabled" if new_status else "disabled"
        flash(f"User account {action}", "success")

        log_audit(db, session["user_id"], f"user_{action}",
                 {"target_user_id": user_id}, request.remote_addr, request.user_agent.string)

    return redirect("/admin/users")


@app.route("/export/<int:consultation_id>")
@login_required
def export_consultation(consultation_id):
    consultation = db.execute(
        "SELECT * FROM consultations WHERE id = ? AND user_id = ?",
        consultation_id, session["user_id"]
    )

    if not consultation:
        return apology("consultation not found", 404)

    log_audit(db, session["user_id"], "export_consultation",
             {"consultation_id": consultation_id}, request.remote_addr, request.user_agent.string)

    response = jsonify(consultation[0])
    response.headers['Content-Disposition'] = f'attachment; filename=consultation_{consultation_id}.json'
    return response


@app.route("/search")
@login_required
def search():
    """Search consultations"""
    query = request.args.get("q", "")

    if not query:
        return render_template("search.html", results=[], query="")

    results = db.execute(
        """SELECT id, query, top_diagnosis, confidence_score, confidence_level, timestamp
           FROM consultations
           WHERE user_id = ? AND (query LIKE ? OR top_diagnosis LIKE ?)
           ORDER BY timestamp DESC
           LIMIT 50""",
        session["user_id"], f"%{query}%", f"%{query}%"
    )

    for r in results:
        r['timestamp_formatted'] = format_timestamp(r['timestamp'])
        r['confidence_formatted'] = f"{r['confidence_score'] * 100:.1f}%"

    return render_template("search.html", results=results, query=query)


@app.route("/profile")
@login_required
def profile():
    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]
    stats = calculate_user_stats(db, session["user_id"])

    top_conditions = db.execute(
        """SELECT top_diagnosis, COUNT(*) as count
           FROM consultations
           WHERE user_id = ?
           GROUP BY top_diagnosis
           ORDER BY count DESC
           LIMIT 5""",
        session["user_id"]
    )

    user['created_formatted'] = format_timestamp(user['created_at'])
    user['last_login_formatted'] = format_timestamp(user['last_login']) if user['last_login'] else "Never"

    return render_template("profile.html", user=user, stats=stats, top_conditions=top_conditions)


@app.errorhandler(404)
def not_found(e):
    return apology("page not found", 404)


@app.errorhandler(500)
def internal_error(e):
    return apology("internal server error", 500)



if __name__ == "__main__":
    # Check database
    if not os.path.exists("cdss.db"):
        logger.warning("⚠️  Database not found. Run: python init_db.py")

    # Check model
    if not os.path.exists("trained_model.json") and not os.path.exists("trained_model_v2.json"):
        logger.warning("⚠️  No model file found")

    # Print startup info
    print("=" * 70)
    print("🏥 CDSS v2.0 - Starting")
    print("=" * 70)
    print(f"✓ Engine: {'Enhanced' if ENHANCED_ENGINE else 'Basic'}")
    print(f"✓ Vital Signs: {'Available' if VITALS_AVAILABLE else 'Not installed'}")
    print(f"✓ Risk Scores: {'Available' if RISK_SCORES_AVAILABLE else 'Not installed'}")
    print("=" * 70)
    print("Server starting on http://localhost:5000")
    print("=" * 70)

    app.run(debug=True, host="0.0.0.0", port=5000)
