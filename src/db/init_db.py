import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'support_tickets.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, 'r') as f:
        cursor.executescript(f.read())

    # Seed lookup tables based on your dataset's known categories
    ticket_types = ['Incident', 'Request', 'Problem', 'Change']  # confirm against your actual 'type' values
    queues = ['Billing and Payments', 'Customer Service', 'General Inquiry', 'Human Resources',
              'IT Support', 'Product Support', 'Returns and Exchanges', 'Sales and Pre-Sales',
              'Service Outages and Maintenance', 'Technical Support']
    priorities = ['low', 'medium', 'high']

    cursor.executemany("INSERT OR IGNORE INTO ticket_types (type_name) VALUES (?)", [(t,) for t in ticket_types])
    cursor.executemany("INSERT OR IGNORE INTO queues (queue_name) VALUES (?)", [(q,) for q in queues])
    cursor.executemany("INSERT OR IGNORE INTO priorities (priority_name) VALUES (?)", [(p,) for p in priorities])

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == '__main__':
    init_db()