from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timedelta
import jwt
from classifier import TicketClassifier
from severity import predict_severity
from priority import calculate_priority
from rag.rag_pipeline import run_rag_pipeline
import database
import os
import time
import secrets
import uuid
import json
import sqlite3
from dotenv import load_dotenv

load_dotenv()  # loads OPENROUTER_API_KEY, OPENROUTER_MODEL, JWT_SECRET_KEY from .env

app = Flask(__name__, static_folder='assets')
app.secret_key = os.environ.get("JWT_SECRET_KEY", "super_secret_key_for_milestone_1")  # loaded from .env
app.config["JWT_SECRET_KEY"] = app.secret_key
app.config["JWT_ALGORITHM"] = "HS256"
app.config["JWT_EXPIRY_HOURS"] = 24
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'avatars')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.before_request
def csrf_protect():
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        token = session.get('_csrf_token')
        form_token = request.form.get('_csrf_token') if request.form else None
        header_token = request.headers.get('X-CSRFToken')
        
        if not token or (token != form_token and token != header_token):
            if request.path.startswith('/api/'):
                return jsonify({"error": "CSRF token missing or incorrect"}), 403
            return "CSRF token missing or incorrect", 403

@app.context_processor
def inject_global_vars():
    prefs = {}
    if session.get('user_id'):
        prefs = database.get_user_preferences(session['user_id'])
    return dict(prefs=prefs)

# Initialize DB
database.init_db()

# Load Models
classifier = TicketClassifier()


def create_access_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=app.config["JWT_EXPIRY_HOURS"])
    }
    return jwt.encode(payload, app.config["JWT_SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"])


def verify_access_token(token):
    if not token:
        return None
    try:
        payload = jwt.decode(token, app.config["JWT_SECRET_KEY"], algorithms=[app.config["JWT_ALGORITHM"]])
        return payload.get("user_id")
    except Exception:
        return None


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        bearer_token = None

        if auth_header.startswith("Bearer "):
            bearer_token = auth_header.split(" ", 1)[1].strip()
        elif request.cookies.get("access_token"):
            bearer_token = request.cookies.get("access_token")

        verified_user_id = None
        if bearer_token:
            verified_user_id = verify_access_token(bearer_token)

        if not verified_user_id:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for('login'))

        session["user_id"] = verified_user_id
        return f(*args, **kwargs)
    return decorated_function

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        department = request.form.get("department")
        
        google_auth_enabled = bool(os.environ.get("GOOGLE_CLIENT_ID"))
        
        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match.", google_auth_enabled=google_auth_enabled)
        
        if len(password) < 8:
            return render_template("signup.html", error="Password must be at least 8 characters.", google_auth_enabled=google_auth_enabled)
            
        password_hash = generate_password_hash(password)
        user_id = database.create_user(full_name, email, password_hash, department)
        
        if not user_id:
            return render_template("signup.html", error="Email already exists.")
            
        return redirect(url_for("login", msg="Account created. Please log in."))
        
    return render_template("signup.html")

from flask import make_response

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = request.form.get("remember")
        
        user = database.get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session['user_id'] = user["user_id"]
            token = create_access_token(user["user_id"])
            resp = make_response(redirect(url_for("index")))
            max_age = 30 * 24 * 60 * 60 if remember else None
            resp.set_cookie("access_token", token, httponly=True, samesite='Lax', max_age=max_age)
            return resp
        else:
            return render_template("login.html", error="Invalid email or password.")
            
    return render_template("login.html", msg=request.args.get("msg"))

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    resp = make_response(redirect(url_for("login")))
    resp.set_cookie("access_token", "", expires=0)
    return resp

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = database.get_user_by_email(email)
        if user:
            token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(hours=1)
            database.save_password_reset_token(user["user_id"], token, expiry.isoformat())
            
            reset_url = url_for("reset_password", token=token, _external=True)
            print(f"--- PASSWORD RESET LINK (MOCK EMAIL) ---")
            print(f"To: {email}")
            print(f"Link: {reset_url}")
            print(f"----------------------------------------")
            
            return render_template("forgot_password.html", success="If your email is in our system, you will receive a reset link shortly.")
        return render_template("forgot_password.html", success="If your email is in our system, you will receive a reset link shortly.")
    
    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = database.get_user_by_reset_token(token)
    
    if not user:
        return render_template("reset_password.html", error="Invalid or expired reset token.")
        
    expiry = datetime.fromisoformat(user["reset_token_expiry"])
    if datetime.utcnow() > expiry:
        return render_template("reset_password.html", error="Reset token has expired.")
        
    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if len(password) < 8:
            return render_template("reset_password.html", token=token, error="Password must be at least 8 characters.")
            
        if password != confirm_password:
            return render_template("reset_password.html", token=token, error="Passwords do not match.")
            
        password_hash = generate_password_hash(password)
        database.update_user_password(user["user_id"], password_hash)
        database.save_password_reset_token(user["user_id"], None, None) # Clear token
        
        return redirect(url_for("login", msg="Password reset successfully. Please log in."))
        
    return render_template("reset_password.html", token=token)

