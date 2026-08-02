import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.agent.graph import agent

test_ticket = {
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

result = agent.invoke(test_ticket)

print("Predicted priority:", result['predicted_priority'])
print("Action:", result['action'])
print("\nResponse:")
print(result['response_text'])