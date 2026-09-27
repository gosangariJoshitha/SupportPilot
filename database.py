import re
import sqlite3
import os
from datetime import datetime

import os

DB_FILE = "tickets.db"
DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL)

if IS_POSTGRES and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_connection():
    if IS_POSTGRES:
        import psycopg2
        from psycopg2.extras import DictCursor
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

def get_cursor(conn):
    if IS_POSTGRES:
        from psycopg2.extras import DictCursor
        return getattr(conn, "cursor")(cursor_factory=DictCursor)
    return getattr(conn, "cursor")()

def execute_query(cursor, query, params=()):
    if IS_POSTGRES:
        query = query.replace('?', '%s')
        query = query.replace('AUTOINCREMENT', '')
        query = query.replace('INTEGER PRIMARY KEY', 'SERIAL PRIMARY KEY')
        query = query.replace('BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE')
        query = query.replace('BOOLEAN DEFAULT 1', 'BOOLEAN DEFAULT TRUE')
        if 'JulianDay' in query:
            query = query.replace('CAST((JulianDay(resolved_at) - JulianDay(created_at)) * 24 * 60 * 60 As Integer)', 'EXTRACT(EPOCH FROM (resolved_at - created_at))')
        
        # PostgreSQL date compatibility
        # Replace date('now', '-X days')
        query = re.sub(r"date\('now',\s*'-(\d+)\s*days'\)", r"(CURRENT_DATE - INTERVAL '\1 days')", query)
        
        # Replace DATE(created_at) -> CAST(created_at AS DATE)
        query = re.sub(r"DATE\((.*?)\)", r"CAST(\1 AS DATE)", query)

    cursor.execute(query, params)

def execute_insert_get_id(cursor, query, params=(), id_col='id'):
    if IS_POSTGRES:
        query = query.replace('?', '%s')
        # Insert RETURNING id if not present
        if 'RETURNING' not in query:
            query = query + f" RETURNING {id_col}"
        cursor.execute(query, params)
        return cursor.fetchone()[0]
    else:
        cursor.execute(query, params)
        return cursor.lastrowid

