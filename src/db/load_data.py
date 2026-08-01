import sqlite3
import pandas as pd
import re
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'support_tickets.db')
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 
                          'aa_dataset-tickets-multi-lang-5-2-50-version.csv')

def clean_text(text):
    if pd.isna(text):
        return ''
    text = text.lower()
    text = text.replace('\\n', ' ').replace('\\r', ' ').replace('\\t', ' ')
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_tickets():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load and filter dataset
    df = pd.read_csv(CSV_PATH)
    en = df[df['language'] == 'en'].copy()
    en = en.dropna(subset=['body', 'type', 'queue', 'priority'])

    # Build lookup dicts: name -> id
    cursor.execute("SELECT type_id, type_name FROM ticket_types")
    type_map = {name: tid for tid, name in cursor.fetchall()}

    cursor.execute("SELECT queue_id, queue_name FROM queues")
    queue_map = {name: qid for qid, name in cursor.fetchall()}

    cursor.execute("SELECT priority_id, priority_name FROM priorities")
    priority_map = {name: pid for pid, name in cursor.fetchall()}

    # Insert tickets
    rows_inserted = 0
    for _, row in en.iterrows():
        type_id = type_map.get(row['type'])
        queue_id = queue_map.get(row['queue'])
        priority_id = priority_map.get(row['priority'])

        if type_id is None or queue_id is None or priority_id is None:
            continue  # skip rows with values not in our lookup tables

        cursor.execute("""
            INSERT INTO tickets (subject, body, type_id, queue_id, predicted_priority_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (row['subject'], row['body'], type_id, queue_id, priority_id, 'open'))
        rows_inserted += 1

    conn.commit()
    conn.close()
    print(f"Inserted {rows_inserted} tickets into the database")

if __name__ == '__main__':
    load_tickets()