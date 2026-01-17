"""
AMPM - AI Meeting Product Manager
Streamlit UI for querying meeting knowledge graph

Usage:
    streamlit run app.py
"""

import os
import time
import traceback
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AMPM modules
from ampm import MeetingLoader, QueryEngine, MeetingGraph

# Page config
st.set_page_config(
    page_title="AMPM - AI Meeting Product Manager",
    page_icon="🕐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-top: 0;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .source-card {
        background: #f0f4f8;
        padding: 0.8rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        border-left: 3px solid #4a5568;
    }
    .decision-card {
        background: #e8f5e9;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #4caf50;
    }
    .action-card {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #2196f3;
    }
    .blocker-card {
        background: #ffebee;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #f44336;
    }
    .timing-badge {
        background: #667eea;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading meetings and building knowledge graph...")
def initialize_ampm(data_dir: str = "data/samples"):
    """
    Initialize AMPM by loading meetings and building knowledge graph.
    
    This is cached to avoid reprocessing on every page load.
    """
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        return None, None, "Missing OPENAI_API_KEY environment variable"
    
    try:
        # Initialize loader with graph
        print("Initializing AMPM...")
        loader = MeetingLoader()
        
        # Load meetings from directory
        print(f"Loading meetings from: {data_dir}")
        meetings = loader.load_directory(data_dir)
        print(f"Loaded {len(meetings)} meetings")
        
        if not meetings:
            return None, None, f"No meetings found in {data_dir}"
        
        # Get graph stats
        stats = loader.graph.get_stats()
        print(f"Graph stats: {stats}")
        
        # Create query engine
        engine = QueryEngine(loader.graph, loader.embeddings)
        
        return loader, engine, None
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"
        print(f"Error: {error_msg}")
        return None, None, error_msg


def render_sidebar(loader):
    """Render the sidebar with stats and info."""
    st.sidebar.markdown("## 🕐 AMPM")
    st.sidebar.markdown("*AI Meeting Product Manager*")
    
    # Cache clear button
    if st.sidebar.button("🔄 Reload Data"):
        st.cache_resource.clear()
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Stats
    if loader and loader.graph:
        stats = loader.graph.get_stats()
        
        st.sidebar.markdown("### 📊 Knowledge Graph Stats")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            st.metric("Meetings", stats.get('meetings', 0))
            st.metric("Decisions", stats.get('decisions', 0))
            st.metric("Topics", stats.get('topics', 0))
        
        with col2:
            st.metric("Actions", stats.get('action_items', 0))
            st.metric("Blockers", stats.get('blockers', 0))
            st.metric("People", stats.get('people', 0))
        
        st.sidebar.markdown("---")
    
    # Sample queries
    st.sidebar.markdown("### 💡 Try asking:")
    sample_queries = [
        "Why did we choose Stripe?",
        "What's blocking the payments launch?",
        "What decisions were made about mobile?",
        "What are Bob's action items?",
        "Tell me about the April outage"
    ]
    
    for query in sample_queries:
        st.sidebar.markdown(f"- *{query}*")


def render_ask_tab(engine: QueryEngine):
    """Render the Ask Questions tab."""
    st.markdown("### 🔍 Ask a Question")
    st.markdown("Ask about decisions, action items, blockers, or any meeting context.")
    
    # Query input
    question = st.text_input(
        "Your question:",
        placeholder="e.g., Why did we choose Stripe for payments?",
        key="question_input"
    )
    
    if st.button("Ask AMPM", type="primary"):
        if question:
            with st.spinner("Searching meeting knowledge..."):
                start_time = time.time()
                result = engine.query(question)
                elapsed = time.time() - start_time
            
            # Show timing
            st.markdown(f"<span class='timing-badge'>Answered in {elapsed:.2f}s</span>", unsafe_allow_html=True)
            
            # Show answer
            st.markdown("### Answer")
            st.markdown(result.answer)
            
            # Show confidence
            confidence = result.confidence
            confidence_color = "green" if confidence > 0.7 else "orange" if confidence > 0.4 else "red"
            st.markdown(f"**Confidence:** :{confidence_color}[{confidence:.0%}]")
            
            # Show sources
            if result.sources:
                st.markdown("### 📚 Sources")
                for source in result.sources[:5]:
                    st.markdown(f"""
                    <div class='source-card'>
                        <strong>{source.meeting_title or source.meeting_id}</strong> ({source.date or 'Unknown date'})<br/>
                        <em>{source.content_type}</em>: {source.content[:150]}...
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("Please enter a question.")


def render_decisions_tab(loader):
    """Render the Decision Ledger tab."""
    st.markdown("### 📋 Decision Ledger")
    st.markdown("All decisions extracted from meetings, sorted by date.")
    
    decisions = loader.graph.get_all_decisions()
    
    if not decisions:
        st.info("No decisions found in the knowledge graph.")
        return
    
    # Filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("Search decisions:", placeholder="e.g., Stripe, mobile, pricing")
    with col2:
        sort_order = st.selectbox("Sort by:", ["Newest first", "Oldest first"])
    
    # Filter and sort
    filtered = decisions
    if search:
        filtered = [d for d in filtered if search.lower() in d.what.lower() 
                    or search.lower() in (d.why or '').lower()]
    
    if sort_order == "Newest first":
        filtered = sorted(filtered, key=lambda d: d.date or '', reverse=True)
    else:
        filtered = sorted(filtered, key=lambda d: d.date or '')
    
    st.markdown(f"**{len(filtered)} decisions found**")
    
    # Display decisions
    for decision in filtered:
        st.markdown(f"""
        <div class='decision-card'>
            <strong>📌 {decision.what}</strong><br/>
            <em>Reasoning:</em> {decision.why or 'Not specified'}<br/>
            <small>
                👤 {decision.who or 'Unknown'} | 
                📅 {decision.date or 'Unknown'} | 
                📋 {decision.meeting_id or 'Unknown meeting'}
            </small>
        </div>
        """, unsafe_allow_html=True)


def render_actions_tab(loader):
    """Render the Action Items tab."""
    st.markdown("### ✅ Action Items")
    st.markdown("Track action items across all meetings.")
    
    # Get all action items
    actions = loader.graph.get_all_action_items()
    
    if not actions:
        st.info("No action items found in the knowledge graph.")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        assignee_filter = st.text_input("Filter by assignee:", placeholder="e.g., Bob")
    with col2:
        status_filter = st.selectbox("Status:", ["All", "pending", "completed", "in_progress"])
    with col3:
        sort_by = st.selectbox("Sort by:", ["Date", "Assignee"])
    
    # Apply filters
    filtered = actions
    if assignee_filter:
        filtered = [a for a in filtered if assignee_filter.lower() in (a.assignee or '').lower()]
    if status_filter != "All":
        filtered = [a for a in filtered if a.status.value == status_filter]
    
    # Sort
    if sort_by == "Date":
        filtered = sorted(filtered, key=lambda a: a.due_date or '', reverse=True)
    else:
        filtered = sorted(filtered, key=lambda a: a.assignee or '')
    
    st.markdown(f"**{len(filtered)} action items found**")
    
    # Display actions
    for action in filtered:
        status = action.status.value if action.status else 'pending'
        status_emoji = "✅" if status == "completed" else "⏳" if status == "in_progress" else "📋"
        
        st.markdown(f"""
        <div class='action-card'>
            <strong>{status_emoji} {action.task}</strong><br/>
            <em>Context:</em> {action.context or 'No context provided'}<br/>
            <small>
                👤 {action.assignee or 'Unassigned'} | 
                📅 Due: {action.due_date or 'Unknown'} |
                Status: {status}
            </small>
        </div>
        """, unsafe_allow_html=True)


def render_meetings_tab(loader):
    """Render the Meeting History tab."""
    st.markdown("### 📅 Meeting History")
    st.markdown("Browse all meetings and their extracted content.")
    
    all_meetings = loader.graph.get_all_meetings()
    
    if not all_meetings:
        st.info("No meetings loaded.")
        return
    
    # Meeting selector
    meeting_options = {f"{m.title} ({m.date})": m.id for m in all_meetings}
    selected_title = st.selectbox("Select a meeting:", list(meeting_options.keys()))
    
    if selected_title:
        meeting_id = meeting_options[selected_title]
        meeting = next((m for m in all_meetings if m.id == meeting_id), None)
        
        if meeting:
            st.markdown(f"## {meeting.title}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Date:** {meeting.date or 'Unknown'}")
            with col2:
                st.markdown(f"**Duration:** {meeting.duration_minutes or 'Unknown'} minutes")
            
            st.markdown(f"**Participants:** {', '.join(meeting.participants) if meeting.participants else 'Unknown'}")
            
            # Get related entities
            decisions = loader.graph.get_decisions_for_meeting(meeting_id)
            actions = loader.graph.get_action_items_for_meeting(meeting_id)
            blockers = loader.graph.get_blockers_for_meeting(meeting_id)
            
            # Decisions
            if decisions:
                st.markdown(f"### 📌 Decisions ({len(decisions)})")
                for d in decisions:
                    st.markdown(f"""
                    <div class='decision-card'>
                        <strong>{d.what}</strong><br/>
                        <em>Reasoning:</em> {d.why or 'Not specified'}<br/>
                        <small>👤 Decided by: {d.who or 'Unknown'}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Action Items
            if actions:
                st.markdown(f"### ✅ Action Items ({len(actions)})")
                for a in actions:
                    st.markdown(f"""
                    <div class='action-card'>
                        <strong>{a.task}</strong><br/>
                        <small>👤 Assigned to: {a.assignee or 'Unassigned'}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Blockers
            if blockers:
                st.markdown(f"### 🚧 Blockers ({len(blockers)})")
                for b in blockers:
                    severity = b.severity or 'medium'
                    severity_emoji = "🔴" if severity == 'high' else "🟡" if severity == 'medium' else "🟢"
                    st.markdown(f"""
                    <div class='blocker-card'>
                        <strong>{severity_emoji} {b.description}</strong><br/>
                        <small>Severity: {severity} | Status: {b.status or 'Unknown'}</small>
                    </div>
                    """, unsafe_allow_html=True)


def render_blockers_tab(loader):
    """Render the Blockers tab."""
    st.markdown("### 🚧 Blockers")
    st.markdown("Track impediments and blockers across all meetings.")
    
    blockers = loader.graph.get_all_blockers()
    
    if not blockers:
        st.info("No blockers found in the knowledge graph.")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status:", ["All", "open", "resolved"], key="blocker_status")
    with col2:
        severity_filter = st.selectbox("Severity:", ["All", "high", "medium", "low"])
    
    # Apply filters
    filtered = blockers
    if status_filter != "All":
        filtered = [b for b in filtered if b.status == status_filter]
    if severity_filter != "All":
        filtered = [b for b in filtered if b.severity == severity_filter]
    
    st.markdown(f"**{len(filtered)} blockers found**")
    
    # Display blockers
    for blocker in filtered:
        severity = blocker.severity or 'medium'
        severity_emoji = "🔴" if severity == 'high' else "🟡" if severity == 'medium' else "🟢"
        status = blocker.status or 'open'
        status_emoji = "✅" if status == "resolved" else "⏳"
        
        st.markdown(f"""
        <div class='blocker-card'>
            <strong>{severity_emoji} {blocker.description}</strong><br/>
            <small>
                👤 Affects: {blocker.owner or 'Unknown'} | 
                📅 {blocker.raised_date or 'Unknown'} |
                {status_emoji} {status}
            </small>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Header
    st.markdown("<h1 class='main-header'>🕐 AMPM</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>AI Meeting Product Manager - From AM to PM, Never Miss a Decision</p>", unsafe_allow_html=True)
    
    # Initialize AMPM
    loader, engine, error = initialize_ampm()
    
    if error:
        st.error(f"Failed to initialize AMPM: {error}")
        
        # Show reload button
        if st.button("🔄 Clear Cache and Retry"):
            st.cache_resource.clear()
            st.rerun()
        
        st.markdown("""
        ### Setup Instructions
        
        1. Make sure you have an OpenAI API key set in `.env`:
           ```
           OPENAI_API_KEY=sk-...
           ```
        
        2. Make sure you have meeting files in the `data/samples/` directory
        
        3. Install dependencies:
           ```bash
           pip install -r requirements.txt
           ```
        
        4. Click "Clear Cache and Retry" above after fixing any issues
        """)
        return
    
    # Render sidebar
    render_sidebar(loader)
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Ask Questions",
        "📋 Decision Ledger", 
        "✅ Action Items",
        "📅 Meeting History",
        "🚧 Blockers"
    ])
    
    with tab1:
        render_ask_tab(engine)
    
    with tab2:
        render_decisions_tab(loader)
    
    with tab3:
        render_actions_tab(loader)
    
    with tab4:
        render_meetings_tab(loader)
    
    with tab5:
        render_blockers_tab(loader)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<center><small>AMPM - AI Meeting Product Manager | Built with Streamlit, NetworkX, and OpenAI</small></center>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