def init_db():
    conn = get_connection()
    cursor = get_cursor(conn)
    
    # Create Users Table
    execute_query(cursor, '''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        department VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create Tickets Table (with user_id and ai fields)
    execute_query(cursor, '''
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        employee_name VARCHAR(100),
        email VARCHAR(150),
        title VARCHAR(255),
        description TEXT,
        department VARCHAR(100),
        business_impact VARCHAR(50),
        category VARCHAR(50),
        severity VARCHAR(20),
        priority VARCHAR(10),
        confidence FLOAT,
        status VARCHAR(30),
        model_name VARCHAR(100),
        ai_resolution TEXT,
        resolution_confidence FLOAT,
        resolution_sources VARCHAR(255),
        resolution_engine VARCHAR(20),
        validation_confidence FLOAT,
        validation_details TEXT,
        resolution_decision VARCHAR(20),
        escalation_reason VARCHAR(255),
        jira_issue_key VARCHAR(50),
        jira_issue_url VARCHAR(255),
        email_status VARCHAR(50),
        email_sent_at TIMESTAMP,
        workflow_status VARCHAR(50),
        workflow_trace TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')

    # Lightweight migration for DBs created before resolution_engine existed
    if IS_POSTGRES:
        execute_query(cursor, "SELECT column_name FROM information_schema.columns WHERE table_name = 'tickets'")
        existing_cols = {row[0] for row in cursor.fetchall()}
    else:
        execute_query(cursor, "PRAGMA table_info(tickets)")
        existing_cols = {row[1] for row in cursor.fetchall()}
    if "resolution_engine" not in existing_cols:
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN resolution_engine VARCHAR(20)")
    if "workflow_status" not in existing_cols:
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN validation_confidence FLOAT")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN resolution_decision VARCHAR(20)")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN escalation_reason VARCHAR(255)")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN jira_issue_key VARCHAR(50)")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN jira_issue_url VARCHAR(255)")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN email_status VARCHAR(50)")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN email_sent_at TIMESTAMP")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN workflow_status VARCHAR(50)")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN workflow_trace TEXT")
    if "validation_details" not in existing_cols:
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN validation_details TEXT")
    if "resolved_at" not in existing_cols:
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN resolved_at TIMESTAMP")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN customer_satisfaction INTEGER")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN repeated_attempts INTEGER DEFAULT 0")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN customer_requested_human BOOLEAN DEFAULT 0")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN ai_response_time FLOAT")
        execute_query(cursor, "ALTER TABLE tickets ADD COLUMN resolution_time FLOAT")
    if IS_POSTGRES:
        execute_query(cursor, "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
        existing_user_cols = {row[0] for row in cursor.fetchall()}
    else:
        execute_query(cursor, "PRAGMA table_info(users)")
        existing_user_cols = {row[1] for row in cursor.fetchall()}
    if "password_reset_token" not in existing_user_cols:
        execute_query(cursor, "ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(255)")
    if "reset_token_expiry" not in existing_user_cols:
        execute_query(cursor, "ALTER TABLE users ADD COLUMN reset_token_expiry TIMESTAMP")
    if "avatar_path" not in existing_user_cols:
        execute_query(cursor, "ALTER TABLE users ADD COLUMN avatar_path VARCHAR(255)")

    # Create Notifications Table
    execute_query(cursor, '''
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticket_id INTEGER,
        type VARCHAR(50),
        title VARCHAR(255),
        message TEXT,
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
    )
    ''')
    execute_query(cursor, "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications (user_id)")

    # Create User Preferences Table
    execute_query(cursor, '''
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY,
        theme VARCHAR(20) DEFAULT 'system',
        notify_ticket_status BOOLEAN DEFAULT 1,
        notify_ai_suggestions BOOLEAN DEFAULT 1,
        notify_weekly_summary BOOLEAN DEFAULT 0,
        notify_product_updates BOOLEAN DEFAULT 0,
        notify_marketing BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')

    # Create AI Conversations Table
    execute_query(cursor, '''
    CREATE TABLE IF NOT EXISTS ai_conversations (
        conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    execute_query(cursor, "CREATE INDEX IF NOT EXISTS idx_ai_conversations_user_id ON ai_conversations (user_id)")

    # Create AI Messages Table
    execute_query(cursor, '''
    CREATE TABLE IF NOT EXISTS ai_messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        role VARCHAR(20) NOT NULL,
        content TEXT NOT NULL,
        sources_json TEXT,
        workflow_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES ai_conversations(conversation_id)
    )
    ''')
    execute_query(cursor, "CREATE INDEX IF NOT EXISTS idx_ai_messages_conversation_id ON ai_messages (conversation_id)")

    conn.commit()
    conn.close()

def create_user(full_name, email, password_hash, department):
    conn = get_connection()
    cursor = get_cursor(conn)
    try:
        user_id = execute_insert_get_id(cursor, '''INSERT INTO users (full_name, email, password_hash, department) VALUES (?, ?, ?, ?)''', (full_name, email, password_hash, department), 'user_id')
        
        # Initialize default preferences
        execute_query(cursor, '''
        INSERT INTO user_preferences (user_id) VALUES (?)
        ''', (user_id,))
        
        conn.commit()
    except sqlite3.IntegrityError:
        user_id = None  # Email already exists
    finally:
        conn.close()
    return user_id

def get_user_by_email(email):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'SELECT * FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def insert_ticket(data):
    conn = get_connection()
    cursor = get_cursor(conn)
    
    ticket_id = execute_insert_get_id(cursor, '''INSERT INTO tickets (
        user_id, employee_name, email, title, description, department, business_impact,
        category, severity, priority, confidence, status, model_name, ai_resolution,
        resolution_confidence, resolution_sources, resolution_engine, workflow_status, validation_details
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        data.get("user_id"),
        data.get("employee_name"),
        data.get("email"),
        data.get("title"),
        data.get("description"),
        data.get("department"),
        data.get("business_impact"),
        data.get("category"),
        data.get("severity"),
        data.get("priority"),
        data.get("confidence"),
        data.get("status", "Open"),
        data.get("model_name"),
        data.get("ai_resolution"),
        data.get("resolution_confidence"),
        data.get("resolution_sources"),
        data.get("resolution_engine"),
        data.get("workflow_status", "NOT_STARTED"),
        data.get("validation_details")
    ), 'ticket_id')
    conn.commit()
    conn.close()
    return ticket_id

def get_all_tickets(user_id=None):
    conn = get_connection()
    cursor = get_cursor(conn)
    if user_id:
        execute_query(cursor, 'SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    else:
        execute_query(cursor, 'SELECT * FROM tickets ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_ticket(ticket_id, user_id=None):
    conn = get_connection()
    cursor = get_cursor(conn)
    if user_id:
        execute_query(cursor, 'SELECT * FROM tickets WHERE ticket_id = ? AND user_id = ?', (ticket_id, user_id))
    else:
        execute_query(cursor, 'SELECT * FROM tickets WHERE ticket_id = ?', (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_ticket_status(ticket_id, user_id, new_status):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
        UPDATE tickets SET status = ? 
        WHERE ticket_id = ? AND user_id = ?
    ''', (new_status, ticket_id, user_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def update_ticket_details(ticket_id, user_id, updates):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
        UPDATE tickets SET 
            title = ?, 
            description = ?, 
            business_impact = ?, 
            category = ?, 
            severity = ?, 
            priority = ?, 
            confidence = ?, 
            model_name = ?,
            ai_resolution = NULL,
            resolution_confidence = NULL,
            resolution_sources = NULL,
            resolution_engine = NULL,
            validation_confidence = NULL,
            validation_details = NULL,
            resolution_decision = NULL,
            escalation_reason = NULL,
            jira_issue_key = NULL,
            jira_issue_url = NULL,
            email_status = NULL,
            email_sent_at = NULL,
            workflow_status = 'NOT_STARTED',
            workflow_trace = NULL
        WHERE ticket_id = ? AND user_id = ?
    ''', (
        updates['title'], 
        updates['description'], 
        updates['business_impact'], 
        updates['category'], 
        updates['severity'], 
        updates['priority'], 
        updates['confidence'], 
        updates['model_name'],
        ticket_id, 
        user_id
    ))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def update_ticket_ai_resolution(ticket_id, user_id, data):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
        UPDATE tickets
        SET ai_resolution = ?,
            resolution_confidence = ?,
            resolution_sources = ?,
            resolution_engine = ?
        WHERE ticket_id = ? AND user_id = ?
    ''', (
        data.get("ai_resolution"),
        data.get("resolution_confidence"),
        data.get("resolution_sources"),
        data.get("resolution_engine"),
        ticket_id,
        user_id
    ))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def update_m3_workflow_state(ticket_id, user_id, updates):
    conn = get_connection()
    cursor = get_cursor(conn)
    
    fields = []
    params = []
    
    allowed_fields = [
        "workflow_status", "workflow_trace", "ai_resolution", 
        "resolution_confidence", "resolution_sources", "resolution_engine",
        "validation_confidence", "validation_details", "resolution_decision", "escalation_reason",
        "jira_issue_key", "jira_issue_url", "email_status", "email_sent_at",
        "status", "ai_response_time", "resolved_at", "customer_satisfaction", "repeated_attempts", "customer_requested_human"
    ]
    
    for k, v in updates.items():
        if k in allowed_fields:
            fields.append(f"{k} = ?")
            params.append(v)
            
    if not fields:
        conn.close()
        return False
        
    params.extend([ticket_id, user_id])
    
    execute_query(cursor, f'''
        UPDATE tickets
        SET {", ".join(fields)}
        WHERE ticket_id = ? AND user_id = ?
    ''', tuple(params))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def delete_ticket(ticket_id, user_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
        DELETE FROM tickets 
        WHERE ticket_id = ? AND user_id = ?
    ''', (ticket_id, user_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def get_dashboard_summary_stats(user_id=None, days=7):
    conn = get_connection()
    cursor = get_cursor(conn)
    
    stats = {
        "total_tickets": 0,
        "open_tickets": 0,
        "resolved_tickets": 0,
        "category_distribution": {},
        "severity_distribution": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
        "priority_distribution": {"P1": 0, "P2": 0, "P3": 0, "P4": 0},
        "ticket_activity": {"dates": [], "counts": []},
        "recent_tickets": []
    }
    
    query_suffix = ' WHERE user_id = ?' if user_id else ''
    params = (user_id,) if user_id else ()
    
    # Total tickets
    execute_query(cursor, f'SELECT COUNT(*) FROM tickets{query_suffix}', params)
    stats["total_tickets"] = cursor.fetchone()[0]
    
    # Open tickets (Open or In Progress)
    execute_query(cursor, f'SELECT COUNT(*) FROM tickets WHERE status != "Closed"{" AND user_id = ?" if user_id else ""}', params)
    stats["open_tickets"] = cursor.fetchone()[0]
    
    # Resolved tickets
    execute_query(cursor, f'SELECT COUNT(*) FROM tickets WHERE status = "Closed"{" AND user_id = ?" if user_id else ""}', params)
    stats["resolved_tickets"] = cursor.fetchone()[0]
    
    # Category distribution
    execute_query(cursor, f'SELECT category, COUNT(*) FROM tickets{query_suffix} GROUP BY category', params)
    for row in cursor.fetchall():
        if row[0]:
            stats["category_distribution"][row[0]] = row[1]
            
    # Severity distribution
    execute_query(cursor, f'SELECT severity, COUNT(*) FROM tickets{query_suffix} GROUP BY severity', params)
    for row in cursor.fetchall():
        if row[0] in stats["severity_distribution"]:
            stats["severity_distribution"][row[0]] = row[1]
            
    # Department distribution
    stats["department_distribution"] = {}
    execute_query(cursor, f'SELECT department, COUNT(*) FROM tickets{query_suffix} GROUP BY department', params)
    for row in cursor.fetchall():
        if row[0]:
            stats["department_distribution"][row[0]] = row[1]
            
    # Employee distribution
    stats["employee_distribution"] = {}
    execute_query(cursor, f'SELECT employee_name, COUNT(*) FROM tickets{query_suffix} GROUP BY employee_name', params)
    for row in cursor.fetchall():
        if row[0]:
            stats["employee_distribution"][row[0]] = row[1]
            
    # Priority distribution
    execute_query(cursor, f'SELECT priority, COUNT(*) FROM tickets{query_suffix} GROUP BY priority', params)
    for row in cursor.fetchall():
        if row[0] in stats["priority_distribution"]:
            stats["priority_distribution"][row[0]] = row[1]
            
    # Ticket Activity (Grouped by date, filtered by last N days)
    stats["ticket_activity"]["resolved_counts"] = []
    
    activity_suffix = f" WHERE created_at >= date('now', '-{days} days')"
    if user_id:
        activity_suffix += " AND user_id = ?"
        
    execute_query(cursor, f'''
        SELECT DATE(created_at) as date, 
               COUNT(*) as submitted,
               SUM(CASE WHEN status='Closed' THEN 1 ELSE 0 END) as resolved
        FROM tickets{activity_suffix} 
        GROUP BY DATE(created_at) 
        ORDER BY date ASC
    ''', params)
    for row in cursor.fetchall():
        if row[0]:
            stats["ticket_activity"]["dates"].append(row[0])
            stats["ticket_activity"]["counts"].append(row[1])
            stats["ticket_activity"]["resolved_counts"].append(row[2] or 0)
        
    conn.close()
    
    # Get recent tickets (last 5)
    recent = get_all_tickets(user_id)[:5]
    stats["recent_tickets"] = recent
    
    return stats


def get_analytics_stats(user_id=None):
    """Real, DB-derived metrics for the Analytics page. No hardcoded or
    simulated numbers - every value is computed from actual stored tickets."""
    conn = get_connection()
    cursor = get_cursor(conn)

    query_suffix = ' WHERE user_id = ?' if user_id else ''
    params = (user_id,) if user_id else ()

    execute_query(cursor, f'SELECT COUNT(*) FROM tickets{query_suffix}', params)
    total = cursor.fetchone()[0]

    execute_query(cursor, f'SELECT AVG(confidence) FROM tickets{query_suffix}', params)
    avg_row = cursor.fetchone()
    avg_confidence = round(avg_row[0] * 100, 1) if avg_row and avg_row[0] is not None else None

    execute_query(cursor, f'SELECT AVG(resolution_confidence) FROM tickets{query_suffix}', params)
    avg_res_row = cursor.fetchone()
    avg_resolution_confidence = round(avg_res_row[0] * 100, 1) if avg_res_row and avg_res_row[0] is not None else None

    resolved_suffix = query_suffix + (' AND' if user_id else ' WHERE') + " resolution_decision = 'AUTO_RESOLVE'"
    execute_query(cursor, f'SELECT COUNT(*) FROM tickets{resolved_suffix}', params)
    ai_resolved_count = cursor.fetchone()[0]
    ai_resolution_rate = round((ai_resolved_count / total) * 100, 1) if total > 0 else 0

    # KB Coverage
    kb_suffix = query_suffix + (' AND' if user_id else ' WHERE') + ' ai_resolution IS NOT NULL'
    execute_query(cursor, f'SELECT COUNT(*) FROM tickets{kb_suffix}', params)
    kb_count = cursor.fetchone()[0]
    kb_coverage = round((kb_count / total) * 100, 1) if total > 0 else 0

    # Average Resolution Time (in seconds)
    execute_query(cursor, f'SELECT AVG(CAST((JulianDay(resolved_at) - JulianDay(created_at)) * 24 * 60 * 60 As Integer)) FROM tickets WHERE resolved_at IS NOT NULL{" AND user_id = ?" if user_id else ""}', params)
    avg_res_time_row = cursor.fetchone()
    avg_resolution_time = round(avg_res_time_row[0], 2) if avg_res_time_row and avg_res_time_row[0] is not None else None

    # Customer Satisfaction
    execute_query(cursor, f'SELECT AVG(customer_satisfaction) FROM tickets WHERE customer_satisfaction IS NOT NULL{" AND user_id = ?" if user_id else ""}', params)
    csat_row = cursor.fetchone()
    avg_csat = round(csat_row[0], 2) if csat_row and csat_row[0] is not None else None

    # Resolution Success Rate (Successfully Resolved / Total Resolution Attempts)
    # Attempts where resolution_decision is not null
    execute_query(cursor, f'SELECT COUNT(*) FROM tickets WHERE resolution_decision IS NOT NULL{" AND user_id = ?" if user_id else ""}', params)
    total_attempts = cursor.fetchone()[0]
    execute_query(cursor, "SELECT COUNT(*) FROM tickets WHERE status = 'Closed' OR resolution_decision = 'AUTO_RESOLVE'" + (" AND user_id = ?" if user_id else ""), params)
    success_attempts = cursor.fetchone()[0]
    res_success_rate = round((success_attempts / total_attempts) * 100, 1) if total_attempts > 0 else 0

    # Resolution engine breakdown (llm vs template fallback vs none)
    execute_query(cursor, f'SELECT resolution_engine, COUNT(*) FROM tickets{query_suffix} GROUP BY resolution_engine', params)
    engine_counts = {"llm": 0, "template": 0}
    for row in cursor.fetchall():
        if row[0] in engine_counts:
            engine_counts[row[0]] = row[1]

    conn.close()

    return {
        "total_tickets": total,
        "avg_classification_confidence": avg_confidence,
        "avg_resolution_confidence": avg_resolution_confidence,
        "ai_resolved_count": ai_resolved_count,
        "ai_resolution_rate": ai_resolution_rate,
        "kb_coverage": kb_coverage,
        "avg_resolution_time": avg_resolution_time,
        "avg_csat": avg_csat,
        "res_success_rate": res_success_rate,
        "engine_counts": engine_counts,
    }


def get_agent_stats(user_id=None):
    """Real stats about the RAG / AI-agent pipeline usage for this user,
    derived entirely from stored ticket rows - no simulated figures."""
    conn = get_connection()
    cursor = get_cursor(conn)

    query_suffix = ' WHERE user_id = ?' if user_id else ''
    params = (user_id,) if user_id else ()

    execute_query(cursor, f'SELECT COUNT(*) FROM tickets{query_suffix}', params)
    total = cursor.fetchone()[0]

    resolved_suffix = query_suffix + (' AND' if user_id else ' WHERE') + ' ai_resolution IS NOT NULL'
    execute_query(cursor, f'SELECT COUNT(*) FROM tickets{resolved_suffix}', params)
    resolutions_generated = cursor.fetchone()[0]

    execute_query(cursor, f'SELECT AVG(resolution_confidence) FROM tickets{query_suffix}', params)
    row = cursor.fetchone()
    avg_resolution_confidence = round(row[0] * 100, 1) if row and row[0] is not None else None

    llm_suffix = query_suffix + (' AND' if user_id else ' WHERE') + " resolution_engine = 'llm'"
    execute_query(cursor, f'SELECT COUNT(*) FROM tickets{llm_suffix}', params)
    llm_generated = cursor.fetchone()[0]

    # Most recent tickets that went through the pipeline, for a live feed
    recent_suffix = query_suffix + (' AND' if user_id else ' WHERE') + ' ai_resolution IS NOT NULL'
    execute_query(cursor, 
        f'SELECT ticket_id, title, category, resolution_confidence, resolution_engine, created_at '
        f'FROM tickets{recent_suffix} ORDER BY created_at DESC LIMIT 5',
        params
    )
    cursor2 = get_cursor(conn)
    execute_query(cursor2, 
        f'SELECT ticket_id, title, category, resolution_confidence, resolution_engine, created_at '
        f'FROM tickets{recent_suffix} ORDER BY created_at DESC LIMIT 5',
        params
    )
    recent = [dict(r) for r in cursor2.fetchall()]

    conn.close()

    return {
        "total_tickets": total,
        "resolutions_generated": resolutions_generated,
        "avg_resolution_confidence": avg_resolution_confidence,
        "llm_generated": llm_generated,
        "template_generated": resolutions_generated - llm_generated,
        "recent_resolutions": recent,
    }


def update_user_profile(user_id, full_name, department):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
    UPDATE users SET full_name = ?, department = ? WHERE user_id = ?
    ''', (full_name, department, user_id))
    conn.commit()
    conn.close()

def update_user_avatar(user_id, avatar_path):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
    UPDATE users SET avatar_path = ? WHERE user_id = ?
    ''', (avatar_path, user_id))
    conn.commit()
    conn.close()


def update_user_password(user_id, new_password_hash):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 
        'UPDATE users SET password_hash = ? WHERE user_id = ?',
        (new_password_hash, user_id)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# --- User Preferences Helpers ---
def get_user_preferences(user_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        execute_query(cursor, 'INSERT INTO user_preferences (user_id) VALUES (?)', (user_id,))
        conn.commit()
        execute_query(cursor, 'SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
    conn.close()
    return dict(row)

def update_user_preferences(user_id, data):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'SELECT user_id FROM user_preferences WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        execute_query(cursor, 'INSERT INTO user_preferences (user_id) VALUES (?)', (user_id,))
    
    fields = []
    params = []
    for k in ["theme", "notify_ticket_status", "notify_ai_suggestions", "notify_weekly_summary", "notify_product_updates", "notify_marketing"]:
        if k in data:
            fields.append(f"{k} = ?")
            # Handle boolean conversions if passed as strings 'true'/'false'
            val = data[k]
            if isinstance(val, str):
                val = 1 if val.lower() == 'true' else 0
            params.append(val)
    
    if fields:
        params.append(user_id)
        execute_query(cursor, f'UPDATE user_preferences SET {", ".join(fields)} WHERE user_id = ?', tuple(params))
        conn.commit()
    conn.close()
    return True

# --- Notifications Helpers ---
def create_notification(user_id, title, message, type="info", ticket_id=None):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
        INSERT INTO notifications (user_id, ticket_id, type, title, message)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, ticket_id, type, title, message))
    conn.commit()
    conn.close()

def get_notifications(user_id, limit=20):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT ?', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_unread_notification_count(user_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def mark_notification_read(notification_id, user_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'UPDATE notifications SET is_read = 1 WHERE notification_id = ? AND user_id = ?', (notification_id, user_id))
    conn.commit()
    conn.close()
    return True

def mark_all_notifications_read(user_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'UPDATE notifications SET is_read = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return True

def clear_all_notifications(user_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'DELETE FROM notifications WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return True

# --- Password Reset Helpers ---
def save_password_reset_token(user_id, token, expiry):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'UPDATE users SET password_reset_token = ?, reset_token_expiry = ? WHERE user_id = ?', (token, expiry, user_id))
    conn.commit()
    conn.close()
    return True

def get_user_by_reset_token(token):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, 'SELECT * FROM users WHERE password_reset_token = ?', (token,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# --- AI Agent Conversations ---

def create_ai_conversation(user_id, title="New Conversation"):
    conn = get_connection()
    cursor = get_cursor(conn)
    conv_id = execute_insert_get_id(cursor, '''INSERT INTO ai_conversations (user_id, title) VALUES (?, ?)''', (user_id, title), 'conversation_id')
    conn.commit()
    conn.close()
    return conv_id

def get_ai_conversations(user_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
    SELECT conversation_id, title, created_at, updated_at
    FROM ai_conversations
    WHERE user_id = ?
    ORDER BY updated_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            "conversation_id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3]
        })
    return result

def get_ai_conversation(user_id, conversation_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
    SELECT conversation_id, title, created_at, updated_at
    FROM ai_conversations
    WHERE conversation_id = ? AND user_id = ?
    ''', (conversation_id, user_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "conversation_id": row[0],
        "title": row[1],
        "created_at": row[2],
        "updated_at": row[3]
    }

def rename_ai_conversation(user_id, conversation_id, new_title):
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
    UPDATE ai_conversations
    SET title = ?, updated_at = CURRENT_TIMESTAMP
    WHERE conversation_id = ? AND user_id = ?
    ''', (new_title, conversation_id, user_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def delete_ai_conversation(user_id, conversation_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    # verify ownership
    execute_query(cursor, "SELECT conversation_id FROM ai_conversations WHERE conversation_id = ? AND user_id = ?", (conversation_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return False
        
    execute_query(cursor, "DELETE FROM ai_messages WHERE conversation_id = ?", (conversation_id,))
    execute_query(cursor, "DELETE FROM ai_conversations WHERE conversation_id = ?", (conversation_id,))
    conn.commit()
    conn.close()
    return True

def add_ai_message(conversation_id, role, content, sources_json=None, workflow_json=None):
    conn = get_connection()
    cursor = get_cursor(conn)
    msg_id = execute_insert_get_id(cursor, '''INSERT INTO ai_messages (conversation_id, role, content, sources_json, workflow_json) VALUES (?, ?, ?, ?, ?)''', (conversation_id, role, content, sources_json, workflow_json), 'message_id')
    
    # Update conversation timestamp
    execute_query(cursor, '''
    UPDATE ai_conversations
    SET updated_at = CURRENT_TIMESTAMP
    WHERE conversation_id = ?
    ''', (conversation_id,))
    
    conn.commit()
    conn.close()
    return msg_id

def get_ai_messages(user_id, conversation_id):
    # Verify ownership first
    if not get_ai_conversation(user_id, conversation_id):
        return []
        
    conn = get_connection()
    cursor = get_cursor(conn)
    execute_query(cursor, '''
    SELECT message_id, role, content, sources_json, workflow_json, created_at
    FROM ai_messages
    WHERE conversation_id = ?
    ORDER BY created_at ASC
    ''', (conversation_id,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            "message_id": row[0],
            "role": row[1],
            "content": row[2],
            "sources_json": row[3],
            "workflow_json": row[4],
            "created_at": row[5]
        })
    return result
