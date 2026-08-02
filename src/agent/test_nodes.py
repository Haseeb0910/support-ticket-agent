import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.agent.graph import classify_ticket, retrieve_similar, TicketState

# Build a fake test ticket, similar to what a real user might submit
test_state: TicketState = {
    'subject': 'Video call keeps disconnecting',
    'body': "I'm having an issue with my video conferencing software. The connection keeps dropping every few minutes during important calls. I've already tried restarting my router but the problem persists.",
    'ticket_type': 'Incident',
    'queue': 'Technical Support',
    'predicted_priority': '',
    'retrieved_matches': [],
    'top_similarity_distance': 0.0,
    'action': '',
    'response_text': ''
}

print("=== BEFORE ===")
print(test_state)

print("\n=== RUNNING classify_ticket ===")
test_state = classify_ticket(test_state)
print("Predicted priority:", test_state['predicted_priority'])

print("\n=== RUNNING retrieve_similar ===")
test_state = retrieve_similar(test_state)
print("Top similarity distance:", test_state['top_similarity_distance'])
print("\nTop 3 matches:")
for i, match in enumerate(test_state['retrieved_matches']):
    print(f"\n--- Match {i+1} ---")
    print("Subject:", match['subject'])
    print("Answer:", match['answer'][:200])
    
print("\n=== RUNNING decide_action ===")
from src.agent.graph import decide_action, auto_resolve, draft_escalation

test_state = decide_action(test_state)
print("Action decided:", test_state['action'])

if test_state['action'] == 'auto_resolve':
    print("\n=== RUNNING auto_resolve ===")
    test_state = auto_resolve(test_state)
else:
    print("\n=== RUNNING draft_escalation ===")
    test_state = draft_escalation(test_state)

print("\nGenerated response:")
print(test_state['response_text'])

print("\n\n=== SECOND TEST: lower priority ticket ===")

test_state_2: TicketState = {
    'subject': 'Question about invoice',
    'body': "Hi, I have a quick question about my last invoice. Could you clarify what the service fee covers? Not urgent, just want to understand my bill better.",
    'ticket_type': 'Request',
    'queue': 'Billing and Payments',
    'predicted_priority': '',
    'retrieved_matches': [],
    'top_similarity_distance': 0.0,
    'action': '',
    'response_text': ''
}

test_state_2 = classify_ticket(test_state_2)
print("Predicted priority:", test_state_2['predicted_priority'])

test_state_2 = retrieve_similar(test_state_2)
print("Top similarity distance:", test_state_2['top_similarity_distance'])

test_state_2 = decide_action(test_state_2)
print("Action decided:", test_state_2['action'])

if test_state_2['action'] == 'auto_resolve':
    test_state_2 = auto_resolve(test_state_2)
else:
    test_state_2 = draft_escalation(test_state_2)

print("\nGenerated response:")
print(test_state_2['response_text'])