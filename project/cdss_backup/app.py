from flask import Flask, render_template, request, session, redirect, jsonify, flash, send_file
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import json
import os

# Import modules
from engine import get_engine
from helpers import (
    login_required, admin_required, apology,
    format_timestamp, format_differential, sanitize_input,
    log_audit, check_disclaimer_acceptance, record_disclaimer_acceptance,
    calculate_user_stats, calculate_system_stats, format_relative_time
)

# Configure application
app = Flask(__name__)

# Ensure the templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure the database
db = SQL("sqlite:///database/cdss.db")

# Initialise the diagnostic engine
engine = get_engine()

# Mention the disclaimer version
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

        # Validate the inputs
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

            # Log the registration
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
    """Log user in"""

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

        # Remember the user
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        session["role"] = rows[0]["role"]
        session["full_name"] = rows[0]["full_name"]

        # Update the last logins
        db.execute("UPDATE users SET last_login = ? WHERE id = ?",
                   datetime.now(), rows[0]["id"])

        # Log the logins
        log_audit(db, rows[0]["id"], "login", None, request.remote_addr, request.user_agent.string)

        # Check the disclaimer
        if rows[0]["must_accept_disclaimer"]:
            flash("Please review and accept the disclaimer to continue.", "warning")
            return redirect("/disclaimer")

        flash(f"Welcome back, {rows[0]['full_name']}!", "success")
        return redirect("/chat")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    user_id = session.get("user_id")
    if user_id:
        log_audit(db, user_id, "logout", None, request.remote_addr, request.user_agent.string)

    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/")


@app.route("/disclaimer", methods=["GET", "POST"])
@login_required
def disclaimer():
    """Display and accept disclaimer"""
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

    return render_template("chat.html")


@app.route("/api/diagnose", methods=["POST"])
@login_required
def api_diagnose():
    """API endpoint for diagnosis"""
    try:
        data = request.get_json()
        query = data.get("query", "")

        if not query:
            return jsonify({"success": False, "error": "No query provided"}), 400

        # Sanitise the input
        query = sanitize_input(query)

        # Get diagnosis
        result = engine.diagnose(query, return_full=False, user_id=session["user_id"])

        if not result['success']:
            return jsonify(result), 400

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
                json.dumps(result.get('symptoms_list', [])),
                result.get('symptoms_detected', 0),
                json.dumps(result),
                json.dumps(result.get('differential_diagnosis', [])),
                result.get('top_diagnosis', ''),
                result.get('top_probability', 0),
                result.get('confidence', 0),
                result.get('confidence_level', 'LOW'),
                result.get('is_urgent', False),
                result.get('is_critical', False),
                result.get('urgency_score', 0),
                result.get('processing_time_ms', 0)
            )

            result['consultation_id'] = consultation_id

        except Exception as e:
            print(f"Database error: {e}")

        # Log the query
        log_audit(db, session["user_id"], "diagnostic_query",
                 {"query": query[:100], "top_diagnosis": result.get('top_diagnosis', '')},
                 request.remote_addr, request.user_agent.string)

        return jsonify(result)

    except Exception as e:
        print(f"Diagnosis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/history")
@login_required
def history():
    """View consultation history"""
    # Get user's consultations
    consultations = db.execute(
        """SELECT id, query, top_diagnosis, confidence_score, top_probability,
                  confidence_level, is_urgent, is_critical, timestamp
           FROM consultations
           WHERE user_id = ?
           ORDER BY timestamp DESC
           LIMIT 50""",
        session["user_id"]
    )

    # Format for the display
    for c in consultations:
        c['timestamp_formatted'] = format_timestamp(c['timestamp'])
        c['confidence_formatted'] = f"{c['confidence_score'] * 100:.1f}%"

    return render_template("history.html", consultations=consultations)


@app.route("/consultation/<int:consultation_id>")
@login_required
def view_consultation(consultation_id):
    """View specific consultation"""
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
        print(f"JSON parse error: {e}")
        consultation['response_data'] = {}
        consultation['differential'] = []

    consultation['timestamp_formatted'] = format_timestamp(consultation['timestamp'])

    return render_template("consultation.html", consultation=consultation)


@app.route("/admin")
@admin_required
def admin():
    """Admin dashboard"""
    # Get the statistics
    stats = calculate_system_stats(db)

    # Top diagnoses
    top_diagnoses = db.execute(
        """SELECT top_diagnosis, COUNT(*) as count
           FROM consultations
           GROUP BY top_diagnosis
           ORDER BY count DESC
           LIMIT 10"""
    )

    # Recent consultations
    recent = db.execute(
        """SELECT c.id, c.query, c.top_diagnosis, c.timestamp, u.username, u.full_name
           FROM consultations c
           JOIN users u ON c.user_id = u.id
           ORDER BY c.timestamp DESC
           LIMIT 20"""
    )

    for r in recent:
        r['timestamp_formatted'] = format_timestamp(r['timestamp'])

    # Recent audit logs
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
    """User management"""
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
    """Export consultation as JSON"""
    consultation = db.execute(
        "SELECT * FROM consultations WHERE id = ? AND user_id = ?",
        consultation_id, session["user_id"]
    )

    if not consultation:
        return apology("consultation not found", 404)

    # Log the exports
    log_audit(db, session["user_id"], "export_consultation",
             {"consultation_id": consultation_id}, request.remote_addr, request.user_agent.string)

    # Return as JSON file
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

    # Search in queries and diagnoses
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
    """User profile"""
    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])[0]

    # Get user stats
    stats = calculate_user_stats(db, session["user_id"])

    # Most diagnosed conditions
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


@app.route("/api/stats")
@login_required
def api_stats():
    """API endpoint for dashboard statistics"""
    stats = {
        'total_consultations': db.execute(
            "SELECT COUNT(*) as count FROM consultations WHERE user_id = ?",
            session["user_id"]
        )[0]['count'],
        'urgent_count': db.execute(
            "SELECT COUNT(*) as count FROM consultations WHERE user_id = ? AND is_urgent = 1",
            session["user_id"]
        )[0]['count'],
        'high_confidence': db.execute(
            "SELECT COUNT(*) as count FROM consultations WHERE user_id = ? AND confidence_level = 'HIGH'",
            session["user_id"]
        )[0]['count']
    }

    return jsonify(stats)


@app.errorhandler(404)
def not_found(e):
    return apology("page not found", 404)


@app.errorhandler(500)
def internal_error(e):
    return apology("internal server error", 500)


if __name__ == "__main__":
    # Check if the database exists
    if not os.path.exists("cdss.db"):
        print("⚠️  Database not found. Please run: python init_db.py")
        print()

    # Check if the model exists
    if not os.path.exists("trained_model.json"):
        print("⚠️  Model file not found: trained_model_v2.json")
        print("    Please ensure trained_model_v2.json is in the project root directory.")
        print()

    print("=" * 70)
    print("🏥 Clinical Decision Support System v2.0")
    print("=" * 70)
    print("Starting server on http://localhost:5000")
    print("=" * 70)
    print()

    app.run(debug=True, host="0.0.0.0", port=5000)
