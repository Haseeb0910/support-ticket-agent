CREATE TABLE ticket_types (
    type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT UNIQUE NOT NULL
);

CREATE TABLE queues (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    queue_name TEXT UNIQUE NOT NULL
);

CREATE TABLE priorities (
    priority_id INTEGER PRIMARY KEY AUTOINCREMENT,
    priority_name TEXT UNIQUE NOT NULL
);

CREATE TABLE tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT,
    body TEXT NOT NULL,
    type_id INTEGER,
    queue_id INTEGER,
    predicted_priority_id INTEGER,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES ticket_types(type_id),
    FOREIGN KEY (queue_id) REFERENCES queues(queue_id),
    FOREIGN KEY (predicted_priority_id) REFERENCES priorities(priority_id)
);

CREATE TABLE agent_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    action_taken TEXT NOT NULL,
    confidence_score REAL,
    response_text TEXT,
    resolved_by TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
);