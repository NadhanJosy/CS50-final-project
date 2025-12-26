"""
helpers.py - Helper Functions for Authentication, Validation, and Utilities

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
from flask import redirect, render_template, session, request
from functools import wraps
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            logger.warning(f"Unauthorized access attempt to {request.path}")
            return redirect("/login")

        # Update last activity
        session['last_activity'] = datetime.utcnow().isoformat()

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        if session.get("role") not in ["admin"]:
            logger.warning(
                f"Unauthorized admin access attempt by user {session.get('user_id')} "
                f"to {request.path}"
            )
            return apology("Admin access required", 403)
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get("user_id") is None:
                return redirect("/login")
            if session.get("role") not in allowed_roles:
                return apology(f"Access restricted to: {', '.join(allowed_roles)}", 403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator



def apology(message: str, code: int = 400):
    """
    Render an apology to user with enhanced context
    """
    logger.info(f"Apology rendered: {code} - {message}")
    return render_template("apology.html", message=message, code=code), code



def format_timestamp(timestamp, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp for display with timezone support
    """
    if not timestamp:
        return "Never"

    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp

        return dt.strftime(format_str)
    except Exception as e:
        logger.error(f"Timestamp formatting error: {e}")
        return str(timestamp)


def format_relative_time(timestamp) -> str:

    if not timestamp:
        return "Never"

    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp

        now = datetime.utcnow()
        diff = now - dt

        seconds = diff.total_seconds()

        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            mins = int(seconds / 60)
            return f"{mins} minute{'s' if mins != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return format_timestamp(dt, "%b %d, %Y")
    except Exception as e:
        logger.error(f"Relative time formatting error: {e}")
        return "Unknown"


def format_confidence(confidence: float) -> str:
    if confidence is None:
        return "N/A"
    return f"{confidence * 100:.1f}%"


def format_probability(prob: float) -> str:
    if prob is None:
        return "N/A"
    return f"{prob * 100:.2f}%"


def get_confidence_color(level: str) -> str:
    colors = {
        "HIGH": "success",
        "MODERATE": "warning",
        "LOW": "danger",
        "VERY LOW": "danger"
    }
    return colors.get(level, "secondary")


def get_urgency_color(urgency_score: int) -> str:
    if urgency_score >= 8:
        return "danger"
    elif urgency_score >= 6:
        return "warning"
    elif urgency_score >= 4:
        return "info"
    else:
        return "secondary"


def format_differential(differential: List[Dict]) -> List[Dict]:
    formatted = []
    for item in differential:
        formatted.append({
            'rank': item.get('rank', 0),
            'disease': item['disease'],
            'probability': item['probability'],
            'probability_pct': f"{item['probability'] * 100:.1f}%",
            'confidence': item['confidence'],
            'confidence_color': get_confidence_color(item['confidence']),
            'supporting_symptoms': item.get('supporting_symptoms', []),
            'symptom_match_scores': item.get('symptom_match_scores', []),
            'is_critical': item.get('is_critical', False),
            'is_urgent': item.get('is_urgent', False)
        })
    return formatted




def sanitize_input(text: str, max_length: int = 5000) -> str:

    if not text:
        return ""

    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    # Remove excessive whitespace
    text = " ".join(text.split())

    # Limit length
    text = text[:max_length]

    # Remove potentially dangerous HTML/JS
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # event handlers
        r'<iframe',
        r'<object',
        r'<embed'
    ]

    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    return text.strip()


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> tuple[bool, str]:

    if not username:
        return False, "Username is required"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, hyphens, and underscores"
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:

    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if len(password) > 128:
        return False, "Password too long"

    # Check for basic complexity
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_number = bool(re.search(r'\d', password))

    if not (has_letter and has_number):
        return False, "Password must contain both letters and numbers"

    return True, ""



