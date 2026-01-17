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
    page_title="AMPM",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, minimal CSS - Light theme
st.markdown("""
<style>
    /* Light theme base */
    .stApp {
        background-color: #ffffff;
    }

    .main-header {
        font-size: 1.75rem;
        font-weight: 600;
        margin-bottom: 0;
        letter-spacing: -0.02em;
        color: #1d1d1f;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #86868b;
        margin-top: 0;
        font-weight: 400;
    }
    .answer-text {
        font-size: 1rem;
        line-height: 1.6;
        color: #1d1d1f;
    }

    /* Even tab spacing */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        justify-content: space-between;
        border-bottom: 1px solid #e5e5e7;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        padding: 12px 24px;
        font-size: 0.9rem;
        font-weight: 500;
        color: #86868b;
        border-radius: 0;
        border-bottom: 2px solid transparent;
        justify-content: center;
    }
    .stTabs [aria-selected="true"] {
        color: #1d1d1f;
        border-bottom: 2px solid #1d1d1f;
        background: transparent;
    }

    /* Cards */
    .source-card {
        background: #f5f5f7;
        padding: 14px 18px;
        border-radius: 10px;
        margin: 10px 0;
        font-size: 0.9rem;
        border: 1px solid #e5e5e7;
    }
    .source-card strong {
        color: #1d1d1f;
        display: block;
        margin-bottom: 4px;
    }
    .source-card .summary {
        color: #424245;
        font-size: 0.85rem;
        margin: 6px 0;
    }
    .source-card a {
        color: #0066cc;
        font-size: 0.8rem;
        text-decoration: none;
    }
    .source-card a:hover {
        text-decoration: underline;
    }
    .decision-card, .action-card {
        background: #f5f5f7;
        padding: 14px 18px;
        border-radius: 10px;
        margin: 8px 0;
        border: 1px solid #e5e5e7;
    }
    .blocker-card {
        background: #fef2f2;
        padding: 14px 18px;
        border-radius: 10px;
        margin: 8px 0;
        border: 1px solid #fecaca;
    }
    .time-label {
        color: #86868b;
        font-size: 0.8rem;
        margin-top: 8px;
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background: #f5f5f7;
        padding: 14px;
        border-radius: 10px;
        border: 1px solid #e5e5e7;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        padding: 8px 20px;
    }
    .stButton > button[kind="primary"] {
        background: #1d1d1f;
        color: white;
    }

    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #e5e5e7;
        padding: 10px 14px;
    }
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 1px solid #e5e5e7;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #fafafa;
        border-right: 1px solid #e5e5e7;
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
    # Use fast_load=True to skip slow LLM entity extraction
    loader = MeetingLoader(graph, embeddings, fast_load=True)

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
def initialize_ampm(data_dir: str = "data/samples", use_backboard: bool = False):
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
    st.sidebar.markdown("## AMPM")
    st.sidebar.caption("Meeting Memory")

    st.sidebar.markdown("---")

    # Stats
    if loader and loader.graph:
        stats = loader.graph.stats

        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.sidebar.metric("Meetings", stats.get('meetings', 0))
            st.sidebar.metric("Decisions", stats.get('decisions', 0))
        with col2:
            st.sidebar.metric("Actions", stats.get('action_items', 0))
            st.sidebar.metric("People", stats.get('people', 0))

        st.sidebar.markdown("---")

    # Sample queries
    st.sidebar.markdown("**Try asking**")
    sample_queries = [
        "Why did we choose Stripe?",
        "What's blocking the payments launch?",
        "What decisions were made about mobile?",
        "What are Bob's action items?",
    ]
    for query in sample_queries:
        st.sidebar.markdown(f"_{query}_")

    st.sidebar.markdown("---")

    # Minimal controls
    if st.sidebar.button("Reload Data", use_container_width=True):
        import shutil
        from pathlib import Path
        cache_dir = Path(".ampm_cache")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        st.cache_resource.clear()
        st.rerun()


def render_ask_tab(engine: QueryEngine):
    """Render the Ask Questions tab."""

    # Input row with text field and buttons
    col_input, col_ask, col_audio = st.columns([8, 1, 1])

    with col_input:
        question = st.text_input(
            "Ask about your meetings",
            placeholder="Why did we choose Stripe for payments?",
            key="question_input",
            label_visibility="collapsed"
        )

    with col_ask:
        ask_clicked = st.button("Ask", type="primary", use_container_width=True)

    with col_audio:
        has_elevenlabs = bool(os.getenv("ELEVENLABS_API_KEY"))
        speak_response = st.button("🔊", disabled=not has_elevenlabs,
                                   help="Voice response" if has_elevenlabs else "Requires ElevenLabs API key",
                                   use_container_width=True)

    # Process the question
    if (ask_clicked or speak_response) and question:
        with st.spinner("Searching..."):
            start_time = time.time()
            result = engine.query(question)
            elapsed = time.time() - start_time

        # Show answer
        st.markdown(f"<div class='answer-text'>{result.answer}</div>", unsafe_allow_html=True)
        st.markdown(f"<p class='time-label'>{elapsed:.1f}s</p>", unsafe_allow_html=True)

        # Generate voice response if enabled
        if speak_response and has_elevenlabs:
            try:
                from elevenlabs import ElevenLabs
                elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
                voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
                audio_generator = elevenlabs_client.text_to_speech.convert(
                    text=result.answer, voice_id=voice_id,
                    model_id="eleven_turbo_v2_5", output_format="mp3_44100_128"
                )
                st.audio(b"".join(audio_generator), format="audio/mp3", autoplay=True)
            except Exception:
                pass

        # Only show sources if the answer is substantive (not "I don't know" type responses)
        answer_lower = result.answer.lower()
        no_info_phrases = ["don't have enough information", "not mentioned", "no mention",
                          "not addressed", "cannot find", "no information", "not found"]
        has_relevant_answer = not any(phrase in answer_lower for phrase in no_info_phrases)

        if result.sources and has_relevant_answer and result.confidence > 0.3:
            with st.expander("Sources", expanded=False):
                for source in result.sources[:3]:
                    meeting_title = source.get('meeting_title', source.get('meeting_id', ''))
                    if not meeting_title:
                        continue

                    # Format date nicely (remove time portion)
                    date = source.get('meeting_date', source.get('date', ''))
                    if date:
                        date = str(date).split(' ')[0]  # Remove time portion
                        if date == 'Unknown date':
                            date = ''

                    # Get meaningful summary - prefer decision/rationale over raw content
                    decision = source.get('decision_content', '')
                    rationale = source.get('rationale', '')
                    content = source.get('content', '')

                    # Pick best summary, skip if it duplicates the meeting title
                    summary = ''
                    for text in [decision, rationale, content]:
                        if not text or len(text) < 20:
                            continue
                        # Skip if text is just the meeting title or starts with it
                        if text == meeting_title:
                            continue
                        # Strip meeting title from beginning if present
                        if text.startswith(meeting_title):
                            text = text[len(meeting_title):].lstrip(' \n\t:.-')
                        if len(text) < 20:
                            continue
                        summary = text[:150].strip()
                        if len(text) > 150:
                            summary += '...'
                        break

                    # Build clean card
                    date_html = f'<span style="color:#86868b;font-size:0.85rem"> · {date}</span>' if date else ''
                    summary_html = f'<p style="color:#555;font-size:0.9rem;margin:8px 0 0 0">{summary}</p>' if summary else ''

                    st.markdown(
                        f'<div class="source-card"><strong>{meeting_title}</strong>{date_html}{summary_html}</div>',
                        unsafe_allow_html=True
                    )

    elif (ask_clicked or speak_response) and not question:
        st.info("Enter a question above.")



def render_decisions_tab(loader):
    """Render the Decision Ledger tab."""
    
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
            <strong>{decision.content}</strong><br/>
            <small>{decision.rationale or ''}</small><br/>
            <small style="color:#86868b">{made_by} · {date_str} · {meeting_title}</small>
        </div>
        """, unsafe_allow_html=True)


