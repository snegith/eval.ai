import os
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import List, Optional

import streamlit as st
import plotly.graph_objects as go

# Ensure project root is on path (mirrors other UI pages)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from storage import session_store

st.set_page_config(
    page_title="Interview Results",
    page_icon="📊",
    layout="wide"
)


def _safe_load_json(session_id: str, filename: str, required_keys: Optional[List[str]] = None):
    """
    Load JSON via storage.session_store with light shape validation.

    Returns:
      - dict on success
      - None if file is missing
      - {"error": "..."} if file exists but is malformed or missing required keys
    """
    session_dir = Path(session_store.get_session_path(session_id))
    file_path = session_dir / filename
    if not file_path.exists():
        return None

    try:
        data = session_store.load_json(session_id, filename)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in {filename}: {e}"}
    except Exception as e:
        return {"error": f"Failed to load {filename}: {e}"}

    if isinstance(data, dict) and "error" in data:
        return data

    if required_keys:
        if not isinstance(data, dict):
            return {"error": f"{filename} must be a JSON object"}
        missing = [k for k in required_keys if k not in data]
        if missing:
            return {"error": f"{filename} missing required keys: {', '.join(missing)}"}

    return data


def load_session_results(session_id):
    """Load all results for a session."""
    results = {}

    results["metadata"] = _safe_load_json(session_id, "metadata.json") or {}
    results["eye_contact"] = _safe_load_json(
        session_id,
        "eye_contact_results.json",
        required_keys=["eye_contact_percentage"],
    ) or {}
    results["posture"] = _safe_load_json(
        session_id,
        "posture_results.json",
        required_keys=["posture_percentage"],
    ) or {}
    results["animation"] = _safe_load_json(
        session_id,
        "animation_results.json",
        required_keys=["expressiveness_score", "consistency_score", "stability_score"],
    ) or {}
    results["feedback"] = _safe_load_json(
        session_id,
        "feedback.json",
    ) or {}
    results["audio_metrics"] = _safe_load_json(
        session_id,
        "audio_metrics.json",
    ) or {}
    results["transcript"] = _safe_load_json(
        session_id,
        "transcript.json",
    ) or {}
    results["derived"] = _safe_load_json(
        session_id,
        "derived_results.json",
        required_keys=["confidence_score", "nervousness_score"],
    ) or {}

    return results


def get_session_metadata(results):
    """Extract session metadata with fallbacks."""
    metadata = results.get('metadata', {})
    
    # Get session date
    created_at = metadata.get('created_at', None)
    if created_at:
        # Parse ISO format and extract date
        session_date = created_at.split('T')[0]
    else:
        session_date = "Unknown"
    
    # Get duration
    duration_seconds = metadata.get('duration_seconds', None)
    if not duration_seconds:
        duration_seconds = results.get("audio_metrics", {}).get("duration_sec")
    if not duration_seconds:
        duration_seconds = results.get("transcript", {}).get("duration_sec")
    if duration_seconds:
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        duration_str = f"{minutes}m {seconds}s"
    else:
        duration_str = "Unknown"

    return session_date, duration_str, metadata.get("status", "unknown")


def get_color_for_score(score):
    """Return color based on score (with transparency variant)."""
    if score >= 75:
        return "#22c55e", "#22c55e20"  # Green, Green with transparency
    elif score >= 60:
        return "#eab308", "#eab30820"  # Yellow
    elif score >= 45:
        return "#f97316", "#f9731620"  # Orange
    else:
        return "#ef4444", "#ef444420"  # Red