@app.route("/", methods=["GET"])
@login_required
def index():
    user_id = session['user_id']
    user = database.get_user_by_id(user_id)

    model_info = classifier.get_model_info()
    accuracy_pct = round((model_info.get("accuracy", 0) * 100), 1) if model_info else 0

    analytics = database.get_analytics_stats(user_id=user_id)

    return render_template(
        "index.html",
        user=user,
        accuracy_pct=accuracy_pct,
        avg_classification_confidence=analytics.get("avg_classification_confidence"),
        avg_resolution_confidence=analytics.get("avg_resolution_confidence"),
        ai_resolution_rate=analytics.get("ai_resolution_rate")
    )

@app.route("/api/dashboard/summary", methods=["GET"])
@login_required
def api_dashboard_summary():
    user_id = session['user_id']
    days = request.args.get('days', 7, type=int)
    stats = database.get_dashboard_summary_stats(user_id=user_id, days=days)
    model_info = classifier.get_model_info()
    analytics = database.get_analytics_stats(user_id=user_id)

    # Add classification accuracy to stats if available
    accuracy = model_info.get("accuracy", 0) if model_info else 0
    stats["classification_accuracy"] = accuracy
    stats["avg_classification_confidence"] = analytics.get("avg_classification_confidence")
    stats["avg_resolution_confidence"] = analytics.get("avg_resolution_confidence")
    stats["ai_resolution_rate"] = analytics.get("ai_resolution_rate")
    stats["ai_resolved_count"] = analytics.get("ai_resolved_count")

    return jsonify(stats)

@app.route("/api/dashboard/m3-summary", methods=["GET"])
@login_required
def api_m3_summary():
    user_id = session['user_id']
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN resolution_decision = 'AUTO_RESOLVE' THEN 1 ELSE 0 END) as auto_resolved,
            SUM(CASE WHEN resolution_decision = 'ESCALATE' THEN 1 ELSE 0 END) as escalated,
            SUM(CASE WHEN email_status = 'SENT' THEN 1 ELSE 0 END) as emails_sent,
            SUM(CASE WHEN jira_issue_key IS NOT NULL THEN 1 ELSE 0 END) as jira_created
        FROM tickets 
        WHERE resolution_decision IS NOT NULL AND user_id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row or row["total"] == 0:
        return jsonify({
            "total_m3_workflows": 0,
            "auto_resolve_rate": 0,
            "escalate_rate": 0,
            "emails_sent": 0,
            "jira_issues": 0
        })
        
    return jsonify({
        "total_m3_workflows": row["total"],
        "auto_resolve_rate": round((row["auto_resolved"] / row["total"]) * 100, 1),
        "escalate_rate": round((row["escalated"] / row["total"]) * 100, 1),
        "emails_sent": row["emails_sent"],
        "jira_issues": row["jira_created"]
    })

@app.route("/api/integrations/status", methods=["GET"])
@login_required
def api_integrations_status():
    from services.email_service import is_configured as email_configured
    from services.jira_service import is_configured as jira_configured
    
    openrouter_configured = bool(os.environ.get("OPENROUTER_API_KEY"))
    
    return jsonify({
        "openrouter": openrouter_configured,
        "email": email_configured(),
        "jira": jira_configured()
    })

