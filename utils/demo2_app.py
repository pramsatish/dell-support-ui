 # demo2_app.py
import streamlit as st
import os
from datetime import datetime
import textwrap
import pandas as pd


# CSS 

st.set_page_config(page_title="Dell Support — Demo", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    :root{
        --accent: #0b6cf2;
        --accent-2: #0f76ff;
        --muted: #6b7280;
        --card: #ffffff;
        --bg: #f6f8fb;
        --panel-radius: 12px;
    }
    body { background: var(--bg); }
    .stApp { color: #0f1724; }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #ffffff, #f8fbff);
        border-right: 1px solid rgba(15,23,36,0.04);
    }
    .big-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .muted { color: var(--muted); font-size: 14px; }
    .card {
        background: var(--card);
        padding: 18px;
        border-radius: var(--panel-radius);
        box-shadow: 0 6px 18px rgba(12, 24, 48, 0.06);
    }
    .accent-btn {
        background: linear-gradient(90deg, var(--accent), var(--accent-2));
        color: white;
        border: none;
        padding: 8px 14px;
        border-radius: 8px;
    }
    .ticket-box { border-left: 4px solid var(--accent); padding: 14px; border-radius: 8px; background: #fff; }
    .kbd { background:#f3f6fb; padding:6px 10px; border-radius:6px; font-size:13px; color:#0b6cf2; }
    </style>
    """,
    unsafe_allow_html=True,
)

def init_state():
    if "tickets" not in st.session_state:
        st.session_state.tickets = []
    if "chat" not in st.session_state:
        st.session_state.chat = {}  
    if "rag_chat" not in st.session_state:
        st.session_state.rag_chat = {}  
    if "agent_feedback" not in st.session_state:
        st.session_state.agent_feedback = []
    if "agent_name" not in st.session_state:
        st.session_state.agent_name = "Agent-1"
    if "selected_ticket" not in st.session_state:
        st.session_state.selected_ticket = None

init_state()


def create_ticket_id():
    return f"TCK-{len(st.session_state.tickets)+1:03}"

def save_uploaded_file(uploaded_file, target_dir="docs/dell-data"):
    os.makedirs(target_dir, exist_ok=True)
    save_path = os.path.join(target_dir, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path

def ticket_df():
    if not st.session_state.tickets:
        return pd.DataFrame(columns=["id","email","category","priority","status","agent","created_at"])
    return pd.DataFrame(st.session_state.tickets)


# SIDEBAR

with st.sidebar:
    st.markdown("<div style='padding:14px 6px'>", unsafe_allow_html=True)
    st.markdown("<div style='font-weight:800; font-size:18px; margin-bottom:8px'>Dell Support System</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    role = st.radio("Select your role", ["User", "Support Agent", "Content Manager"], index=0)

    st.markdown("---")
    st.markdown("<div class='muted'>Tip: Upload docs in Content Manager to improve KB (UI-only)</div>", unsafe_allow_html=True)


st.markdown("<div class='big-title'>Support System</div>", unsafe_allow_html=True)



# USER PAGE

def user_page():
    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown("<div class='card'><strong>Raise a Ticket</strong><div class='muted'>Report an issue</div></div>", unsafe_allow_html=True)
        with st.form("raise_ticket_form"):
            email = st.text_input("Your email")
            category = st.selectbox("Category", ["Login Issue", "Hardware Issue", "Software Bug", "Warranty", "Other"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            message = st.text_area("Describe the issue", height=120)
            submitted = st.form_submit_button("Submit Ticket")
            if submitted:
                if not email or not message.strip():
                    st.warning("Please provide your email and a short description.")
                else:
                    tid = create_ticket_id()
                    st.session_state.tickets.append({
                        "id": tid,
                        "email": email,
                        "message": message.strip(),
                        "category": category,
                        "priority": priority,
                        "status": "Open",
                        "agent": "Not Assigned",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.success(f"Ticket {tid} created.")

    with col2:
        st.markdown("<div class='card'><strong>Your Tickets</strong><div class='muted'>Track status & open chat</div></div>", unsafe_allow_html=True)
        user_email = st.text_input("Filter by your email (leave empty to see all)", value="")
        tickets = st.session_state.tickets
        filtered = [t for t in tickets if (user_email.strip() == "" or t["email"] == user_email.strip())]
        if not filtered:
            st.info("No tickets found.")
        else:
            for t in filtered:
                st.markdown(f"<div class='ticket-box' style='margin-top:10px'>", unsafe_allow_html=True)
                st.markdown(f"**{t['id']}**  ·  {t['category']}  ·  <span class='muted'>Priority: {t['priority']}</span>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top:8px'>{t['message']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top:8px' class='muted'>Status: {t['status']}  ·  Agent: {t['agent']}</div>", unsafe_allow_html=True)
                btn_col1, btn_col2 = st.columns([1,1])
                with btn_col1:
                    if st.button("Open Chat", key=f"openchat_{t['id']}"):
                        st.session_state.selected_ticket = t['id']
                        st.experimental_rerun()
                with btn_col2:
                    if st.button("Copy ID", key=f"copy_{t['id']}"):
                        st.write(f"Ticket ID: {t['id']}")
                st.markdown("</div>", unsafe_allow_html=True)

        
        if st.session_state.selected_ticket:
            sel = st.session_state.selected_ticket
            st.markdown(f"<div class='card'><strong>Chat — {sel}</strong><div class='muted'>Two-way messages (demo)</div></div>", unsafe_allow_html=True)
            if sel not in st.session_state.chat:
                st.session_state.chat[sel] = []
            
            for m in st.session_state.chat[sel]:
                st.markdown(m, unsafe_allow_html=True)
            user_msg = st.text_input("Type a message to the agent", key=f"usermsg_{sel}")
            if st.button("Send", key=f"send_user_{sel}"):
                if user_msg.strip():
                    st.session_state.chat[sel].append(f"<div style='padding:8px; border-radius:8px; background:#eef6ff; margin-bottom:6px'><strong>You:</strong> {user_msg}</div>")
                    # dummy agent reply
                    st.session_state.chat[sel].append(f"<div style='padding:8px; border-radius:8px; background:#f7f7fb; margin-bottom:6px'><strong>{st.session_state.agent_name}:</strong> Thanks — we'll check and update you shortly.</div>")
                    st.experimental_rerun()
                else:
                    st.warning("Message is empty.")


# AGENT PAGE

def agent_page():
    left_col, right_col = st.columns([2, 3])

    with left_col:
        st.markdown("<div class='card'><strong>New Ticket Queue</strong><div class='muted'>Pick a ticket to handle</div></div>", unsafe_allow_html=True)
        queue = [t for t in st.session_state.tickets if t["status"] in ("Open", "In Progress")]
        if not queue:
            st.info("No tickets in queue.")
        else:
            for t in queue:
                st.markdown(f"<div class='ticket-box' style='margin-top:10px'>", unsafe_allow_html=True)
                st.markdown(f"**{t['id']}**  ·  {t['category']}  ·  <span class='muted'>Priority: {t['priority']}</span>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-top:8px' class='muted'>From: {t['email']} · Created: {t['created_at']}</div>", unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns([1,1,1])
                with col_a:
                    if st.button("Assign to me", key=f"assign_{t['id']}"):
                        t["agent"] = st.session_state.agent_name
                        t["status"] = "In Progress"
                        st.success(f"{t['id']} assigned to you")
                        st.experimental_rerun()
                with col_b:
                    if st.button("Open", key=f"open_{t['id']}"):
                        st.session_state.selected_ticket = t['id']
                        st.experimental_rerun()
                with col_c:
                    if st.button("Mark Resolved", key=f"resolve_{t['id']}"):
                        t["status"] = "Resolved"
                        st.success(f"{t['id']} marked resolved")
                        st.experimental_rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("<div class='card'><strong>Handle Ticket</strong><div class='muted'>Chat with user, consult RAG, and give feedback</div></div>", unsafe_allow_html=True)
        if not st.session_state.selected_ticket:
            st.info("Select a ticket from the left queue (Assign/Open).")
            return

        sel = st.session_state.selected_ticket
        ticket = next((x for x in st.session_state.tickets if x["id"] == sel), None)
        if not ticket:
            st.warning("Ticket not found.")
            return

        st.markdown(f"<div style='margin-bottom:8px'><strong>{ticket['id']}</strong>  ·  {ticket['category']}  ·  <span class='muted'>Priority: {ticket['priority']} · Status: {ticket['status']}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card' style='margin-bottom:10px'><strong>User Query</strong><div style='margin-top:8px'>{ticket['message']}</div></div>", unsafe_allow_html=True)

        # two-column layout for chats
        c1, c2 = st.columns([1.6, 1])
        with c1:
            st.markdown("<div class='card'><strong>Chat with User</strong><div class='muted'>Two-way messages</div></div>", unsafe_allow_html=True)
            if sel not in st.session_state.chat:
                st.session_state.chat[sel] = []
            for m in st.session_state.chat[sel]:
                st.markdown(m, unsafe_allow_html=True)
            agent_msg = st.text_input("Type message to user", key=f"agent_msg_{sel}")
            if st.button("Send to user", key=f"send_agent_{sel}"):
                if agent_msg.strip():
                    st.session_state.chat[sel].append(f"<div style='padding:8px; border-radius:8px; background:#eef9f5; margin-bottom:6px'><strong>{st.session_state.agent_name}:</strong> {agent_msg}</div>")
                    st.success("Message sent to user (demo)")
                    st.experimental_rerun()
                else:
                    st.warning("Message empty!")

        with c2:
            st.markdown("<div class='card'><strong>RAG Assistant</strong><div class='muted'>Ask the retrieval assistant for suggestions</div></div>", unsafe_allow_html=True)
            if sel not in st.session_state.rag_chat:
                st.session_state.rag_chat[sel] = []
            for m in st.session_state.rag_chat[sel]:
                st.markdown(m, unsafe_allow_html=True)
            rag_q = st.text_input("Ask RAG (e.g., recommended fix?)", key=f"rag_q_{sel}")
            if st.button("Query RAG", key=f"query_rag_{sel}"):
                if rag_q.strip():
                    st.session_state.rag_chat[sel].append(f"<div style='padding:8px; border-radius:8px; background:#eef6ff; margin-bottom:6px'><strong>Agent → RAG:</strong> {rag_q}</div>")
                    reply = textwrap.dedent(f"""
                    <div style='padding:8px; border-radius:8px; background:#f7fbff; margin-bottom:6px'>
                    <strong>RAG:</strong> Based on KB matches (demo):
                    <ul style='margin-top:6px'>
                      <li>Recommended action: Restart the device & update BIOS</li>
                      <li>Relevant article: <span class='kbd'>dell-battery-troubleshoot.docx</span></li>
                      <li>Confidence: Medium</li>
                    </ul>
                    </div>
                    """)
                    st.session_state.rag_chat[sel].append(reply)
                    st.experimental_rerun()
                else:
                    st.warning("Empty query!")

        st.markdown("---")
        st.markdown("<div class='card'><strong>Provide Feedback & Update Ticket</strong><div class='muted'>Help Content Manager improve KB</div></div>", unsafe_allow_html=True)
        colf1, colf2 = st.columns([2,1])
        with colf1:
            usefulness = st.selectbox("RAG Usefulness", ["Very Useful", "Somewhat Useful", "Not Useful"], key=f"useful_{sel}")
            missing_suggest = st.text_area("Suggest missing KB article (optional)", key=f"missing_{sel}", height=80)
        with colf2:
            new_status = st.selectbox("Update Ticket Status", ["In Progress", "Waiting for User", "Resolved"], index=0, key=f"status_{sel}")
            if st.button("Submit Feedback & Update", key=f"submit_feedback_{sel}"):
                ticket["status"] = new_status
                st.session_state.agent_feedback.append({
                    "ticket_id": sel,
                    "agent": st.session_state.agent_name,
                    "usefulness": usefulness,
                    "missing_kb": missing_suggest,
                    "status": new_status,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.success("Feedback submitted & ticket updated.")
                st.experimental_rerun()


# CONTENT MANAGER PAGE

def content_manager_page():
    st.markdown("<div class='card'><strong>Content Manager Dashboard</strong><div class='muted'>Review feedback and manage KB</div></div>", unsafe_allow_html=True)
    tabs = st.tabs(["Feedback Overview", "Upload Documents", "Knowledge Base"])

    # Feedback 
    with tabs[0]:
        st.subheader("Agent Feedback")
        feedback = st.session_state.agent_feedback
        if not feedback:
            st.info("No feedback submitted yet.")
        else:
            df = pd.DataFrame(feedback)
            total = len(df)
            helpful = df[df["usefulness"] == "Very Useful"].shape[0] if "usefulness" in df else 0
            col1, col2 = st.columns(2)
            col1.metric("Total Feedbacks", total)
            col2.metric("Very Useful", helpful)

            st.markdown("---")
            if not df.empty and "usefulness" in df:
                benefit = df["usefulness"].value_counts()
                st.bar_chart(benefit)

            st.markdown("---")
            # detailed list
            for _, row in df.sort_values(by="timestamp", ascending=False).iterrows():
                st.markdown(f"<div class='card' style='margin-bottom:10px'><strong>Ticket {row['ticket_id']}</strong><div class='muted'>By {row['agent']} · {row['timestamp']}</div><div style='margin-top:8px'><b>Usefulness:</b> {row['usefulness']}<br/><b>Missing KB:</b> {row['missing_kb'] if row['missing_kb'] else '—'}<br/><b>Status:</b> {row['status']}</div></div>", unsafe_allow_html=True)

    # Upload docs
    with tabs[1]:
        st.subheader("Upload New KB Document")
        st.markdown("<div class='muted'>Upload .docx files to improve the knowledge base (UI-only upload saved to docs/dell-data)</div>", unsafe_allow_html=True)
        upload = st.file_uploader("Upload .docx (multiple allowed)", type=["docx"], accept_multiple_files=True)
        if upload:
            for f in upload:
                save_path = save_uploaded_file(f)
                st.success(f"Saved: {os.path.basename(save_path)}")
        st.markdown("")
        if st.button("Rebuild Embeddings (UI-only)"):
            st.success("Embeddings rebuild started (demo - UI only)")

    # KB viewer
    with tabs[2]:
        st.subheader("Knowledge Base Snapshot")
        kb_dir = "docs/dell-data"
        if not os.path.exists(kb_dir):
            st.info("No KB documents uploaded yet.")
        else:
            files = sorted(os.listdir(kb_dir))
            if not files:
                st.info("No KB documents uploaded yet.")
            else:
                for fn in files:
                    st.markdown(f"<div class='card' style='margin-bottom:8px'><strong>{fn}</strong><div class='muted'>Stored in {kb_dir}</div></div>", unsafe_allow_html=True)


# ROUTER

if role == "User":
    user_page()
elif role == "Support Agent":
    agent_page()
elif role == "Content Manager":
    content_manager_page()
else:
    st.info("Choose a role from the sidebar.")


