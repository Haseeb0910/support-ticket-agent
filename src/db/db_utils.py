import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'support_tickets.db')


def get_lookup_ids(ticket_type, queue, priority):
    """Convert text values to their corresponding IDs from lookup tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT type_id FROM ticket_types WHERE type_name = ?", (ticket_type,))
    type_row = cursor.fetchone()

    cursor.execute("SELECT queue_id FROM queues WHERE queue_name = ?", (queue,))
    queue_row = cursor.fetchone()

    cursor.execute("SELECT priority_id FROM priorities WHERE priority_name = ?", (priority,))
    priority_row = cursor.fetchone()

    conn.close()

    return (
        type_row[0] if type_row else None,
        queue_row[0] if queue_row else None,
        priority_row[0] if priority_row else None
    )


def insert_ticket_and_log(subject, body, ticket_type, queue, predicted_priority, 
                            action, response_text, status):
    """Insert a new ticket and its agent log entry. Returns the new ticket_id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    type_id, queue_id, priority_id = get_lookup_ids(ticket_type, queue, predicted_priority)

    cursor.execute("""
        INSERT INTO tickets (subject, body, type_id, queue_id, predicted_priority_id, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (subject, body, type_id, queue_id, priority_id, status))

    ticket_id = cursor.lastrowid

    resolved_by = 'ai' if action == 'auto_resolve' else 'ai_drafted'

    cursor.execute("""
        INSERT INTO agent_logs (ticket_id, action_taken, response_text, resolved_by)
        VALUES (?, ?, ?, ?)
    """, (ticket_id, action, response_text, resolved_by))

    conn.commit()
    conn.close()

    return ticket_id