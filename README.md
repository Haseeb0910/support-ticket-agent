# 🎫 Support Ticket AI

An end-to-end AI-powered customer support system that automatically classifies, triages, and resolves support tickets — combining a trained ML classifier, a LangGraph agent with RAG-based retrieval, a relational database, and a live analytics dashboard.

Built as a portfolio project to demonstrate a full ML + AI systems pipeline: from raw data to a working, demoable product.

---

## 🧠 What It Does

1. A customer submits a support ticket (subject + description + category)
2. A **trained Random Forest classifier** predicts the ticket's priority (low / medium / high)
3. A **FAISS similarity search** retrieves the most relevant past tickets and their resolutions
4. A **LangGraph agent** decides whether to:
   - **Auto-resolve** — generate a direct response using retrieved context, or
   - **Escalate** — draft a response for human review, with a note explaining why
5. Every ticket and agent decision is logged to a **relational SQLite database**
6. An **admin dashboard** surfaces live analytics: ticket volume, priority breakdown, category trends, and resolution rates

---

## 🏗️ Architecture

```
                    ┌─────────────────┐
                    │   New Ticket    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ classify_ticket │  ← Random Forest (queue+type+TF-IDF)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ retrieve_similar│  ← FAISS + sentence-transformers
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  decide_action  │  ← priority + similarity threshold
                    └────┬───────┬────┘
                         │       │
                         ▼       ▼
              ┌──────────────┐ ┌───────────────────┐
              │ auto_resolve │ │  draft_escalation  │  ← LLM response (Groq/Llama)
              └──────┬───────┘ └─────────┬──────────┘
                     │                   │
                     └─────────┬─────────┘
                               ▼
                      ┌─────────────────┐
                      │    log_to_db    │  ← SQLite (tickets + agent_logs)
                      └─────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| ML Classification | scikit-learn (Random Forest, TF-IDF, One-Hot Encoding) |
| Agent Orchestration | LangGraph |
| Retrieval (RAG) | FAISS + sentence-transformers (`all-MiniLM-L6-v2`) |
| LLM | Groq (Llama 3.1 8B Instant) |
| Database | SQLite (normalized relational schema) |
| UI | Streamlit + Plotly |

---

## 📊 Dataset

- **Source**: [Multilingual Customer Support Tickets](https://www.kaggle.com/datasets/tobiasbueck/multilingual-customer-support-tickets) (Kaggle)
- **Size**: 16,338 English-language tickets after filtering
- **Fields used**: subject, body, answer (historical resolution), type, queue (category), priority

An earlier candidate dataset was evaluated and discarded after EDA revealed templated/corrupted ticket text (unfilled placeholder fields and garbled filler content) — see [`data/README.md`](data/README.md) for details on dataset selection.

---

## 🔍 Key Findings from EDA

- **Ticket length has no relationship with priority** — short and long tickets are equally likely to be any priority level.
- **Queue category is a moderate predictor of priority** (e.g., "Service Outages and Maintenance" skews heavily toward high priority; "General Inquiry" skews toward low).
- **Raw word frequency was misleading** — the top 15 words were nearly identical across all priority classes, suggesting text wouldn't help. This was **contradicted** by actual model results (see below), where TF-IDF text features nearly doubled classifier accuracy. Lesson: surface-level word-frequency EDA can under-represent the signal a real model can extract from subtler word combinations.

---

## 🤖 Model Performance

Multiple approaches were tested and compared on a held-out test set (stratified 80/20 split):

| Model | Features | Accuracy |
|---|---|---|
| Random Forest | queue + type only | 49.2% |
| **Random Forest (final)** | **queue + type + body TF-IDF** | **79.3%** |
| Random Forest | + subject text | 79.3% (no improvement — redundant with body) |
| Random Forest | + bigrams, 5000 features | 78.9% (no improvement) |
| Logistic Regression | queue + type + body TF-IDF | 60.2% (worse than Random Forest) |

**Final model**: Random Forest (200 trees) on one-hot encoded `queue`/`type` + TF-IDF vectorized `body` text (3,000 features, unigrams).

---

## ⚠️ Known Limitations

- **Priority classification is not perfectly reliable on security-sensitive language.** During batch testing, two similarly-worded tickets both mentioning data breaches received different priority predictions (one correctly flagged high, one incorrectly predicted medium). This highlights a real limitation of the current model and is part of the justification for keeping a human-in-the-loop escalation path rather than fully automating resolution.
- The training dataset is synthetically generated, which likely limits how much real-world nuance (e.g., tone, urgency cues in phrasing) the model can learn. Retraining on real, anonymized support data would likely improve robustness.
- Historical tickets loaded directly from the dataset don't have `agent_logs` entries (only tickets processed live through the agent do) — this is by design, but means dashboard metrics reflect only agent-processed tickets, not the full historical set.

---

## 📁 Project Structure

```
support-ticket-agent/
├── data/
│   ├── raw/                    # source dataset
│   └── support_tickets.db      # SQLite database
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_preprocessing_baseline.ipynb
│   └── 03_rag_setup.ipynb
├── src/
│   ├── agent/
│   │   ├── graph.py             # LangGraph agent definition
│   │   ├── batch_process.py     # batch-run historical tickets through agent
│   │   ├── test_nodes.py        # unit tests for individual agent nodes
│   │   └── test_graph.py        # end-to-end agent test
│   ├── db/
│   │   ├── schema.sql
│   │   ├── init_db.py
│   │   ├── load_data.py
│   │   └── db_utils.py
│   ├── models/                  # trained classifier + vectorizers (gitignored)
│   └── rag/                     # FAISS index + metadata
├── app.py                       # Streamlit UI (submission + dashboard)
├── requirements.txt
└── README.md
```

---

## 🚀 Setup & Installation

```bash
# Clone the repo
git clone https://github.com/Haseeb0910/support-ticket-agent.git
cd support-ticket-agent

# Install dependencies
pip install -r requirements.txt

# Set up your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# Initialize the database
python src/db/init_db.py
python src/db/load_data.py

# Train the classifier and build the RAG index
# (run notebooks/02_preprocessing_baseline.ipynb and notebooks/03_rag_setup.ipynb)

# Launch the app
streamlit run app.py
```

---

## 🔮 Future Improvements

- Retrain the classifier on real (anonymized) support ticket data to reduce synthetic-data artifacts
- Add confidence scores to the dashboard alongside predictions
- Support multi-turn ticket conversations rather than single-message submissions
- Add authentication for the admin dashboard
- Deploy with a production database (PostgreSQL) instead of SQLite

---

## 👤 Author

**Haseeb ur Rehman**
[GitHub](https://github.com/Haseeb0910) · [LinkedIn](https://linkedin.com/in/haseeburrehman1098)
