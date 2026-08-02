from typing import TypedDict, List
import os
import re
from dotenv import load_dotenv

load_dotenv()  # loads GROQ_API_KEY from .env into environment - must happen before Groq client is created

import joblib
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph, END
from groq import Groq

# --- Load saved artifacts once at module level ---
clf = joblib.load('src/models/priority_classifier.joblib')
ohe = joblib.load('src/models/queue_type_encoder.joblib')
tfidf = joblib.load('src/models/body_tfidf_vectorizer.joblib')

embed_model = SentenceTransformer('all-MiniLM-L6-v2')
faiss_index = faiss.read_index('src/rag/ticket_index.faiss')
ticket_metadata = pd.read_csv('src/rag/ticket_metadata.csv')

groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY'))


def clean_text(text):
    text = text.lower()
    text = text.replace('\\n', ' ').replace('\\r', ' ').replace('\\t', ' ')
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# --- State definition ---
class TicketState(TypedDict):
    subject: str
    body: str
    ticket_type: str
    queue: str
    predicted_priority: str
    retrieved_matches: List[dict]
    top_similarity_distance: float
    action: str
    response_text: str


# --- Node 1: classify priority ---
def classify_ticket(state: TicketState) -> TicketState:
    body_clean = clean_text(state['body'])

    cat_features = ohe.transform(pd.DataFrame(
        [[state['ticket_type'], state['queue']]],
        columns=['type', 'queue']
    ))
    text_features = tfidf.transform([body_clean])

    from scipy.sparse import hstack
    combined = hstack([cat_features, text_features])

    prediction = clf.predict(combined)[0]
    state['predicted_priority'] = prediction
    return state


# --- Node 2: retrieve similar tickets ---
def retrieve_similar(state: TicketState) -> TicketState:
    query_embedding = embed_model.encode([state['body']])
    distances, indices = faiss_index.search(
        np.array(query_embedding).astype('float32'), k=3
    )

    matches = ticket_metadata.iloc[indices[0]][['subject', 'body', 'answer']].to_dict('records')
    state['retrieved_matches'] = matches
    state['top_similarity_distance'] = float(distances[0][0])
    return state


# --- Node 3: decide action ---
def decide_action(state: TicketState) -> TicketState:
    SIMILARITY_THRESHOLD = 0.6  # lower distance = more similar; tune this later

    if state['predicted_priority'] == 'high':
        state['action'] = 'escalate'
    elif state['top_similarity_distance'] <= SIMILARITY_THRESHOLD:
        state['action'] = 'auto_resolve'
    else:
        state['action'] = 'escalate'

    return state


# --- Conditional edge function (tells LangGraph which path to take) ---
def route_decision(state: TicketState) -> str:
    return state['action']  # returns 'auto_resolve' or 'escalate'


# --- Node 4a: auto resolve ---
def auto_resolve(state: TicketState) -> TicketState:
    context = "\n\n".join([
        f"Past similar ticket: {m['subject']}\nResolution: {m['answer']}"
        for m in state['retrieved_matches'][:2]
    ])

    prompt = f"""You are a customer support agent. A customer submitted this ticket:

Subject: {state['subject']}
Message: {state['body']}

Here are similar past tickets and how they were resolved:
{context}

Write a helpful, direct response to resolve this customer's issue, using the past resolutions as reference where relevant."""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    state['response_text'] = response.choices[0].message.content
    return state


# --- Node 4b: draft escalation ---
def draft_escalation(state: TicketState) -> TicketState:
    context = "\n\n".join([
        f"Past similar ticket: {m['subject']}\nResolution: {m['answer']}"
        for m in state['retrieved_matches'][:2]
    ])

    prompt = f"""You are a customer support agent drafting a response for HUMAN REVIEW before sending (this ticket was flagged as high priority or lacks a confident match).

Subject: {state['subject']}
Message: {state['body']}
Predicted priority: {state['predicted_priority']}

Similar past tickets for reference:
{context}

Write a draft response a human agent could review and send, and briefly note (in one sentence at the end) why this needs human review."""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    state['response_text'] = response.choices[0].message.content
    return state

# --- Build the graph ---
def build_agent_graph():
    workflow = StateGraph(TicketState)

    workflow.add_node("classify_ticket", classify_ticket)
    workflow.add_node("retrieve_similar", retrieve_similar)
    workflow.add_node("decide_action", decide_action)
    workflow.add_node("auto_resolve", auto_resolve)
    workflow.add_node("draft_escalation", draft_escalation)

    workflow.set_entry_point("classify_ticket")
    workflow.add_edge("classify_ticket", "retrieve_similar")
    workflow.add_edge("retrieve_similar", "decide_action")

    workflow.add_conditional_edges(
        "decide_action",
        route_decision,
        {
            "auto_resolve": "auto_resolve",
            "escalate": "draft_escalation"
        }
    )

    workflow.add_edge("auto_resolve", END)
    workflow.add_edge("draft_escalation", END)

    return workflow.compile()


agent = build_agent_graph()