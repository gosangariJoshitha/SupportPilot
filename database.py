import sqlite3
import os
from datetime import datetime

DB_FILE = "tickets.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute('''
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
    cursor.execute('''
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')

    # Lightweight migration for DBs created before resolution_engine existed
    cursor.execute("PRAGMA table_info(tickets)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    if "resolution_engine" not in existing_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN resolution_engine VARCHAR(20)")

    conn.commit()
    conn.close()

def create_user(full_name, email, password_hash, department):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO users (full_name, email, password_hash, department)
        VALUES (?, ?, ?, ?)
        ''', (full_name, email, password_hash, department))
        user_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        user_id = None  # Email already exists
    finally:
        conn.close()
    return user_id

def get_user_by_email(email):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def insert_ticket(data):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO tickets (
        user_id, employee_name, email, title, description, department, business_impact,
        category, severity, priority, confidence, status, model_name, ai_resolution,
        resolution_confidence, resolution_sources, resolution_engine
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
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
        data.get("resolution_engine")
    ))
    
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def get_all_tickets(user_id=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if user_id:
        cursor.execute('SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    else:
        cursor.execute('SELECT * FROM tickets ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_ticket(ticket_id, user_id=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if user_id:
        cursor.execute('SELECT * FROM tickets WHERE ticket_id = ? AND user_id = ?', (ticket_id, user_id))
    else:
        cursor.execute('SELECT * FROM tickets WHERE ticket_id = ?', (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_ticket_status(ticket_id, user_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tickets SET status = ? 
        WHERE ticket_id = ? AND user_id = ?
    ''', (new_status, ticket_id, user_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def update_ticket_ai_resolution(ticket_id, user_id, data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
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


def delete_ticket(ticket_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM tickets 
        WHERE ticket_id = ? AND user_id = ?
    ''', (ticket_id, user_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def get_dashboard_summary_stats(user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    
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
    cursor.execute(f'SELECT COUNT(*) FROM tickets{query_suffix}', params)
    stats["total_tickets"] = cursor.fetchone()[0]
    
    # Open tickets (Open or In Progress)
    cursor.execute(f'SELECT COUNT(*) FROM tickets WHERE status != "Closed"{" AND user_id = ?" if user_id else ""}', params)
    stats["open_tickets"] = cursor.fetchone()[0]
    
    # Resolved tickets
    cursor.execute(f'SELECT COUNT(*) FROM tickets WHERE status = "Closed"{" AND user_id = ?" if user_id else ""}', params)
    stats["resolved_tickets"] = cursor.fetchone()[0]
    
    # Category distribution
    cursor.execute(f'SELECT category, COUNT(*) FROM tickets{query_suffix} GROUP BY category', params)
    for row in cursor.fetchall():
        if row[0]:
            stats["category_distribution"][row[0]] = row[1]
            
    # Severity distribution
    cursor.execute(f'SELECT severity, COUNT(*) FROM tickets{query_suffix} GROUP BY severity', params)
    for row in cursor.fetchall():
        if row[0] in stats["severity_distribution"]:
            stats["severity_distribution"][row[0]] = row[1]
            
    # Priority distribution
    cursor.execute(f'SELECT priority, COUNT(*) FROM tickets{query_suffix} GROUP BY priority', params)
    for row in cursor.fetchall():
        if row[0] in stats["priority_distribution"]:
            stats["priority_distribution"][row[0]] = row[1]
            
    # Ticket Activity (Last 7 days approx, grouped by date)
    cursor.execute(f'SELECT DATE(created_at) as date, COUNT(*) FROM tickets{query_suffix} GROUP BY DATE(created_at) ORDER BY date ASC LIMIT 7', params)
    for row in cursor.fetchall():
        if row[0]:
            stats["ticket_activity"]["dates"].append(row[0])
            stats["ticket_activity"]["counts"].append(row[1])
        
    conn.close()
    
    # Get recent tickets (last 5)
    recent = get_all_tickets(user_id)[:5]
    stats["recent_tickets"] = recent
    
    return stats


def get_analytics_stats(user_id=None):
    """Real, DB-derived metrics for the Analytics page. No hardcoded or
    simulated numbers - every value is computed from actual stored tickets."""
    conn = get_connection()
    cursor = conn.cursor()

    query_suffix = ' WHERE user_id = ?' if user_id else ''
    params = (user_id,) if user_id else ()

    cursor.execute(f'SELECT COUNT(*) FROM tickets{query_suffix}', params)
    total = cursor.fetchone()[0]

    cursor.execute(f'SELECT AVG(confidence) FROM tickets{query_suffix}', params)
    avg_row = cursor.fetchone()
    avg_confidence = round(avg_row[0] * 100, 1) if avg_row and avg_row[0] is not None else None

    cursor.execute(f'SELECT AVG(resolution_confidence) FROM tickets{query_suffix}', params)
    avg_res_row = cursor.fetchone()
    avg_resolution_confidence = round(avg_res_row[0] * 100, 1) if avg_res_row and avg_res_row[0] is not None else None

    # AI resolutions actually produced (RAG pipeline status == OK) vs total
    resolved_suffix = query_suffix + (' AND' if user_id else ' WHERE') + ' ai_resolution IS NOT NULL'
    cursor.execute(f'SELECT COUNT(*) FROM tickets{resolved_suffix}', params)
    ai_resolved_count = cursor.fetchone()[0]
    ai_resolution_rate = round((ai_resolved_count / total) * 100, 1) if total > 0 else 0

    # Resolution engine breakdown (llm vs template fallback vs none)
    cursor.execute(f'SELECT resolution_engine, COUNT(*) FROM tickets{query_suffix} GROUP BY resolution_engine', params)
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
        "engine_counts": engine_counts,
    }


def get_agent_stats(user_id=None):
    """Real stats about the RAG / AI-agent pipeline usage for this user,
    derived entirely from stored ticket rows - no simulated figures."""
    conn = get_connection()
    cursor = conn.cursor()

    query_suffix = ' WHERE user_id = ?' if user_id else ''
    params = (user_id,) if user_id else ()

    cursor.execute(f'SELECT COUNT(*) FROM tickets{query_suffix}', params)
    total = cursor.fetchone()[0]

    resolved_suffix = query_suffix + (' AND' if user_id else ' WHERE') + ' ai_resolution IS NOT NULL'
    cursor.execute(f'SELECT COUNT(*) FROM tickets{resolved_suffix}', params)
    resolutions_generated = cursor.fetchone()[0]

    cursor.execute(f'SELECT AVG(resolution_confidence) FROM tickets{query_suffix}', params)
    row = cursor.fetchone()
    avg_resolution_confidence = round(row[0] * 100, 1) if row and row[0] is not None else None

    llm_suffix = query_suffix + (' AND' if user_id else ' WHERE') + " resolution_engine = 'llm'"
    cursor.execute(f'SELECT COUNT(*) FROM tickets{llm_suffix}', params)
    llm_generated = cursor.fetchone()[0]

    # Most recent tickets that went through the pipeline, for a live feed
    recent_suffix = query_suffix + (' AND' if user_id else ' WHERE') + ' ai_resolution IS NOT NULL'
    cursor.execute(
        f'SELECT ticket_id, title, category, resolution_confidence, resolution_engine, created_at '
        f'FROM tickets{recent_suffix} ORDER BY created_at DESC LIMIT 5',
        params
    )
    conn.row_factory = sqlite3.Row
    cursor2 = conn.cursor()
    cursor2.execute(
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
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET full_name = ?, department = ? WHERE user_id = ?',
        (full_name, department, user_id)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def update_user_password(user_id, new_password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET password_hash = ? WHERE user_id = ?',
        (new_password_hash, user_id)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success