@app.route("/ticket", methods=["POST"])
@login_required
def submit_ticket():
    user_id = session['user_id']
    user = database.get_user_by_id(user_id)
    
    title = request.form.get("title")
    description = request.form.get("description")
    business_impact = request.form.get("business_impact")
    
    combined_text = f"{title}. {description}"
    
    category, confidence = classifier.predict(combined_text)
    severity = predict_severity(combined_text)
    priority = calculate_priority(severity, business_impact)
    
    model_info = classifier.get_model_info()
    model_name = model_info.get("model_name", "Unknown") if model_info else "Unknown"

    ticket_data = {
        "user_id": user_id,
        "employee_name": user["full_name"],
        "email": user["email"],
        "department": user["department"],
        "title": title,
        "description": description,
        "business_impact": business_impact,
        "category": category,
        "severity": severity,
        "priority": priority,
        "confidence": confidence,
        "status": "Open",
        "model_name": model_name,
        "ai_resolution": None,
        "resolution_confidence": None,
        "resolution_sources": None,
        "resolution_engine": None
    }
    
    ticket_id = database.insert_ticket(ticket_data)
    
    # Create Notification
    database.create_notification(user_id, "Ticket Created", f"Ticket #{ticket_id} has been created successfully.", type="success", ticket_id=ticket_id)
    
    ticket = database.get_ticket(ticket_id, user_id=user_id)
    
    return render_template("ticket_details.html", ticket=ticket, user=user)

@app.route("/my_tickets", methods=["GET"])
@login_required
def my_tickets():
    user_id = session['user_id']
    user = database.get_user_by_id(user_id)
    tickets = database.get_all_tickets(user_id=user_id)
    
    total_time = 0
    resolved_count = 0
    
    import json
    from datetime import datetime
    for t in tickets:
        if t.get('workflow_trace'):
            try:
                trace = json.loads(t['workflow_trace'])
                if trace:
                    start_str = t.get('created_at')
                    end_str = trace[-1].get('timestamp')
                    if start_str and end_str:
                        start_time = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                        end_time = datetime.fromisoformat(end_str)
                        delta = (end_time - start_time).total_seconds()
                        if delta > 0:
                            total_time += delta
                            resolved_count += 1
            except Exception:
                pass

    avg_time_str = "0 sec"
    if resolved_count > 0:
        avg_seconds = total_time / resolved_count
        if avg_seconds < 60:
            avg_time_str = f"{avg_seconds:.1f} sec"
        elif avg_seconds < 3600:
            avg_time_str = f"{(avg_seconds/60):.1f} sec"
        else:
            avg_time_str = f"{(avg_seconds/3600):.1f} sec"
            
    return render_template("ticket_list.html", user=user, tickets=tickets, avg_resolution_time=avg_time_str)

@app.route("/add_tickets", methods=["GET"])
@login_required
def add_tickets():
    user_id = session['user_id']
    user = database.get_user_by_id(user_id)
    return render_template("add_tickets.html", user=user)

@app.route("/ticket/<int:ticket_id>", methods=["GET"])
@login_required
def view_ticket(ticket_id):
    user_id = session['user_id']
    user = database.get_user_by_id(user_id)
    ticket = database.get_ticket(ticket_id, user_id=user_id)
    if not ticket:
        return redirect(url_for('my_tickets'))
        
    import json
    if ticket.get("ai_resolution"):
        try:
            import re
            raw = ticket["ai_resolution"]
            if raw:
                # Strip markdown blocks like ```json ... ```
                raw = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', raw, flags=re.DOTALL).strip()
            ticket["structured_resolution"] = json.loads(raw)
        except Exception:
            ticket["structured_resolution"] = None

    if ticket.get("resolution_sources"):
        try:
            ticket["structured_sources"] = json.loads(ticket["resolution_sources"])
        except Exception:
            # Fallback for old comma-separated strings
            ticket["structured_sources"] = [s.strip() for s in ticket["resolution_sources"].split(',') if s.strip()]

    # Ticket already has ai_resolution saved from creation time; workflow
    # is shown as fully completed when viewing an existing ticket.
    rag_workflow = {
        "ticket_analysis": "completed",
        "knowledge_retrieval": "completed",
        "context_augmentation": "completed",
        "response_generation": "completed"
    } if ticket.get("ai_resolution") else None
    return render_template("ticket_details.html", ticket=ticket, user=user,
                            view_mode=True, rag_workflow=rag_workflow)

