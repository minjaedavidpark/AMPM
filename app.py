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


def get_source_files_hash(data_dir: str) -> str:
    """Get a hash of all source files to detect changes."""
    import hashlib
    from pathlib import Path
    
    hasher = hashlib.md5()
    data_path = Path(data_dir)
    
    if not data_path.exists():
        return ""
    
    # Get all JSON files sorted by name
    for file_path in sorted(data_path.glob("*.json")):
        # Include filename and modification time
        stat = file_path.stat()
        hasher.update(f"{file_path.name}:{stat.st_mtime}:{stat.st_size}".encode())
    
    return hasher.hexdigest()


def load_or_build_knowledge_graph(data_dir: str = "data/samples", cache_dir: str = ".ampm_cache", use_backboard: bool = True):
    """
    Load knowledge graph from cache or build from source files.

    Args:
        data_dir: Directory containing meeting JSON files
        cache_dir: Directory for local cache
        use_backboard: Whether to use Backboard API for persistent memory

    Returns:
        Tuple of (loader, was_cached, error)
    """
    from pathlib import Path
    import json

    cache_path = Path(cache_dir)
    graph_cache = cache_path / "graph.json"
    embeddings_cache = cache_path / "embeddings.json"
    metadata_cache = cache_path / "metadata.json"

    # Calculate hash of source files
    source_hash = get_source_files_hash(data_dir)

    # Check if cache is valid
    cache_valid = False
    if metadata_cache.exists():
        try:
            with open(metadata_cache, 'r') as f:
                metadata = json.load(f)
            if metadata.get("source_hash") == source_hash:
                cache_valid = True
                print("Cache is valid (source files unchanged)")
        except Exception:
            pass

    # Try to load from cache
    if cache_valid and graph_cache.exists() and embeddings_cache.exists():
        print("Loading from cache...")
        try:
            from ampm.core.graph import MeetingGraph
            from ampm.core.embeddings import EmbeddingStore

            graph = MeetingGraph()
            # Use Backboard for embeddings if available
            embeddings = EmbeddingStore(
                use_backboard=use_backboard,
                config_dir=str(cache_path / "backboard"),
                persist=True
            )

            if graph.load(str(graph_cache)) and embeddings.load(str(embeddings_cache)):
                # Create a simple loader wrapper
                loader = MeetingLoader(graph, embeddings)
                return loader, True, None
            else:
                print("Cache load failed, rebuilding...")
        except Exception as e:
            print(f"Cache load error: {e}, rebuilding...")

    # Build from source
    print("Building knowledge graph from source files...")

    from ampm.core.graph import MeetingGraph
    from ampm.core.embeddings import EmbeddingStore

    graph = MeetingGraph()
    embeddings = EmbeddingStore(
        use_backboard=use_backboard,
        config_dir=str(cache_path / "backboard"),
        persist=True
    )
    loader = MeetingLoader(graph, embeddings)

    meetings = loader.load_directory(data_dir)
    if not meetings:
        return None, False, f"No meetings found in {data_dir}"

    print(f"Loaded {len(meetings)} meetings")
    print(f"Graph stats: {loader.graph.stats}")

    # Save to cache
    try:
        cache_path.mkdir(parents=True, exist_ok=True)

        loader.graph.save(str(graph_cache))
        loader.embeddings.save(str(embeddings_cache))

        # Save metadata
        with open(metadata_cache, 'w') as f:
            json.dump({
                "source_hash": source_hash,
                "data_dir": data_dir,
                "stats": loader.graph.stats,
                "use_backboard": use_backboard
            }, f, indent=2)

        print("Cache saved successfully")
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

    return loader, False, None


