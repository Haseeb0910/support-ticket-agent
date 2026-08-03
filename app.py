import streamlit as st
import sys, os
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
sys.path.append(os.path.dirname(__file__))

from src.agent.graph import agent

st.set_page_config(
    page_title="Support Ticket AI",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for a polished dark theme ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #22d3ee);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .sub-header {
        color: #9ca3af;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161b22;
        padding: 6px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        border-radius: 8px;
        color: #9ca3af;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: white !important;
    }
    
    .result-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 24px;
        margin-top: 20px;
    }
    
    .badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-right: 8px;
    }
    
    .badge-high { background-color: #7f1d1d; color: #fca5a5; }
    .badge-medium { background-color: #78350f; color: #fcd34d; }
    .badge-low { background-color: #14532d; color: #86efac; }
    .badge-resolved { background-color: #14532d; color: #86efac; }
    .badge-review { background-color: #713f12; color: #fde68a; }
    
    .response-box {
        background-color: #0d1117;
        border-left: 3px solid #6366f1;
        padding: 16px 20px;
        border-radius: 8px;
        margin-top: 16px;
        white-space: pre-wrap;
        line-height: 1.6;
        color: #e5e7eb;
    }
    
    div.stButton > button {
        background: linear-gradient(90deg, #6366f1, #4f46e5);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        width: 100%;
    }
    
    div.stButton > button:hover {
        background: linear-gradient(90deg, #4f46e5, #4338ca);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎫 Support Ticket AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated ticket triage, resolution, and analytics</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📩 Submit Ticket", "📊 Admin Dashboard"])

QUEUES = ['Billing and Payments', 'Customer Service', 'General Inquiry', 'Human Resources',
          'IT Support', 'Product Support', 'Returns and Exchanges', 'Sales and Pre-Sales',
          'Service Outages and Maintenance', 'Technical Support']
TYPES = ['Incident', 'Request', 'Problem', 'Change']

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("#### New Ticket")
        subject = st.text_input("Subject", placeholder="Brief summary of the issue")
        body = st.text_area("Description", height=180, placeholder="Describe your issue in detail...")
        
        c1, c2 = st.columns(2)
        with c1:
            ticket_type = st.selectbox("Ticket Type", TYPES)
        with c2:
            queue = st.selectbox("Category", QUEUES)
        
        submit = st.button("Submit Ticket →")

    with col2:
        st.markdown("#### Agent Response")
        
        if submit:
            if not subject or not body:
                st.warning("Please fill in both subject and description.")
            else:
                with st.spinner("Agent is processing your ticket..."):
                    result = agent.invoke({
                        'subject': subject,
                        'body': body,
                        'ticket_type': ticket_type,
                        'queue': queue,
                        'predicted_priority': '',
                        'retrieved_matches': [],
                        'top_similarity_distance': 0.0,
                        'action': '',
                        'response_text': ''
                    })
                
                priority = result['predicted_priority']
                action = result['action']
                
                priority_badge_class = f"badge-{priority}"
                status_text = "Auto-Resolved" if action == 'auto_resolve' else "Escalated for Review"
                status_badge_class = "badge-resolved" if action == 'auto_resolve' else "badge-review"
                
                st.markdown(f"""
                <div class="result-card">
                    <span class="badge {priority_badge_class}">{priority.upper()} PRIORITY</span>
                    <span class="badge {status_badge_class}">{status_text}</span>
                    <div class="response-box">{result['response_text']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Fill out the form and submit to see the AI agent's response here.")
            

with tab2:
    conn = sqlite3.connect('data/support_tickets.db')

    # Pull joined data for analysis
    df = pd.read_sql_query("""
        SELECT t.ticket_id, t.subject, t.status, t.created_at,
               q.queue_name, p.priority_name, tt.type_name,
               al.action_taken, al.resolved_by, al.response_text
        FROM tickets t
        LEFT JOIN queues q ON t.queue_id = q.queue_id
        LEFT JOIN priorities p ON t.predicted_priority_id = p.priority_id
        LEFT JOIN ticket_types tt ON t.type_id = tt.type_id
        LEFT JOIN agent_logs al ON t.ticket_id = al.ticket_id
    """, conn)
    conn.close()

    # --- Metrics row ---
    total_tickets = len(df)
    resolved_count = len(df[df['action_taken'] == 'auto_resolve'])
    escalated_count = len(df[df['action_taken'] == 'escalate'])
    resolution_rate = (resolved_count / (resolved_count + escalated_count) * 100) if (resolved_count + escalated_count) > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tickets", f"{total_tickets:,}")
    m2.metric("Auto-Resolved", f"{resolved_count:,}")
    m3.metric("Escalated", f"{escalated_count:,}")
    m4.metric("AI Resolution Rate", f"{resolution_rate:.1f}%")

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Priority Distribution")
        priority_counts = df['priority_name'].value_counts().reset_index()
        priority_counts.columns = ['priority', 'count']
        
        fig = px.pie(
            priority_counts, values='count', names='priority',
            color='priority',
            color_discrete_map={'high': '#ef4444', 'medium': '#f59e0b', 'low': '#22c55e'},
            hole=0.5
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e5e7eb',
            showlegend=True,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### Tickets by Category")
        queue_counts = df['queue_name'].value_counts().reset_index()
        queue_counts.columns = ['queue', 'count']

        fig2 = px.bar(
            queue_counts, x='count', y='queue', orientation='h',
            color='count', color_continuous_scale='Purples'
        )
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e5e7eb',
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=20, r=20),
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Recent Tickets")

    recent = df[df['response_text'].notna()].tail(10).iloc[::-1]
    for _, row in recent.iterrows():
        status_label = "🟢 Resolved" if row['action_taken'] == 'auto_resolve' else "🟡 Escalated"
        with st.expander(f"#{row['ticket_id']} — {row['subject']} · {status_label}"):
            st.markdown(f"**Priority:** {row['priority_name']} · **Category:** {row['queue_name']}")
            st.markdown(row['response_text'])