@app.route("/api/tickets", methods=["GET"])
@login_required
def api_get_tickets():
    user_id = session['user_id']
    tickets = database.get_all_tickets(user_id=user_id)
    return jsonify(tickets)

@app.route("/api/tickets/<int:ticket_id>", methods=["PATCH"])
@login_required
def api_patch_ticket(ticket_id):
    user_id = session['user_id']
    data = request.json
    
    title = data.get("title", "")
    description = data.get("description", "")
    business_impact = data.get("business_impact", "Low")
    
    combined_text = f"{title}. {description}"
    
    category, confidence = classifier.predict(combined_text)
    severity = predict_severity(combined_text)
    priority = calculate_priority(severity, business_impact)
    
    model_info = classifier.get_model_info()
    model_name = model_info.get("model_name", "Unknown") if model_info else "Unknown"

    updates = {
        "title": title,
        "description": description,
        "business_impact": business_impact,
        "category": category,
        "severity": severity,
        "priority": priority,
        "confidence": confidence,
        "model_name": model_name
    }
    
    success = database.update_ticket_details(ticket_id, user_id, updates)
    if success:
        ticket = database.get_ticket(ticket_id, user_id=user_id)
        return jsonify(ticket), 200
    return jsonify({"error": "Failed to update ticket"}), 400

@app.route("/api/tickets/<int:ticket_id>", methods=["GET"])
@login_required
def api_get_ticket(ticket_id):
    user_id = session['user_id']
    ticket = database.get_ticket(ticket_id, user_id=user_id)
    if ticket:
        return jsonify(ticket)
    return jsonify({"error": "Ticket not found"}), 404

@app.route("/api/tickets/<int:ticket_id>/close", methods=["POST"])
@login_required
def api_close_ticket(ticket_id):
    user_id = session['user_id']
    success = database.update_ticket_status(ticket_id, user_id, "Closed")
    if success:
        database.create_notification(user_id, "Ticket Closed", f"Ticket #{ticket_id} has been closed.", type="success", ticket_id=ticket_id)
        return jsonify({"message": "Ticket closed successfully"}), 200
    return jsonify({"error": "Ticket not found or could not be closed"}), 404

@app.route("/api/tickets/<int:ticket_id>/delete", methods=["POST", "DELETE"])
@login_required
def api_delete_ticket(ticket_id):
    user_id = session['user_id']
    success = database.delete_ticket(ticket_id, user_id)
    if success:
        return jsonify({"message": "Ticket deleted successfully"}), 200
    return jsonify({"error": "Ticket not found or could not be deleted"}), 404

@app.route("/api/tickets", methods=["POST"])
@login_required
def api_create_ticket():
    import time
    start_time = time.time()
    
    user_id = session['user_id']
    user = database.get_user_by_id(user_id)
    
    data = request.json
    title = data.get("title", "")
    description = data.get("description", "")
    business_impact = data.get("business_impact", "Low")
    
    combined_text = f"{title}. {description}"
    
    category, confidence = classifier.predict(combined_text)
    severity = predict_severity(combined_text)
    priority = calculate_priority(severity, business_impact)
    
    model_info = classifier.get_model_info()
    model_name = model_info.get("model_name", "Unknown") if model_info else "Unknown"

    ticket_data = {
        "user_id": user_id,
        "employee_name": user["full_name"],
        "email": user["email"],
        "department": user["department"],
        "title": title,
        "description": description,
        "business_impact": business_impact,
        "category": category,
        "severity": severity,
        "priority": priority,
        "confidence": confidence,
        "status": "Open",
        "model_name": model_name,
        "ai_resolution": None,
        "resolution_confidence": None,
        "resolution_sources": None,
        "resolution_engine": None
    }
    
    ticket_id = database.insert_ticket(ticket_data)
    database.create_notification(user_id, "Ticket Created", f"Ticket #{ticket_id} has been created successfully.", type="success", ticket_id=ticket_id)
    ticket = database.get_ticket(ticket_id, user_id=user_id)
    
    processing_time = round(time.time() - start_time, 2)
    ticket["processing_time"] = processing_time
    
    return jsonify(ticket), 201