def render_actions_tab(loader):
    """Render the Action Items tab."""
    
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

        # Get assignee name
        person = loader.graph.get_person(action.assigned_to) if action.assigned_to else None
        assignee = person.name if person else action.assigned_to or 'Unassigned'

        due_date = action.due_date.strftime('%Y-%m-%d') if action.due_date else ''
        due_str = f" · Due {due_date}" if due_date else ""

        st.markdown(f"""
        <div class='action-card'>
            <strong>{action.task}</strong><br/>
            <small style="color:#86868b">{assignee}{due_str} · {status}</small>
        </div>
        """, unsafe_allow_html=True)


def render_meetings_tab(loader):
    """Render the Meeting History tab."""
    
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
                st.markdown(f"**Decisions** ({len(decisions)})")
                for d in decisions:
                    person = loader.graph.get_person(d.made_by) if d.made_by else None
                    made_by = person.name if person else d.made_by or ''
                    st.markdown(f"""
                    <div class='decision-card'>
                        <strong>{d.content}</strong><br/>
                        <small>{d.rationale or ''}</small>
                        <small style="color:#86868b">{made_by}</small>
                    </div>
                    """, unsafe_allow_html=True)

            # Action Items
            action_items = [loader.graph._action_items.get(aid) for aid in meeting.action_items]
            action_items = [a for a in action_items if a]

            if action_items:
                st.markdown(f"**Actions** ({len(action_items)})")
                for a in action_items:
                    person = loader.graph.get_person(a.assigned_to) if a.assigned_to else None
                    assignee = person.name if person else a.assigned_to or ''
                    st.markdown(f"""
                    <div class='action-card'>
                        <strong>{a.task}</strong><br/>
                        <small style="color:#86868b">{assignee}</small>
                    </div>
                    """, unsafe_allow_html=True)

            # Blockers
            blockers = [loader.graph._blockers.get(bid) for bid in meeting.blockers]
            blockers = [b for b in blockers if b]

            if blockers:
                st.markdown(f"**Blockers** ({len(blockers)})")
                for b in blockers:
                    status = "Resolved" if b.resolved else "Open"
                    st.markdown(f"""
                    <div class='blocker-card'>
                        <strong>{b.description}</strong><br/>
                        <small style="color:#86868b">{status}</small>
                    </div>
                    """, unsafe_allow_html=True)