@st.cache_resource(show_spinner="Loading meetings and building knowledge graph...")
def initialize_ampm(data_dir: str = "data/samples", use_backboard: bool = True):
    """
    Initialize AMPM by loading meetings and building knowledge graph.

    This is cached to avoid reprocessing on every page load.
    Uses persistent file cache to avoid rebuilding on app restart.

    Args:
        data_dir: Directory containing meeting JSON files
        use_backboard: Whether to use Backboard API for persistent memory
    """
    # Check for API keys
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_cerebras = bool(os.getenv("CEREBRAS_API_KEY"))
    has_backboard = bool(os.getenv("BACKBOARD_API_KEY"))

    if not has_openai and not has_cerebras:
        return None, None, "Missing API keys. Set OPENAI_API_KEY or CEREBRAS_API_KEY in .env"

    try:
        # Load or build the knowledge graph
        loader, was_cached, error = load_or_build_knowledge_graph(
            data_dir,
            use_backboard=use_backboard and has_backboard
        )

        if error:
            return None, None, error

        if was_cached:
            print("Using cached knowledge graph")
        else:
            print("Built new knowledge graph")

        # Create query engine
        engine = QueryEngine(loader.graph, loader.embeddings)

        # Store Backboard status in engine for UI access
        engine._use_backboard = use_backboard and has_backboard
        engine._has_backboard_thread = bool(
            loader.embeddings.thread_id if hasattr(loader.embeddings, 'thread_id') else False
        )

        return loader, engine, None

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"
        print(f"Error: {error_msg}")
        return None, None, error_msg


