#!/usr/bin/env python3
"""
Streamlit UI for Personal Diary Assistant

A user-friendly web interface for the Personal Diary Assistant with
advanced memory capabilities, mood tracking, and personalized insights.

Features:
- Interactive chat interface
- Mood and productivity tracking
- Visual analytics and insights
- Goal setting and tracking
- Daily summaries and reports
- Memory search and exploration

Requirements:
- pip install streamlit plotly pandas
- Run with: streamlit run streamlit_app.py
"""

from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from diary_assistant import PersonalDiaryAssistant

# Page configuration
st.set_page_config(
    page_title="Personal Diary Assistant",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4A90E2;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    .assistant-message {
        background-color: #F3E5F5;
        border-left: 4px solid #9C27B0;
    }
    .metric-card {
        background-color: #F8F9FA;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #E9ECEF;
        text-align: center;
    }
    .mood-emoji {
        font-size: 2rem;
        margin: 0.5rem;
    }
    .stButton > button {
        background-color: #4A90E2;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize session state
def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "assistant" not in st.session_state:
        st.session_state.assistant = PersonalDiaryAssistant(
            "personal_diary_streamlit.db"
        )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "current_mood" not in st.session_state:
        st.session_state.current_mood = None

    if "current_productivity" not in st.session_state:
        st.session_state.current_productivity = 5

    if "daily_entries" not in st.session_state:
        st.session_state.daily_entries = []


def display_chat_message(message, sender):
    """Display a chat message with proper styling."""
    if sender == "user":
        st.markdown(
            f'<div class="chat-message user-message"><strong>You:</strong> {message}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message}</div>',
            unsafe_allow_html=True,
        )


def mood_to_emoji(mood):
    """Convert mood string to emoji."""
    mood_emojis = {
        "very_happy": "😊",
        "happy": "🙂",
        "neutral": "😐",
        "sad": "😢",
        "very_sad": "😭",
        "excited": "🤩",
        "anxious": "😰",
        "angry": "😠",
        "peaceful": "😌",
        "energetic": "⚡",
    }
    return mood_emojis.get(mood, "😐")


def create_mood_chart(mood_data):
    """Create a mood tracking chart."""
    if not mood_data:
        return None

    df = pd.DataFrame(mood_data)
    df["date"] = pd.to_datetime(df["date"])

    mood_scores = {
        "very_sad": 1,
        "sad": 2,
        "neutral": 3,
        "happy": 4,
        "very_happy": 5,
        "angry": 1,
        "anxious": 2,
        "peaceful": 4,
        "excited": 5,
        "energetic": 4,
    }

    df["mood_score"] = df["mood"].map(mood_scores)

    fig = px.line(
        df,
        x="date",
        y="mood_score",
        title="Mood Tracking Over Time",
        labels={"mood_score": "Mood Level", "date": "Date"},
    )

    fig.update_layout(
        yaxis={
            "range": [1, 5],
            "tickmode": "array",
            "tickvals": [1, 2, 3, 4, 5],
            "ticktext": ["Low", "Below Average", "Neutral", "Good", "Excellent"],
        }
    )

    return fig


def create_productivity_chart(productivity_data):
    """Create a productivity tracking chart."""
    if not productivity_data:
        return None

    df = pd.DataFrame(productivity_data)
    df["date"] = pd.to_datetime(df["date"])

    fig = px.bar(
        df,
        x="date",
        y="productivity",
        title="Daily Productivity Levels",
        labels={"productivity": "Productivity (1-10)", "date": "Date"},
    )

    fig.update_layout(yaxis={"range": [0, 10]})

    return fig


def main():
    """Main Streamlit application."""
    initialize_session_state()

    # Header
    st.markdown(
        '<h1 class="main-header">🌟 Personal Diary Assistant</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;">Your intelligent companion for personal growth and reflection</p>',
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.header("📋 Quick Actions")

        # Mood tracking
        st.subheader("🎭 Current Mood")
        mood_options = {
            "😊 Very Happy": "very_happy",
            "🙂 Happy": "happy",
            "😐 Neutral": "neutral",
            "😢 Sad": "sad",
            "😭 Very Sad": "very_sad",
            "🤩 Excited": "excited",
            "😰 Anxious": "anxious",
            "😠 Angry": "angry",
            "😌 Peaceful": "peaceful",
            "⚡ Energetic": "energetic",
        }

        selected_mood = st.selectbox("How are you feeling?", list(mood_options.keys()))
        st.session_state.current_mood = mood_options[selected_mood]

        # Productivity tracking
        st.subheader("📈 Productivity Level")
        st.session_state.current_productivity = st.slider(
            "Rate your productivity today (1-10)", 1, 10, 5
        )

        # Quick entry
        st.subheader("✍️ Quick Diary Entry")
        quick_entry = st.text_area("What's on your mind?", height=100)

        if st.button("💾 Save Entry"):
            if quick_entry.strip():
                result = st.session_state.assistant.process_diary_entry(
                    quick_entry,
                    mood=st.session_state.current_mood,
                    productivity=st.session_state.current_productivity,
                )
                st.success(result)
                st.session_state.daily_entries.append(
                    {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "time": datetime.now().strftime("%H:%M"),
                        "entry": quick_entry,
                        "mood": st.session_state.current_mood,
                        "productivity": st.session_state.current_productivity,
                    }
                )

        # Quick actions
        st.subheader("🔮 Quick Insights")
        if st.button("📊 Daily Summary"):
            summary = st.session_state.assistant.get_daily_summary()
            st.session_state.chat_history.append(("Daily Summary Request", "user"))
            st.session_state.chat_history.append((summary, "assistant"))

        if st.button("🎯 Get Recommendations"):
            recommendations = st.session_state.assistant.get_recommendations("general")
            st.session_state.chat_history.append(("Get Recommendations", "user"))
            st.session_state.chat_history.append((recommendations, "assistant"))

        if st.button("🧠 Analyze Patterns"):
            analysis = st.session_state.assistant.analyze_patterns("overall", "month")
            st.session_state.chat_history.append(("Analyze Patterns", "user"))
            st.session_state.chat_history.append((analysis, "assistant"))

    # Main content area with tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["💬 Chat", "📊 Analytics", "📝 Entries", "🎯 Goals"]
    )

    with tab1:
        st.header("💬 Chat with Your Assistant")

        # Chat interface
        chat_container = st.container()

        with chat_container:
            # Display chat history
            for message, sender in st.session_state.chat_history[
                -10:
            ]:  # Show last 10 messages
                display_chat_message(message, sender)

        # Chat input
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input("Type your message here...", key="chat_input")
        with col2:
            send_button = st.button("Send 📤")

        if send_button and user_input.strip():
            # Add user message to history
            st.session_state.chat_history.append((user_input, "user"))

            # Get assistant response
            response = st.session_state.assistant.chat_with_memory(user_input)
            st.session_state.chat_history.append((response, "assistant"))

            # Rerun to update the chat display
            st.rerun()

    with tab2:
        st.header("📊 Personal Analytics")

        # Today's metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                "Today's Mood",
                f"{mood_to_emoji(st.session_state.current_mood)} {st.session_state.current_mood.replace('_', ' ').title()}",
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Productivity", f"{st.session_state.current_productivity}/10")
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                "Entries Today",
                len(
                    [
                        e
                        for e in st.session_state.daily_entries
                        if e["date"] == date.today().strftime("%Y-%m-%d")
                    ]
                ),
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Entries", len(st.session_state.daily_entries))
            st.markdown("</div>", unsafe_allow_html=True)

        # Charts
        if st.session_state.daily_entries:
            col1, col2 = st.columns(2)

            with col1:
                mood_chart = create_mood_chart(st.session_state.daily_entries)
                if mood_chart:
                    st.plotly_chart(mood_chart, use_container_width=True)

            with col2:
                productivity_chart = create_productivity_chart(
                    st.session_state.daily_entries
                )
                if productivity_chart:
                    st.plotly_chart(productivity_chart, use_container_width=True)
        else:
            st.info("📈 Start adding diary entries to see your analytics!")

    with tab3:
        st.header("📝 Your Diary Entries")

        if st.session_state.daily_entries:
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                date_filter = st.date_input("Filter by date", value=date.today())
            with col2:
                mood_filter = st.selectbox(
                    "Filter by mood", ["All"] + list(mood_options.values())
                )

            # Display entries
            filtered_entries = st.session_state.daily_entries

            if date_filter:
                filtered_entries = [
                    e
                    for e in filtered_entries
                    if e["date"] == date_filter.strftime("%Y-%m-%d")
                ]

            if mood_filter != "All":
                filtered_entries = [
                    e for e in filtered_entries if e["mood"] == mood_filter
                ]

            for entry in reversed(filtered_entries):  # Show newest first
                with st.expander(
                    f"{entry['date']} at {entry['time']} - {mood_to_emoji(entry['mood'])} {entry['mood'].replace('_', ' ').title()}"
                ):
                    st.write(f"**Entry:** {entry['entry']}")
                    st.write(f"**Productivity:** {entry['productivity']}/10")
        else:
            st.info(
                "📖 No diary entries yet. Start by adding your first entry in the sidebar!"
            )

    with tab4:
        st.header("🎯 Goals & Progress")

        # Goal setting interface
        st.subheader("📋 Set New Goal")
        col1, col2 = st.columns(2)

        with col1:
            goal_title = st.text_input("Goal Title")
            goal_category = st.selectbox(
                "Category",
                ["Personal", "Professional", "Health", "Learning", "Relationships"],
            )

        with col2:
            goal_deadline = st.date_input("Target Date")
            goal_priority = st.selectbox("Priority", ["Low", "Medium", "High"])

        goal_description = st.text_area("Goal Description")

        if st.button("🎯 Add Goal"):
            if goal_title and goal_description:
                goal_entry = f"New goal set: {goal_title} (Category: {goal_category}, Priority: {goal_priority}, Deadline: {goal_deadline}). Description: {goal_description}"
                result = st.session_state.assistant.process_diary_entry(
                    goal_entry, tags=["goal", goal_category.lower()]
                )
                st.success("Goal added successfully!")

                # Ask for goal-specific recommendations
                goal_recommendations = st.session_state.assistant.get_recommendations(
                    "goals"
                )
                st.session_state.chat_history.append(
                    (f"Added new goal: {goal_title}", "user")
                )
                st.session_state.chat_history.append(
                    (goal_recommendations, "assistant")
                )

        # Progress tracking
        st.subheader("📈 Track Progress")
        progress_update = st.text_area("Update your progress on any goals...")

        if st.button("💾 Update Progress") and progress_update:
            result = st.session_state.assistant.process_diary_entry(
                f"Goal progress update: {progress_update}", tags=["progress", "goal"]
            )
            st.success("Progress updated!")

    # Footer
    st.markdown("---")
    st.markdown(
        "🌟 **Powered By [GibsonAI Memori](https://github.com/gibsonai/memori)** - Advanced memory capabilities for AI applications"
    )


if __name__ == "__main__":
    main()