def log_audit(db, user_id: Optional[int], action: str,
             details: Optional[Dict] = None,
             severity: str = "info",
             ip_address: Optional[str] = None,
             user_agent: Optional[str] = None):

    try:
        # Get request context
        if not ip_address:
            ip_address = request.remote_addr if request else None
        if not user_agent:
            user_agent = request.user_agent.string if request else None

        # Categorize action
        category = categorize_action(action)

        # Get username for denormalization
        username = None
        if user_id:
            try:
                user = db.execute("SELECT username FROM users WHERE id = ?", user_id)
                if user:
                    username = user[0]['username']
            except:
                pass

        # Insert audit log
        db.execute("""
            INSERT INTO audit_log (
                user_id, username, action, action_category,
                details, severity, ip_address, user_agent,
                request_method, request_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            user_id, username, action, category,
            json.dumps(details) if details else None,
            severity, ip_address, user_agent,
            request.method if request else None,
            request.path if request else None
        )

        logger.debug(f"Audit log: {action} by user {user_id}")

    except Exception as e:
        logger.error(f"Audit logging error: {e}")


def categorize_action(action: str) -> str:
    """Categorize audit action"""
    categories = {
        'login': 'auth',
        'logout': 'auth',
        'register': 'auth',
        'accept_disclaimer': 'auth',
        'diagnostic_query': 'query',
        'export_consultation': 'data',
        'view_consultation': 'access',
        'user_enabled': 'admin',
        'user_disabled': 'admin',
    }
    return categories.get(action, 'other')



def check_disclaimer_acceptance(db, user_id: int) -> bool:
    """Check if user has accepted current disclaimer"""
    try:
        result = db.execute(
            "SELECT must_accept_disclaimer FROM users WHERE id = ?",
            user_id
        )
        if result and len(result) > 0:
            return not result[0]['must_accept_disclaimer']
        return False
    except Exception as e:
        logger.error(f"Disclaimer check error: {e}")
        return False


def record_disclaimer_acceptance(db, user_id: int,
                                version: str = "2.0",
                                ip_address: Optional[str] = None):
    """Record disclaimer acceptance"""
    try:
        if not ip_address:
            ip_address = request.remote_addr if request else None

        db.execute("""
            INSERT INTO disclaimer_acceptances (user_id, version, ip_address)
            VALUES (?, ?, ?)
        """, user_id, version, ip_address)

        db.execute(
            "UPDATE users SET must_accept_disclaimer = 0 WHERE id = ?",
            user_id
        )

        logger.info(f"Disclaimer accepted by user {user_id}")
    except Exception as e:
        logger.error(f"Disclaimer recording error: {e}")
        raise



def is_session_expired() -> bool:
    """Check if user session has expired"""
    last_activity = session.get('last_activity')
    if not last_activity:
        return True

    try:
        last_dt = datetime.fromisoformat(last_activity)
        timeout = timedelta(hours=2)  # 2 hour timeout
        return (datetime.utcnow() - last_dt) > timeout
    except:
        return True


def refresh_session():
    """Refresh session timestamp"""
    session['last_activity'] = datetime.utcnow().isoformat()
    session.modified = True


def prepare_export_data(consultation: Dict) -> Dict:
    """Prepare consultation data for export"""
    # Remove sensitive fields
    export_data = {k: v for k, v in consultation.items()
                   if k not in ['user_id', 'ip_address', 'session_id']}

    # Parse JSON fields
    json_fields = ['symptoms_detected', 'response', 'differential_diagnosis']
    for field in json_fields:
        if field in export_data and isinstance(export_data[field], str):
            try:
                export_data[field] = json.loads(export_data[field])
            except:
                pass

    return export_data



def calculate_user_stats(db, user_id: int) -> Dict:
    """Calculate comprehensive user statistics"""
    stats = {}

    try:
        # Total consultations
        result = db.execute(
            "SELECT COUNT(*) as count FROM consultations WHERE user_id = ?",
            user_id
        )
        stats['total_consultations'] = result[0]['count'] if result else 0

        # This week
        result = db.execute("""
            SELECT COUNT(*) as count FROM consultations
            WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
        """, user_id)
        stats['consultations_this_week'] = result[0]['count'] if result else 0

        # This month
        result = db.execute("""
            SELECT COUNT(*) as count FROM consultations
            WHERE user_id = ? AND timestamp >= datetime('now', '-30 days')
        """, user_id)
        stats['consultations_this_month'] = result[0]['count'] if result else 0

        # Urgent cases
        result = db.execute("""
            SELECT COUNT(*) as count FROM consultations
            WHERE user_id = ? AND is_urgent = 1
        """, user_id)
        stats['urgent_cases'] = result[0]['count'] if result else 0

        # Average confidence
        result = db.execute("""
            SELECT AVG(confidence_score) as avg FROM consultations
            WHERE user_id = ?
        """, user_id)
        stats['avg_confidence'] = round(result[0]['avg'], 3) if result and result[0]['avg'] else 0

        # Most common diagnoses
        result = db.execute("""
            SELECT top_diagnosis, COUNT(*) as count
            FROM consultations
            WHERE user_id = ?
            GROUP BY top_diagnosis
            ORDER BY count DESC
            LIMIT 5
        """, user_id)
        stats['top_diagnoses'] = result if result else []

    except Exception as e:
        logger.error(f"Stats calculation error: {e}")

    return stats


def calculate_system_stats(db) -> Dict:
    """Calculate system-wide statistics"""
    stats = {}

    try:
        # Total users
        result = db.execute("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = result[0]['count'] if result else 0

        # Active users (last 7 days)
        result = db.execute("""
            SELECT COUNT(*) as count FROM users
            WHERE last_login >= datetime('now', '-7 days')
        """)
        stats['active_users_7d'] = result[0]['count'] if result else 0

        # Total consultations
        result = db.execute("SELECT COUNT(*) as count FROM consultations")
        stats['total_consultations'] = result[0]['count'] if result else 0

        # Today's consultations
        result = db.execute("""
            SELECT COUNT(*) as count FROM consultations
            WHERE DATE(timestamp) = DATE('now')
        """)
        stats['consultations_today'] = result[0]['count'] if result else 0

        # Average confidence
        result = db.execute("SELECT AVG(confidence_score) as avg FROM consultations")
        stats['avg_confidence'] = round(result[0]['avg'], 3) if result and result[0]['avg'] else 0

    except Exception as e:
        logger.error(f"System stats error: {e}")

    return stats



def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_json_safe(json_str: str, default=None):
    if not json_str:
        return default
    try:
        return json.loads(json_str)
    except:
        return default


def get_client_ip() -> str:
    if request:
        if request.headers.getlist("X-Forwarded-For"):
            return request.headers.getlist("X-Forwarded-For")[0]
        return request.remote_addr
    return "unknown"


__all__ = [
    'login_required',
    'admin_required',
    'role_required',
    'apology',
    'format_timestamp',
    'format_relative_time',
    'format_confidence',
    'format_differential',
    'sanitize_input',
    'validate_email',
    'validate_username',
    'validate_password',
    'log_audit',
    'check_disclaimer_acceptance',
    'record_disclaimer_acceptance',
    'calculate_user_stats',
    'calculate_system_stats'
]