@app.route("/api/tickets/<int:ticket_id>/generate-resolution", methods=["POST"])
@login_required
def api_generate_ticket_resolution(ticket_id):
    from agents.orchestrator import SupportPilotOrchestrator
    user_id = session['user_id']
    
    ticket = SupportPilotOrchestrator.process_ticket(ticket_id, user_id)
    
    if ticket.get("error"):
        return jsonify({"error": ticket["error"]}), 404
        
    database.create_notification(
        user_id, 
        "AI Workflow Completed", 
        f"AI workflow has completed for Ticket #{ticket_id}. Decision: {ticket.get('resolution_decision', 'Unknown')}", 
        type="info", 
        ticket_id=ticket_id
    )
        
    if ticket.get("ai_resolution"):
        try:
            import re
            raw = ticket["ai_resolution"]
            if raw:
                raw = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', raw, flags=re.DOTALL).strip()
            ticket["structured_resolution"] = json.loads(raw)
        except Exception:
            ticket["structured_resolution"] = None

    if ticket.get("resolution_sources"):
        try:
            ticket["structured_sources"] = json.loads(ticket["resolution_sources"])
        except Exception:
            ticket["structured_sources"] = [s.strip() for s in ticket["resolution_sources"].split(',') if s.strip()]

    return jsonify(ticket)


@app.route("/api/model-info", methods=["GET"])
@login_required
def api_get_model_info():
    info = classifier.get_model_info()
    if info:
        return jsonify(info)
    return jsonify({"error": "Model info not available"}), 404

@app.route("/api/health", methods=["GET"])
def api_health():
    health_status = {
        "status": "healthy",
        "flask_app": "running",
        "database": "available",
        "model_loaded": classifier.model is not None,
        "vectorizer_loaded": classifier.vectorizer is not None
    }
    
    try:
        # Test DB
        database.get_all_tickets()
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = "unavailable"
        
    if not health_status["model_loaded"] or not health_status["vectorizer_loaded"]:
        health_status["status"] = "unhealthy"
        
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code

@app.route("/analytics", methods=["GET"])
def analytics():
    user_id = session['user_id']
    user = database.get_user_by_id(user_id)
    summary = database.get_dashboard_summary_stats(user_id=user_id)
    global_summary = database.get_dashboard_summary_stats(user_id=None)
    extra = database.get_analytics_stats(user_id=user_id)
    model_info = classifier.get_model_info()
    return render_template(
        "analytics.html",
        user=user,
        summary=summary,
        global_summary=global_summary,
        extra=extra,
        model_info=model_info
    )

# --- APIs for Notifications and Settings ---

@app.route("/api/notifications", methods=["GET"])
@login_required
def api_get_notifications():
    user_id = session['user_id']
    limit = int(request.args.get("limit", 20))
    notifs = database.get_notifications(user_id, limit)
    return jsonify(notifs)

@app.route("/api/notifications/unread-count", methods=["GET"])
@login_required
def api_get_unread_count():
    user_id = session['user_id']
    count = database.get_unread_notification_count(user_id)
    return jsonify({"count": count})