def render_blockers_tab(loader):
    """Render the Blockers tab."""
    
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
        status = "Resolved" if blocker.resolved else "Open"

        # Get reporter name
        person = loader.graph.get_person(blocker.reported_by) if blocker.reported_by else None
        reported_by = person.name if person else blocker.reported_by or 'Unknown'

        date_str = blocker.created_at.strftime('%Y-%m-%d') if blocker.created_at else ''

        st.markdown(f"""
        <div class='blocker-card'>
            <strong>{blocker.description}</strong><br/>
            <small>{blocker.impact or ''}</small><br/>
            <small style="color:#86868b">{reported_by} · {date_str} · {status}</small>
        </div>
        """, unsafe_allow_html=True)


def render_add_info_tab(loader):
    """Render the Add Info tab for real-time knowledge graph updates."""

    # Create or get live meeting
    live_meeting = loader.get_or_create_live_meeting()

    # Sub-tabs for different entry types
    add_type = st.radio(
        "Add to meeting",
        ["Decision", "Action", "Blocker", "Person", "Note"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Get existing people for dropdowns
    people = list(loader.graph._people.values())
    people_options = ["(none)"] + [p.name for p in people]
    
    if add_type == "Decision":
                
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
        
        if st.button("Add", type="primary", key="add_decision_btn"):
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
                st.success("Added")
                st.rerun()
            else:
                st.warning("Please enter a decision.")
    
    elif add_type == "Action":
                
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
        
        if st.button("Add", type="primary", key="add_action_btn"):
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
                st.success("Added")
                st.rerun()
            else:
                st.warning("Please enter a task description.")
    
    elif add_type == "Blocker":
                
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
        
        if st.button("Add", type="primary", key="add_blocker_btn"):
            if blocker_desc:
                person_id = None
                if reported_by != "(none)":
                    person_id = reported_by.lower().replace(" ", "_")
                
                blocker = loader.add_blocker_realtime(
                    description=blocker_desc,
                    reported_by=person_id,
                    impact=blocker_impact if blocker_impact else None
                )
                st.success("Added")
                st.rerun()
            else:
                st.warning("Please describe the blocker.")
    
    elif add_type == "Person":
                
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
        
        if st.button("Add", type="primary", key="add_person_btn"):
            if person_name:
                person = loader.add_person_realtime(
                    name=person_name,
                    role=person_role if person_role else None,
                    email=person_email if person_email else None
                )
                st.success("Added")
                st.rerun()
            else:
                st.warning("Please enter a name.")
    
    elif add_type == "Note":
                
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
        
        if st.button("Add", type="primary", key="add_note_btn"):
            if note_content:
                note_id = loader.add_note_realtime(
                    content=note_content,
                    category=note_category
                )
                st.success("Added")
                st.rerun()
            else:
                st.warning("Please enter a note.")
    
    # Show recent additions (only if there are any)
    live_decisions = [d for d in loader.graph._decisions.values() if d.meeting_id == "live_meeting"]
    live_actions = [a for a in loader.graph._action_items.values() if a.meeting_id == "live_meeting"]
    live_blockers = [b for b in loader.graph._blockers.values() if b.meeting_id == "live_meeting"]

    if live_decisions or live_actions or live_blockers:
        st.markdown("---")
        with st.expander(f"This session: {len(live_decisions)} decisions, {len(live_actions)} actions, {len(live_blockers)} blockers"):
            for d in live_decisions[-5:]:
                st.markdown(f"- {d.content}")
            for a in live_actions[-5:]:
                st.markdown(f"- {a.task}")
            for b in live_blockers[-5:]:
                st.markdown(f"- {b.description}")


def main():
    """Main application entry point."""
    # Header
    st.markdown("<h1 class='main-header'>AMPM</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Your meeting memory</p>", unsafe_allow_html=True)

    # Initialize
    loader, engine, error = initialize_ampm()

    if error:
        st.error(f"Failed to load: {error}")
        if st.button("Retry"):
            st.cache_resource.clear()
            st.rerun()
        return

    # Render sidebar
    render_sidebar(loader, engine)

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Ask",
        "Add",
        "Decisions",
        "Actions",
        "Meetings",
        "Blockers"
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


if __name__ == "__main__":
    main()