def render_sidebar(loader, engine=None):
    """Render the sidebar with stats and info."""
    st.sidebar.markdown("## 🕐 AMPM")
    st.sidebar.markdown("*AI Meeting Product Manager*")

    # Show backend status
    has_backboard = bool(os.getenv("BACKBOARD_API_KEY"))
    has_cerebras = bool(os.getenv("CEREBRAS_API_KEY"))

    if engine:
        use_backboard = getattr(engine, '_use_backboard', False)
        has_thread = getattr(engine, '_has_backboard_thread', False)

        if use_backboard and has_thread:
            st.sidebar.success("🔗 Backboard Connected (Persistent Memory)")
        elif has_backboard:
            st.sidebar.warning("⚠️ Backboard Available (Not Connected)")
        else:
            st.sidebar.info("💾 Local Mode (No Persistence)")

        if has_cerebras:
            st.sidebar.caption("⚡ Using Cerebras for fast LLM")

    st.sidebar.markdown("---")

    # Cache control buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Reload"):
            st.cache_resource.clear()
            st.rerun()
    with col2:
        if st.button("🗑️ Clear Cache"):
            # Clear persistent cache
            import shutil
            from pathlib import Path
            cache_dir = Path(".ampm_cache")
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                st.sidebar.success("Cache cleared!")
            st.cache_resource.clear()
            st.rerun()

    st.sidebar.markdown("---")
    
    # Stats
    if loader and loader.graph:
        stats = loader.graph.stats
        
        st.sidebar.markdown("### 📊 Knowledge Graph Stats")
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            st.metric("Meetings", stats.get('meetings', 0))
            st.metric("Decisions", stats.get('decisions', 0))
            st.metric("Topics", stats.get('topics', 0))
        
        with col2:
            st.metric("Actions", stats.get('action_items', 0))
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
    """Render the Ask Questions tab with voice support."""
    st.markdown("### 🔍 Ask a Question")
    st.markdown("Ask about decisions, action items, blockers, or any meeting context.")

    # Check API keys
    has_elevenlabs = bool(os.getenv("ELEVENLABS_API_KEY"))
    use_backboard = getattr(engine, '_use_backboard', False)
    has_thread = getattr(engine, '_has_backboard_thread', False)

    # Query mode selection
    col1, col2 = st.columns([2, 1])
    with col1:
        input_mode = st.radio(
            "Input method:",
            ["⌨️ Type", "🎤 Voice"],
            horizontal=True,
            key="input_mode"
        )
    with col2:
        # Fast mode uses Backboard's integrated RAG
        fast_mode = st.checkbox(
            "⚡ Fast Mode",
            value=use_backboard and has_thread,
            disabled=not (use_backboard and has_thread),
            help="Use Backboard's memory-augmented RAG for faster responses" if use_backboard else "Enable Backboard to use Fast Mode"
        )
    
    question = None
    
    if input_mode == "🎤 Voice":
        # Voice input mode
        audio_input = st.audio_input("Click to record your question", key="voice_input")
        
        if audio_input:
            st.audio(audio_input, format="audio/wav")
            
            if st.button("🎯 Transcribe & Ask", type="primary"):
                with st.spinner("Transcribing audio..."):
                    try:
                        from openai import OpenAI
                        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                        
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                            f.write(audio_input.getvalue())
                            temp_path = f.name
                        
                        with open(temp_path, "rb") as audio_file:
                            transcript = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                language="en"
                            )
                        
                        os.unlink(temp_path)
                        question = transcript.text
                        st.markdown(f"**Transcribed:** *{question}*")
                        
                    except Exception as e:
                        st.error(f"Transcription failed: {e}")
                        return
    else:
        # Text input mode
        question = st.text_input(
            "Your question:",
            placeholder="e.g., Why did we choose Stripe for payments?",
            key="question_input"
        )
        
        if st.button("Ask AMPM", type="primary"):
            if not question:
                st.warning("Please enter a question.")
                return
        else:
            question = None  # Don't process unless button clicked
    
    # Voice response option
    col1, col2 = st.columns([3, 1])
    with col2:
        speak_response = st.checkbox(
            "🔊 Voice response",
            value=False,
            disabled=not has_elevenlabs,
            help="Enable ElevenLabs to hear the answer" if has_elevenlabs else "Add ELEVENLABS_API_KEY to .env"
        )
    
    # Process the question
    if question:
        mode_label = "Backboard RAG" if fast_mode else "Graph + LLM"
        with st.spinner(f"Searching meeting knowledge ({mode_label})..."):
            start_time = time.time()
            if fast_mode:
                result = engine.query_fast(question)
            else:
                result = engine.query(question)
            elapsed = time.time() - start_time

        # Show timing with mode indicator
        mode_badge = "⚡" if fast_mode else "🔍"
        st.markdown(f"<span class='timing-badge'>{mode_badge} Answered in {elapsed:.2f}s</span>", unsafe_allow_html=True)
        
        # Show answer
        st.markdown("### Answer")
        st.markdown(result.answer)
        
        # Generate voice response if enabled
        if speak_response and has_elevenlabs:
            with st.spinner("Generating voice response..."):
                try:
                    from elevenlabs import ElevenLabs
                    
                    elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
                    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
                    
                    audio_generator = elevenlabs.text_to_speech.convert(
                        text=result.answer,
                        voice_id=voice_id,
                        model_id="eleven_turbo_v2_5",
                        output_format="mp3_44100_128"
                    )
                    
                    audio_bytes = b"".join(audio_generator)
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                    
                except Exception as e:
                    st.error(f"Voice generation failed: {e}")
        
        # Show confidence
        confidence = result.confidence
        confidence_color = "green" if confidence > 0.7 else "orange" if confidence > 0.4 else "red"
        st.markdown(f"**Confidence:** :{confidence_color}[{confidence:.0%}]")
        
        # Show sources
        if result.sources:
            st.markdown("### 📚 Sources")
            for source in result.sources[:5]:
                meeting_title = source.get('meeting_title', source.get('meeting_id', 'Unknown'))
                date = source.get('date', 'Unknown date')
                content_type = source.get('type', 'content')
                content = source.get('content', source.get('text', ''))[:150]
                st.markdown(f"""
                <div class='source-card'>
                    <strong>{meeting_title}</strong> ({date})<br/>
                    <em>{content_type}</em>: {content}...
                </div>
                """, unsafe_allow_html=True)