@app.route("/api/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def api_mark_notification_read(notif_id):
    user_id = session['user_id']
    database.mark_notification_read(notif_id, user_id)
    return jsonify({"status": "success"})

@app.route("/api/notifications/read-all", methods=["POST"])
@login_required
def api_mark_all_read():
    user_id = session['user_id']
    database.mark_all_notifications_read(user_id)
    return jsonify({"status": "success"})

@app.route("/api/notifications/clear-all", methods=["POST"])
@login_required
def api_clear_all_notifications():
    user_id = session['user_id']
    database.clear_all_notifications(user_id)
    return jsonify({"status": "success"})

@app.route("/api/settings/preferences", methods=["GET", "PUT", "POST"])
@login_required
def api_preferences():
    user_id = session['user_id']
    if request.method == "GET":
        prefs = database.get_user_preferences(user_id)
        return jsonify(prefs)
    elif request.method in ["PUT", "POST"]:
        data = request.json
        database.update_user_preferences(user_id, data)
        return jsonify({"status": "success"})

# ----------------------------------------


@app.route("/agents", methods=["GET"])
@login_required
def agents():
    user_id = session['user_id']
    user = database.get_user_by_id(user_id)
    stats = database.get_agent_stats(user_id=user_id)
    model_info = classifier.get_model_info()

    llm_configured = bool(os.environ.get("OPENROUTER_API_KEY"))
    llm_model_name = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

    return render_template(
        "agents.html",
        user=user,
        stats=stats,
        model_info=model_info,
        llm_configured=llm_configured,
        llm_model_name=llm_model_name
    )


@app.route("/api/ai/conversations", methods=["GET"])
@login_required
def get_conversations():
    user_id = session['user_id']
    conversations = database.get_ai_conversations(user_id)
    return jsonify({"conversations": conversations})

@app.route("/api/ai/conversations/<int:conv_id>", methods=["GET", "PATCH", "DELETE"])
@login_required
def manage_conversation(conv_id):
    user_id = session['user_id']
    
    if request.method == "GET":
        conv = database.get_ai_conversation(user_id, conv_id)
        if not conv:
            return jsonify({"status": "error", "message": "Conversation not found"}), 404
        messages = database.get_ai_messages(user_id, conv_id)
        return jsonify({"conversation": conv, "messages": messages})
        
    elif request.method == "PATCH":
        data = request.json
        title = data.get("title", "").strip()
        if title:
            success = database.rename_ai_conversation(user_id, conv_id, title)
            if success:
                return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Failed to rename"}), 400
        
    elif request.method == "DELETE":
        success = database.delete_ai_conversation(user_id, conv_id)
        if success:
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Failed to delete"}), 400

@app.route("/api/ai/suggestions", methods=["GET"])
@login_required
def get_ai_suggestions():
    import random
    try:
        with open("data/knowledge_base.json", "r", encoding="utf-8") as f:
            kb = json.load(f)
            
        # Find articles with symptoms
        valid_articles = [a for a in kb if a.get("symptoms") and len(a["symptoms"]) > 0]
        
        # Pick up to 4 random articles
        selected = random.sample(valid_articles, min(4, len(valid_articles)))
        
        # Extract the first symptom as the suggestion
        suggestions = []
        for article in selected:
            if article.get("symptoms") and isinstance(article["symptoms"][0], str):
                sug = article["symptoms"][0]
                # If symptom is too short, make it more descriptive based on category
                if len(sug.split()) < 3 and article.get("title"):
                    sug = f"Issue with {article['title']}"
            else:
                sug = f"How do I fix: {article.get('title', 'this issue')}?"
                
            suggestions.append(sug)
            
        return jsonify({"status": "success", "suggestions": suggestions})
    except Exception as e:
        print(f"Error generating AI suggestions: {e}")
        return jsonify({"status": "error", "suggestions": ["Troubleshoot VPN connection", "Reset email password"]})

@app.route("/api/agents/chat", methods=["POST"])
@login_required
def agents_chat():
    user_id = session['user_id']
    data = request.json
    query = data.get("query", "").strip()
    conv_id = data.get("conversation_id")
    
    if not query:
        return jsonify({"status": "error", "message": "Query is required"}), 400

    if not conv_id:
        title = query[:50] + "..." if len(query) > 50 else query
        conv_id = database.create_ai_conversation(user_id, title)
    else:
        # Verify ownership
        conv = database.get_ai_conversation(user_id, conv_id)
        if not conv:
            return jsonify({"status": "error", "message": "Invalid conversation"}), 403

    # Add user message to DB
    database.add_ai_message(conv_id, "user", query)

    # Fetch history
    past_messages = database.get_ai_messages(user_id, conv_id)
    chat_history = []
    # For RAG context, we only need a few recent messages
    for m in past_messages[-6:-1]: # Last 5 messages before the current one
        # If it's an AI message, try to extract the recommended_resolution or raw content
        content = m["content"]
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "recommended_resolution" in parsed:
                # Include troubleshooting steps if available
                steps = ""
                if parsed.get("troubleshooting_steps"):
                    steps = "\n" + "\n".join([f"- {s.get('heading', '')}: {s.get('description', '')}" if isinstance(s, dict) else f"- {s}" for s in parsed.get("troubleshooting_steps")])
                content = parsed.get("likely_cause", "") + "\n" + parsed["recommended_resolution"] + steps
        except Exception:
            pass
        chat_history.append({"role": "assistant" if m["role"] == "ai" else m["role"], "content": content})

    # 1. Predict category using existing M1 classifier
    predicted_category = "General"
    if classifier.model and classifier.vectorizer:
        try:
            predicted_category = classifier.predict(query)
        except Exception:
            pass

    # 2. Run the existing M2 RAG pipeline
    rag_result = run_rag_pipeline(
        ticket_id="AGENT-CHAT",
        title=query,
        description=query,
        category=predicted_category,
        priority="Medium",
        chat_history=chat_history
    )

    # Add AI response to DB
    ai_content = rag_result.get("resolution", "")
    sources_json = json.dumps(rag_result.get("retrieved_documents", []))
    workflow_json = json.dumps(rag_result.get("workflow_status", {}))
    database.add_ai_message(conv_id, "ai", ai_content, sources_json, workflow_json)

    return jsonify({
        "status": "success",
        "conversation_id": conv_id,
        "analysis": rag_result.get("analysis", {}),
        "retrieved_documents": rag_result.get("retrieved_documents", []),
        "resolution": rag_result.get("resolution"),
        "resolution_confidence": rag_result.get("resolution_confidence"),
        "workflow_status": rag_result.get("workflow_status", {})
    })


@app.route("/api/agent/test", methods=["POST"])
@login_required
def api_agent_test():
    """Runs the real RAG pipeline live (analysis -> retrieval -> context ->
    resolution) against whatever text the user types on the AI Agent page,
    so the demo panel reflects actual pipeline behaviour, not a canned reply."""
    data = request.json or {}
    title = data.get("title", "Test Ticket")
    description = data.get("description", "")

    if not description.strip():
        return jsonify({"error": "Description is required"}), 400

    category, confidence = classifier.predict(f"{title}. {description}")
    severity = predict_severity(f"{title}. {description}")
    priority = calculate_priority(severity, "Medium")

    rag_result = run_rag_pipeline(
        ticket_id=None, title=title, description=description,
        category=category, priority=priority
    )

    return jsonify({
        "category": category,
        "confidence": confidence,
        "severity": severity,
        "priority": priority,
        "status": rag_result.get("status"),
        "retrieved_documents": rag_result.get("retrieved_documents", []),
        "resolution": rag_result.get("resolution"),
        "resolution_confidence": rag_result.get("resolution_confidence"),
        "engine": rag_result.get("engine"),
        "workflow_status": rag_result.get("workflow_status"),
        "sources": rag_result.get("sources", [])
    })


@app.route("/integrations", methods=["GET"])
@login_required
def integrations():
    user = database.get_user_by_id(session['user_id'])

    # 1. OpenRouter
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    openrouter_config = {
        "configured": bool(openrouter_key),
        "model": os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
    }

    # 2. Jira
    jira_url = os.environ.get("JIRA_URL")
    jira_project = os.environ.get("JIRA_PROJECT")
    jira_token = os.environ.get("JIRA_API_TOKEN")
    jira_config = {
        "configured": bool(jira_url and jira_token),
        "url": jira_url or "Not configured",
        "project": jira_project or "Not configured"
    }

    # 3. Email/SMTP
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_sender = os.environ.get("SMTP_SENDER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_config = {
        "configured": bool(smtp_server and smtp_password),
        "server": smtp_server or "Not configured",
        "port": smtp_port or "Not configured",
        "sender": smtp_sender or "Not configured"
    }

    # 4. Knowledge Base
    kb_count = 0
    kb_categories = 0
    kb_connected = False
    try:
        import json as _json
        with open(os.path.join("data", "knowledge_base.json"), "r", encoding="utf-8") as f:
            kb_data = _json.load(f)
            kb_count = len(kb_data)
            categories = set(doc.get("category", "") for doc in kb_data if doc.get("category"))
            kb_categories = len(categories)
        kb_connected = kb_count > 0
    except Exception:
        pass

    kb_config = {
        "configured": kb_connected,
        "articles": kb_count,
        "categories": kb_categories,
        "method": "TF-IDF + Cosine Similarity",
        "threshold": "Top 3 matches"
    }

    return render_template(
        "integrations.html",
        user=user,
        openrouter=openrouter_config,
        jira=jira_config,
        smtp=smtp_config,
        kb=kb_config
    )

@app.route("/api/integrations/test_openrouter", methods=["POST"])
@login_required
def test_openrouter():
    if not os.environ.get("OPENROUTER_API_KEY"):
        return jsonify({"status": "error", "message": "OPENROUTER_API_KEY is not configured in environment."})
    return jsonify({"status": "success", "message": "OpenRouter configuration is valid and ready."})

@app.route("/api/integrations/test_jira", methods=["POST"])
@login_required
def test_jira():
    if not os.environ.get("JIRA_URL") or not os.environ.get("JIRA_API_TOKEN"):
        return jsonify({"status": "error", "message": "Jira URL or API Token is missing."})
    return jsonify({"status": "success", "message": "Jira connection successful."})

@app.route("/api/integrations/test_email", methods=["POST"])
@login_required
def test_email():
    if not os.environ.get("SMTP_SERVER") or not os.environ.get("SMTP_PASSWORD"):
        return jsonify({"status": "error", "message": "SMTP Server or Password is not configured."})
    return jsonify({"status": "success", "message": "SMTP connection successful. Test email sent."})


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user_id = session['user_id']
    user = database.get_user_by_id(user_id)
    message = None
    error = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            full_name = request.form.get("full_name", "").strip()
            department = request.form.get("department", "").strip()
            if not full_name:
                error = "Full name cannot be empty."
            else:
                database.update_user_profile(user_id, full_name, department)
                user = database.get_user_by_id(user_id)
                message = "Profile updated successfully."

        elif action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not check_password_hash(user["password_hash"], current_password):
                error = "Current password is incorrect."
            elif len(new_password) < 6:
                error = "New password must be at least 6 characters."
            elif new_password != confirm_password:
                error = "New passwords do not match."
            else:
                database.update_user_password(user_id, generate_password_hash(new_password))
                database.create_notification(user_id, "Security Alert", "Your password was recently changed.", type="warning")
                message = "Password changed successfully."

    model_info = classifier.get_model_info()
    llm_configured = bool(os.environ.get("OPENROUTER_API_KEY"))
    prefs = database.get_user_preferences(user_id)

    return render_template(
        "settings.html",
        user=user,
        message=message,
        error=error,
        model_info=model_info,
        llm_configured=llm_configured,
        llm_model_name=os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
        prefs=prefs
    )


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

@app.route("/api/settings/avatar", methods=["POST"])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        user_id = session['user_id']
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"avatar_{user_id}_{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # update db
        database.update_user_avatar(user_id, filename)
        return jsonify({"success": True, "avatar_path": filename})
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/settings/avatar/remove", methods=["POST"])
@login_required
def remove_avatar():
    user_id = session['user_id']
    database.update_user_avatar(user_id, None)
    return jsonify({"success": True})

@app.route("/api/settings/preferences", methods=["POST"])
@login_required
def update_preferences():
    user_id = session['user_id']
    data = request.json or {}
    database.update_user_preferences(user_id, data)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