def display_colored_metric(label, score, grade=""):
    """Display metric with color-coded styling."""
    color, bg_color = get_color_for_score(score)
    
    grade_text = f"<p style='margin:0; color: {color}; font-size: 14px;'>{grade}</p>" if grade else ""
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {bg_color} 0%, {bg_color}50 100%);
        border-left: 4px solid {color};
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    ">
        <p style="margin:0; color: #666; font-size: 12px; text-transform: uppercase;">{label}</p>
        <h2 style="margin:5px 0; color: {color};">{score:.1f}%</h2>
        {grade_text}
    </div>
    """, unsafe_allow_html=True)


def get_grade_emoji(grade):
    """Return emoji based on grade."""
    grade_lower = grade.lower()
    if "excellent" in grade_lower:
        return "🌟"
    elif "good" in grade_lower:
        return "✅"
    elif "fair" in grade_lower:
        return "👍"
    else:
        return "📝"


def create_radar_chart(metrics):
    """Create a radar chart for behavioral metrics."""
    categories = ['Eye Contact', 'Posture', 'Expressiveness', 'Consistency', 'Stability']
    
    values = [
        metrics.get('eye_contact', {}).get('eye_contact_percentage', 0),
        metrics.get('posture', {}).get('posture_percentage', 0),
        metrics.get('animation', {}).get('expressiveness_score', 0),
        metrics.get('animation', {}).get('consistency_score', 0),
        metrics.get('animation', {}).get('stability_score', 0)
    ]
    
    # Close the radar chart
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        name='Your Performance',
        line_color='rgb(34, 197, 94)',
        fillcolor='rgba(34, 197, 94, 0.3)'
    ))
    
    # Add benchmark line (70%)
    benchmark = [70] * len(categories_closed)
    fig.add_trace(go.Scatterpolar(
        r=benchmark,
        theta=categories_closed,
        fill='none',
        name='Target (70%)',
        line=dict(color='gray', dash='dash')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        height=400
    )
    
    return fig


# ============================================================
# MAIN APP
# ============================================================

st.title("📊 Interview Analysis Results")

# Sidebar - Session Selection
st.sidebar.header("Select Session")

# Get available sessions
sessions_dir = Path(session_store.BASE_DIR)
if not sessions_dir.exists():
    st.error("No sessions found. Please complete an interview first.")
    st.stop()

available_sessions = [d.name for d in sessions_dir.iterdir() if d.is_dir()]

if not available_sessions:
    st.error("No sessions found. Please complete an interview first.")
    st.stop()

selected_session = st.sidebar.selectbox(
    "Session ID",
    available_sessions,
    format_func=lambda x: f"Session {x}"
)

# Load results
with st.spinner("Loading results..."):
    results = load_session_results(selected_session)

if not results:
    st.error(f"No results found for session {selected_session}")
    st.stop()

# ============================================================
# PHASE 5A: CORE RESULTS DISPLAY
# ============================================================

# Overall Score Section
st.header("🎯 Overall Performance")

feedback = results.get('feedback', {})
if isinstance(feedback, dict) and feedback.get("error"):
    st.error(f"Feedback not available: {feedback['error']}")
    feedback = {}
overall_score = feedback.get('overall_score', 0)

# Get session metadata
session_date, duration_str, session_status = get_session_metadata(results)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.metric(
        "Overall Interview Score",
        f"{overall_score}/100",
        delta=None
    )
    st.progress(overall_score / 100)
    
    # Grade interpretation
    if overall_score >= 80:
        st.success("🌟 Excellent Performance!")
    elif overall_score >= 65:
        st.success("✅ Good Performance!")
    elif overall_score >= 50:
        st.warning("👍 Fair Performance")
    else:
        st.info("📝 Needs Improvement")

with col2:
    st.metric(
        "Session Date",
        session_date
    )

with col3:
    st.metric(
        "Session Duration",
        duration_str
    )

st.caption(f"Session status: `{session_status}`")

st.divider()

# ============================================================
# PHASE 5B: VISUAL SCORING UI
# ============================================================

st.header("📈 Behavioral Metrics")

# Metric Cards
col1, col2, col3 = st.columns(3)

# Eye Contact
eye_contact = results.get('eye_contact', {})
if isinstance(eye_contact, dict) and eye_contact.get("error"):
    st.warning(f"Eye contact results unavailable: {eye_contact['error']}")
    eye_contact = {}
eye_score = eye_contact.get('eye_contact_percentage', 0)
eye_grade = eye_contact.get('grade', 'Unknown')

with col1:
    st.subheader("👁️ Eye Contact")
    st.metric(
        "",
        f"{eye_score:.1f}%",
        delta=f"{eye_grade}"
    )
    st.progress(eye_score / 100)
    
    # Details in expander
    with st.expander("Details"):
        st.write(f"**Grade:** {get_grade_emoji(eye_grade)} {eye_grade}")
        st.write(f"**Longest Streak:** {eye_contact.get('longest_streak', 0)} frames")
        st.write(f"**Stability:** {eye_contact.get('gaze_stability', 0):.2f}")

# Posture
posture = results.get('posture', {})
if isinstance(posture, dict) and posture.get("error"):
    st.warning(f"Posture results unavailable: {posture['error']}")
    posture = {}
posture_score = posture.get('posture_percentage', 0)
posture_grade = posture.get('grade', 'Unknown')

with col2:
    st.subheader("🧍 Posture")
    st.metric(
        "",
        f"{posture_score:.1f}%",
        delta=f"{posture_grade}"
    )
    st.progress(posture_score / 100)
    
    with st.expander("Details"):
        st.write(f"**Grade:** {get_grade_emoji(posture_grade)} {posture_grade}")
        st.write(f"**Torso Angle:** {posture.get('mean_torso_angle_deg', 0):.1f}°")
        st.write(f"**Shoulder Tilt:** {posture.get('mean_shoulder_tilt', 0):.4f}")

# Facial Animation
animation = results.get('animation', {})
if isinstance(animation, dict) and animation.get("error"):
    st.warning(f"Facial animation results unavailable: {animation['error']}")
    animation = {}
express_score = animation.get('expressiveness_score', 0)
animation_grade = animation.get('grade', 'Unknown')

with col3:
    st.subheader("😊 Facial Animation")
    st.metric(
        "",
        f"{express_score:.1f}/100",
        delta=f"{animation.get('consistency_score', 0):.1f}% consistency"
    )
    st.progress(express_score / 100)
    
    with st.expander("Details"):
        st.write(f"**Grade:** {get_grade_emoji(animation_grade)} {animation_grade}")
        st.write(f"**Expressiveness:** {express_score:.1f}/100")
        st.write(f"**Consistency:** {animation.get('consistency_score', 0):.1f}/100")
        st.write(f"**Stability:** {animation.get('stability_score', 0):.1f}/100")

st.divider()

# Radar Chart
st.subheader("🎯 Performance Radar")
radar_fig = create_radar_chart(results)
st.plotly_chart(radar_fig, use_container_width=True)

st.divider()

# Derived indicators (mathematical, explainable; not emotion classification)
derived = results.get("derived", {})
if isinstance(derived, dict) and derived.get("error"):
    st.warning(f"Derived indicators unavailable: {derived['error']}")
else:
    confidence_score = float(derived.get("confidence_score", 0.0))
    nervousness_score = float(derived.get("nervousness_score", 0.0))

    st.subheader("🧮 Derived Indicators (Explainable)")
    st.caption(
        "Derived mathematically from behavioral metrics (not emotion detection). "
        "Confidence is derived from eye contact + posture. "
        "Nervousness is an indicator derived from facial animation consistency + stability."
    )

    col_conf, col_nerv = st.columns(2)

    with col_conf:
        confidence_score_normalized = min(100.0, (confidence_score / 95.0) * 100.0)
        st.metric("Confidence (derived, normalized)", f"{confidence_score_normalized:.1f}/100")
        st.progress(min(1.0, confidence_score_normalized / 100.0))
        st.caption("Normalized to a 100-point display scale. The underlying derived score is capped at 95.")

    with col_nerv:
        st.metric("Nervousness indicator (derived)", f"{nervousness_score:.1f}/100")
        st.progress(min(1.0, nervousness_score / 100.0))

# ============================================================
# FEEDBACK DISPLAY
# ============================================================

st.header("💬 AI Feedback")

# Score Breakdown
if 'score_breakdown' in feedback:
    st.subheader("Score Breakdown")
    breakdown = feedback['score_breakdown']
    
    cols = st.columns(4)
    metrics_list = [
        ("Content", breakdown.get('content', 0)),
        ("Eye Contact", breakdown.get('eye_contact', 0)),
        ("Posture", breakdown.get('posture', 0)),
        ("Animation", breakdown.get('animation', 0))
    ]
    
    for col, (label, score) in zip(cols, metrics_list):
        with col:
            st.metric(label, f"{score}/100")
            st.progress(score / 100)

st.divider()

# Summary
st.subheader("📝 Overall Assessment")
st.info(feedback.get('summary', 'No summary available'))

# Strengths
st.subheader("💪 Key Strengths")
for i, strength in enumerate(feedback.get('strengths', []), 1):
    st.success(f"**{i}.** {strength}")

# Improvements
st.subheader("📈 Areas for Improvement")
for i, improvement in enumerate(feedback.get('improvements', []), 1):
    st.warning(f"**{i}.** {improvement}")

# STAR Analysis (if applicable)
if 'star_analysis' in feedback:
    star = feedback['star_analysis']
    if star.get('applicable'):
        st.divider()
        st.subheader("⭐ STAR Method Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        star_components = [
            ("Situation", star.get('situation_score')),
            ("Task", star.get('task_score')),
            ("Action", star.get('action_score')),
            ("Result", star.get('result_score'))
        ]
        
        for col, (component, score) in zip([col1, col2, col3, col4], star_components):
            with col:
                if score:
                    st.metric(component, f"{score}/5")
                    st.progress(score / 5)
        
        st.info(f"**Feedback:** {star.get('feedback', 'N/A')}")

# Recommendations
st.subheader("💡 Actionable Recommendations")
for i, rec in enumerate(feedback.get('recommendations', []), 1):
    st.info(f"**{i}.** {rec}")

st.divider()

# ============================================================
# EXPORT OPTIONS
# ============================================================

st.header("📥 Export Results")

col1, col2 = st.columns(2)

with col1:
    # Download JSON
    json_str = json.dumps({
        'session_id': selected_session,
        'results': results
    }, indent=2)

    st.download_button(
        label="Download JSON Report",
        data=json_str,
        file_name=f"interview_results_{selected_session}.json",
        mime="application/json"
    )

with col2:
    # Download Text Summary
    text_report = f"""
INTERVIEW ANALYSIS REPORT
Session: {selected_session}
Date: {datetime.now().strftime("%Y-%m-%d")}

OVERALL SCORE: {overall_score}/100

BEHAVIORAL METRICS:
- Eye Contact: {eye_score:.1f}% ({eye_grade})
- Posture: {posture_score:.1f}% ({posture_grade})
- Facial Animation: {express_score:.1f}/100 ({animation_grade})

SUMMARY:
{feedback.get('summary', 'N/A')}

STRENGTHS:
{chr(10).join([f"{i}. {s}" for i, s in enumerate(feedback.get('strengths', []), 1)])}

IMPROVEMENTS:
{chr(10).join([f"{i}. {s}" for i, s in enumerate(feedback.get('improvements', []), 1)])}

RECOMMENDATIONS:
{chr(10).join([f"{i}. {s}" for i, s in enumerate(feedback.get('recommendations', []), 1)])}
"""

    st.download_button(
        label="Download Text Report",
        data=text_report,
        file_name=f"interview_report_{selected_session}.txt",
        mime="text/plain"
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption("🤖 AI Interview Evaluator | Powered by Computer Vision + LLM")