def render_decisions_tab(loader):
    """Render the Decision Ledger tab."""
    st.markdown("### 📋 Decision Ledger")
    st.markdown("All decisions extracted from meetings, sorted by date.")
    
    # Access decisions from the internal dict
    decisions = list(loader.graph._decisions.values())
    
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
        filtered = [d for d in filtered if search.lower() in d.content.lower() 
                    or search.lower() in (d.rationale or '').lower()]
    
    if sort_order == "Newest first":
        filtered = sorted(filtered, key=lambda d: d.timestamp, reverse=True)
    else:
        filtered = sorted(filtered, key=lambda d: d.timestamp)
    
    st.markdown(f"**{len(filtered)} decisions found**")
    
    # Display decisions
    for decision in filtered:
        # Get meeting title if available
        meeting = loader.graph.get_meeting(decision.meeting_id) if decision.meeting_id else None
        meeting_title = meeting.title if meeting else decision.meeting_id or 'Unknown meeting'
        
        # Get person name if available
        person = loader.graph.get_person(decision.made_by) if decision.made_by else None
        made_by = person.name if person else decision.made_by or 'Unknown'
        
        date_str = decision.timestamp.strftime('%Y-%m-%d') if decision.timestamp else 'Unknown'
        
        st.markdown(f"""
        <div class='decision-card'>
            <strong>📌 {decision.content}</strong><br/>
            <em>Reasoning:</em> {decision.rationale or 'Not specified'}<br/>
            <small>
                👤 {made_by} | 
                📅 {date_str} | 
                📋 {meeting_title}
            </small>
        </div>
        """, unsafe_allow_html=True)


def render_actions_tab(loader):
    """Render the Action Items tab."""
    st.markdown("### ✅ Action Items")
    st.markdown("Track action items across all meetings.")
    
    # Access action items from the internal dict
    actions = list(loader.graph._action_items.values())
    
    if not actions:
        st.info("No action items found in the knowledge graph.")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        assignee_filter = st.text_input("Filter by assignee:", placeholder="e.g., Bob")
    with col2:
        status_options = ["All", "pending", "in_progress", "completed", "blocked"]
        status_filter = st.selectbox("Status:", status_options)
    with col3:
        sort_by = st.selectbox("Sort by:", ["Date", "Assignee"])
    
    # Apply filters
    filtered = actions
    if assignee_filter:
        filtered = [a for a in filtered 
                    if assignee_filter.lower() in (a.assigned_to or '').lower()]
    if status_filter != "All":
        filtered = [a for a in filtered if a.status.value == status_filter]
    
    # Sort
    if sort_by == "Date":
        filtered = sorted(filtered, key=lambda a: a.created_at, reverse=True)
    else:
        filtered = sorted(filtered, key=lambda a: a.assigned_to or '')
    
    st.markdown(f"**{len(filtered)} action items found**")
    
    # Display actions
    for action in filtered:
        status = action.status.value if action.status else 'pending'
        status_emoji = "✅" if status == "completed" else "⏳" if status == "in_progress" else "🔴" if status == "blocked" else "📋"
        
        # Get assignee name
        person = loader.graph.get_person(action.assigned_to) if action.assigned_to else None
        assignee = person.name if person else action.assigned_to or 'Unassigned'
        
        due_date = action.due_date.strftime('%Y-%m-%d') if action.due_date else 'No due date'
        
        st.markdown(f"""
        <div class='action-card'>
            <strong>{status_emoji} {action.task}</strong><br/>
            <small>
                👤 {assignee} | 
                📅 Due: {due_date} |
                Status: {status}
            </small>
        </div>
        """, unsafe_allow_html=True)


