import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
from src.agent.graph import agent

# Load a sample of historical tickets to run through the live agent
df = pd.read_csv('data/raw/aa_dataset-tickets-multi-lang-5-2-50-version.csv')
en = df[df['language'] == 'en'].dropna(subset=['subject', 'body', 'type', 'queue', 'priority']).reset_index(drop=True)
# Take a random sample - mix of priorities for a realistic-looking dashboard
sample = en.sample(n=25, random_state=7)

print(f"Processing {len(sample)} tickets through the agent...\n")

for i, (_, row) in enumerate(sample.iterrows(), 1):
    print(f"[{i}/{len(sample)}] Processing: {row['subject'][:50]}...")
    try:
        result = agent.invoke({
            'subject': row['subject'],
            'body': row['body'],
            'ticket_type': row['type'],
            'queue': row['queue'],
            'predicted_priority': '',
            'retrieved_matches': [],
            'top_similarity_distance': 0.0,
            'action': '',
            'response_text': ''
        })
        print(f"   -> priority={result['predicted_priority']}, action={result['action']}")
    except Exception as e:
        print(f"   -> ERROR: {e}")

print("\nBatch processing complete.")