def render_meetings_tab(loader):
    """Render the Meeting History tab."""
    st.markdown("### 📅 Meeting History")
    st.markdown("Browse all meetings and their extracted content.")
    
    # Access meetings from the internal dict
    all_meetings = list(loader.graph._meetings.values())
    
    if not all_meetings:
        st.info("No meetings loaded.")
        return
    
    # Sort by date
    all_meetings = sorted(all_meetings, key=lambda m: m.date, reverse=True)
    
    # Meeting selector
    meeting_options = {f"{m.title} ({m.date.strftime('%Y-%m-%d') if m.date else 'Unknown'})": m.id 
                       for m in all_meetings}
    selected_title = st.selectbox("Select a meeting:", list(meeting_options.keys()))
    
    if selected_title:
        meeting_id = meeting_options[selected_title]
        meeting = loader.graph.get_meeting(meeting_id)
        
        if meeting:
            st.markdown(f"## {meeting.title}")
            
            col1, col2 = st.columns(2)
            with col1:
                date_str = meeting.date.strftime('%Y-%m-%d') if meeting.date else 'Unknown'
                st.markdown(f"**Date:** {date_str}")
            with col2:
                st.markdown(f"**Duration:** {meeting.duration_minutes or 'Unknown'} minutes")
            
            # Get attendee names
            attendee_names = []
            for person_id in meeting.attendees:
                person = loader.graph.get_person(person_id)
                attendee_names.append(person.name if person else person_id)
            st.markdown(f"**Participants:** {', '.join(attendee_names) if attendee_names else 'Unknown'}")
            
            if meeting.summary:
                st.markdown(f"**Summary:** {meeting.summary}")
            
            # Get related entities
            decisions = loader.graph.get_decisions_by_meeting(meeting_id)
            
            # Decisions
            if decisions:
                st.markdown(f"### 📌 Decisions ({len(decisions)})")
                for d in decisions:
                    person = loader.graph.get_person(d.made_by) if d.made_by else None
                    made_by = person.name if person else d.made_by or 'Unknown'
                    st.markdown(f"""
                    <div class='decision-card'>
                        <strong>{d.content}</strong><br/>
                        <em>Reasoning:</em> {d.rationale or 'Not specified'}<br/>
                        <small>👤 Decided by: {made_by}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Action Items - get from meeting's action_items list
            action_items = []
            for action_id in meeting.action_items:
                action = loader.graph._action_items.get(action_id)
                if action:
                    action_items.append(action)
            
            if action_items:
                st.markdown(f"### ✅ Action Items ({len(action_items)})")
                for a in action_items:
                    person = loader.graph.get_person(a.assigned_to) if a.assigned_to else None
                    assignee = person.name if person else a.assigned_to or 'Unassigned'
                    st.markdown(f"""
                    <div class='action-card'>
                        <strong>{a.task}</strong><br/>
                        <small>👤 Assigned to: {assignee}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Blockers - get from meeting's blockers list
            blockers = []
            for blocker_id in meeting.blockers:
                blocker = loader.graph._blockers.get(blocker_id)
                if blocker:
                    blockers.append(blocker)
            
            if blockers:
                st.markdown(f"### 🚧 Blockers ({len(blockers)})")
                for b in blockers:
                    status = "✅ Resolved" if b.resolved else "⏳ Open"
                    st.markdown(f"""
                    <div class='blocker-card'>
                        <strong>{b.description}</strong><br/>
                        <small>Status: {status}</small>
                    </div>
                    """, unsafe_allow_html=True)


def render_blockers_tab(loader):
    """Render the Blockers tab."""
    st.markdown("### 🚧 Blockers")
    st.markdown("Track impediments and blockers across all meetings.")
    
    # Access blockers from the internal dict
    blockers = list(loader.graph._blockers.values())
    
    if not blockers:
        st.info("No blockers found in the knowledge graph.")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status:", ["All", "open", "resolved"], key="blocker_status")
    
    # Apply filters
    filtered = blockers
    if status_filter == "open":
        filtered = [b for b in filtered if not b.resolved]
    elif status_filter == "resolved":
        filtered = [b for b in filtered if b.resolved]
    
    st.markdown(f"**{len(filtered)} blockers found**")
    
    # Display blockers
    for blocker in filtered:
        status = "✅ Resolved" if blocker.resolved else "⏳ Open"
        status_emoji = "✅" if blocker.resolved else "🔴"
        
        # Get reporter name
        person = loader.graph.get_person(blocker.reported_by) if blocker.reported_by else None
        reported_by = person.name if person else blocker.reported_by or 'Unknown'
        
        date_str = blocker.created_at.strftime('%Y-%m-%d') if blocker.created_at else 'Unknown'
        
        st.markdown(f"""
        <div class='blocker-card'>
            <strong>{status_emoji} {blocker.description}</strong><br/>
            <em>Impact:</em> {blocker.impact or 'Not specified'}<br/>
            <small>
                👤 Reported by: {reported_by} | 
                📅 {date_str} |
                {status}
            </small>
        </div>
        """, unsafe_allow_html=True)


def render_add_info_tab(loader):
    """Render the Add Info tab for real-time knowledge graph updates."""
    st.markdown("### ➕ Add Information in Real-Time")
    st.markdown("Add decisions, actions, blockers, or notes during your meeting. Changes are saved automatically.")
    
    # Create or get live meeting
    live_meeting = loader.get_or_create_live_meeting()
    
    st.info(f"📍 **Live Session:** {live_meeting.title}")
    
    # Sub-tabs for different entry types
    add_type = st.radio(
        "What would you like to add?",
        ["📋 Decision", "✅ Action Item", "🚧 Blocker", "👤 Person", "📝 Note"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Get existing people for dropdowns
    people = list(loader.graph._people.values())
    people_options = ["(none)"] + [p.name for p in people]
    
    if add_type == "📋 Decision":
        st.markdown("#### Record a Decision")
        
        decision_content = st.text_area(
            "Decision:",
            placeholder="e.g., We will use Stripe for payment processing",
            key="new_decision"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            decision_topic = st.text_input(
                "Topic:",
                placeholder="e.g., payments, security, architecture",
                key="decision_topic"
            )
        with col2:
            made_by = st.selectbox("Made by:", people_options, key="decision_made_by")
        
        decision_rationale = st.text_area(
            "Rationale (optional):",
            placeholder="Why was this decision made?",
            key="decision_rationale"
        )
        
        if st.button("➕ Add Decision", type="primary", key="add_decision_btn"):
            if decision_content:
                person_id = None
                if made_by != "(none)":
                    person_id = made_by.lower().replace(" ", "_")
                
                decision = loader.add_decision_realtime(
                    content=decision_content,
                    rationale=decision_rationale if decision_rationale else None,
                    topic=decision_topic if decision_topic else None,
                    made_by=person_id
                )
                st.success(f"✓ Decision added! ID: {decision.id}")
                st.rerun()
            else:
                st.warning("Please enter a decision.")
    
    elif add_type == "✅ Action Item":
        st.markdown("#### Record an Action Item")
        
        action_task = st.text_area(
            "Task:",
            placeholder="e.g., Create API documentation for the payment integration",
            key="new_action"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            assigned_to = st.selectbox("Assigned to:", people_options, key="action_assigned")
        with col2:
            due_date = st.date_input("Due date (optional):", value=None, key="action_due")
        
        # Get decisions for linking
        decisions = list(loader.graph._decisions.values())
        decision_options = ["(none)"] + [f"{d.content[:50]}..." for d in decisions[-10:]]  # Last 10
        related_decision = st.selectbox("Related to decision:", decision_options, key="action_decision")
        
        if st.button("➕ Add Action Item", type="primary", key="add_action_btn"):
            if action_task:
                person_id = None
                if assigned_to != "(none)":
                    person_id = assigned_to.lower().replace(" ", "_")
                
                decision_id = None
                if related_decision != "(none)":
                    idx = decision_options.index(related_decision) - 1
                    if idx >= 0:
                        decision_id = decisions[-(10-idx) if len(decisions) > 10 else idx].id
                
                from datetime import datetime
                due_dt = datetime.combine(due_date, datetime.min.time()) if due_date else None
                
                action = loader.add_action_realtime(
                    task=action_task,
                    assigned_to=person_id,
                    due_date=due_dt,
                    decision_id=decision_id
                )
                st.success(f"✓ Action item added! ID: {action.id}")
                st.rerun()
            else:
                st.warning("Please enter a task description.")
    
    elif add_type == "🚧 Blocker":
        st.markdown("#### Report a Blocker")
        
        blocker_desc = st.text_area(
            "Blocker description:",
            placeholder="e.g., Waiting for security team approval on the API design",
            key="new_blocker"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            reported_by = st.selectbox("Reported by:", people_options, key="blocker_reporter")
        
        blocker_impact = st.text_input(
            "Impact (optional):",
            placeholder="e.g., Blocks payment feature launch",
            key="blocker_impact"
        )
        
        if st.button("➕ Add Blocker", type="primary", key="add_blocker_btn"):
            if blocker_desc:
                person_id = None
                if reported_by != "(none)":
                    person_id = reported_by.lower().replace(" ", "_")
                
                blocker = loader.add_blocker_realtime(
                    description=blocker_desc,
                    reported_by=person_id,
                    impact=blocker_impact if blocker_impact else None
                )
                st.success(f"✓ Blocker added! ID: {blocker.id}")
                st.rerun()
            else:
                st.warning("Please describe the blocker.")
    
    elif add_type == "👤 Person":
        st.markdown("#### Add a Team Member")
        
        person_name = st.text_input(
            "Name:",
            placeholder="e.g., Sarah Chen",
            key="new_person_name"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            person_role = st.text_input(
                "Role:",
                placeholder="e.g., Engineering Manager",
                key="person_role"
            )
        with col2:
            person_email = st.text_input(
                "Email (optional):",
                placeholder="e.g., sarah@company.com",
                key="person_email"
            )
        
        if st.button("➕ Add Person", type="primary", key="add_person_btn"):
            if person_name:
                person = loader.add_person_realtime(
                    name=person_name,
                    role=person_role if person_role else None,
                    email=person_email if person_email else None
                )
                st.success(f"✓ Person added: {person.name}")
                st.rerun()
            else:
                st.warning("Please enter a name.")
    
    elif add_type == "📝 Note":
        st.markdown("#### Add a Note")
        
        note_content = st.text_area(
            "Note:",
            placeholder="Any observation, insight, or discussion point...",
            key="new_note"
        )
        
        note_category = st.selectbox(
            "Category:",
            ["note", "insight", "question", "followup", "context"],
            key="note_category"
        )
        
        if st.button("➕ Add Note", type="primary", key="add_note_btn"):
            if note_content:
                note_id = loader.add_note_realtime(
                    content=note_content,
                    category=note_category
                )
                st.success(f"✓ Note added! ID: {note_id}")
                st.rerun()
            else:
                st.warning("Please enter a note.")
    
    # Show recent additions
    st.markdown("---")
    st.markdown("#### 📊 Live Session Summary")
    
    col1, col2, col3 = st.columns(3)
    
    # Count items from live meeting
    live_decisions = [d for d in loader.graph._decisions.values() if d.meeting_id == "live_meeting"]
    live_actions = [a for a in loader.graph._action_items.values() if a.meeting_id == "live_meeting"]
    live_blockers = [b for b in loader.graph._blockers.values() if b.meeting_id == "live_meeting"]
    
    with col1:
        st.metric("Decisions", len(live_decisions))
    with col2:
        st.metric("Action Items", len(live_actions))
    with col3:
        st.metric("Blockers", len(live_blockers))
    
    # Show recent items
    if live_decisions or live_actions or live_blockers:
        with st.expander("View items added this session"):
            if live_decisions:
                st.markdown("**Decisions:**")
                for d in live_decisions[-5:]:
                    st.markdown(f"- {d.content}")
            if live_actions:
                st.markdown("**Actions:**")
                for a in live_actions[-5:]:
                    st.markdown(f"- {a.task}")
            if live_blockers:
                st.markdown("**Blockers:**")
                for b in live_blockers[-5:]:
                    st.markdown(f"- {b.description}")


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
        
        1. Make sure you have API keys set in `.env`:
           ```
           OPENAI_API_KEY=sk-...
           CEREBRAS_API_KEY=...
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
    render_sidebar(loader, engine)
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔍 Ask Questions",
        "➕ Add Info",
        "📋 Decision Ledger", 
        "✅ Action Items",
        "📅 Meeting History",
        "🚧 Blockers"
    ])
    
    with tab1:
        render_ask_tab(engine)
    
    with tab2:
        render_add_info_tab(loader)
    
    with tab3:
        render_decisions_tab(loader)
    
    with tab4:
        render_actions_tab(loader)
    
    with tab5:
        render_meetings_tab(loader)
    
    with tab6:
        render_blockers_tab(loader)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<center><small>AMPM - AI Meeting Product Manager | Built with Streamlit, NetworkX, and OpenAI</small></center>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
