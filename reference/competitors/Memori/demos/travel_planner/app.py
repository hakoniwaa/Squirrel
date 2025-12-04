"""
Personalized Travel Planner Streamlit App
A clean UI for the CrewAI-powered travel planning assistant with Memori memory integration
"""

import streamlit as st
from travel_agent import TravelPlannerAgent


def main():
    """Main Streamlit application"""

    st.set_page_config(
        page_title="🌍 Personalized Travel Planner", page_icon="✈️", layout="wide"
    )

    st.title("🌍 Personalized Travel Planner Agent")
    st.markdown("**AI-powered travel planning with memory of your preferences**")

    # Initialize the travel agent
    if "travel_agent" not in st.session_state:
        try:
            with st.spinner("🧠 Initializing travel planning agent..."):
                st.session_state["travel_agent"] = TravelPlannerAgent()
                st.success("✅ Travel agent initialized!")
        except ValueError as e:
            st.error(f"❌ Configuration Error: {str(e)}")
            st.info(
                """
            **Please set up your environment:**

            1. Create a `.env` file in this directory with:
            ```
            OPENAI_API_KEY=sk-your-openai-key-here
            SERPER_API_KEY=your-serper-key-here
            ```

            2. Get your API keys:
            - 🔸 **OpenAI API Key**: Visit [OpenAI Platform](https://platform.openai.com/api-keys)
            - 🔸 **Serper API Key**: Visit [Serper.dev](https://serper.dev) (100 free searches/month)
            """
            )
            return
        except Exception as e:
            st.error(f"❌ Initialization Error: {str(e)}")
            st.info("Please check your .env file and dependencies.")
            return

    # Main interface
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("✈️ Plan Your Trip")

        # Travel request input
        travel_request = st.text_area(
            "Describe your travel plans:",
            placeholder="I want to visit Japan for 10 days in April. I love anime, traditional culture, and great food.",
            height=100,
        )

        # Additional preferences
        st.subheader("🎯 Travel Preferences")

        col_pref1, col_pref2 = st.columns(2)

        with col_pref1:
            budget_range = st.selectbox(
                "Budget Range",
                [
                    "Budget ($500-1500)",
                    "Mid-range ($1500-3500)",
                    "Luxury ($3500+)",
                    "No specific budget",
                ],
            )

            travel_style = st.selectbox(
                "Travel Style",
                [
                    "Adventure",
                    "Cultural",
                    "Relaxation",
                    "Food & Drink",
                    "Nature",
                    "City Explorer",
                    "Mixed",
                ],
            )

        with col_pref2:
            accommodation_type = st.selectbox(
                "Accommodation Preference",
                [
                    "Hotels",
                    "Airbnb/Rentals",
                    "Hostels",
                    "Resorts",
                    "Boutique",
                    "No preference",
                ],
            )

            group_size = st.selectbox(
                "Group Size",
                [
                    "Solo",
                    "Couple",
                    "Family with kids",
                    "Friends group",
                    "Large group (6+)",
                ],
            )

        # Plan trip button
        if st.button("🚀 Plan My Trip", type="primary"):
            if not travel_request.strip():
                st.warning("Please describe your travel plans!")
                return

            # Prepare the full request
            full_request = f"""
            {travel_request}

            Additional preferences:
            - Budget: {budget_range}
            - Travel Style: {travel_style}
            - Accommodation: {accommodation_type}
            - Group: {group_size}
            """

            # Prepare preferences data
            user_preferences = {
                "budget_range": budget_range,
                "travel_style": travel_style,
                "accommodation_type": accommodation_type,
                "group_size": group_size,
            }

            with st.spinner("🤖 AI agents are planning your perfect trip..."):
                try:
                    # Use the travel agent to plan the trip
                    result = st.session_state["travel_agent"].plan_trip(
                        full_request, user_preferences
                    )

                    # Display results
                    st.success("🎉 Your personalized travel plan is ready!")
                    st.markdown("---")
                    st.markdown(result)

                except Exception as e:
                    st.error(f"❌ Error creating travel plan: {str(e)}")
                    st.info(
                        "This might be due to API limits or connectivity issues. Please try again."
                    )

    with col2:
        st.header("🧠 Your Travel Memory")

        # Memory search
        st.subheader("🔍 Search Past Trips")
        memory_query = st.text_input(
            "Ask about your travel history:",
            placeholder="When was my last trip? What are my budget preferences? Japan trips...",
        )

        if st.button("Search Memory"):
            if memory_query and "travel_agent" in st.session_state:
                try:
                    with st.spinner("🧠 Searching your travel memory..."):
                        results = st.session_state["travel_agent"].search_memory(
                            memory_query
                        )
                    st.markdown(results)
                except Exception as e:
                    st.error(f"Search error: {str(e)}")
            elif not memory_query:
                st.warning("Please enter a question about your travel history!")

        # Add example queries for better user experience
        with st.expander("💡 Example Memory Questions"):
            st.markdown(
                """
            **Try asking questions like:**
            - "When was my last trip?"
            - "What are my budget preferences?"
            - "Where have I traveled recently?"
            - "What hotels do I prefer?"
            - "What activities do I enjoy?"
            - "Any trips to Europe?"
            - "My dining preferences"
            - "Transportation preferences"
            """
            )

        # Memory stats
        st.subheader("📊 Memory Stats")
        if "travel_agent" in st.session_state:
            try:
                stats = st.session_state["travel_agent"].get_memory_stats()
                for key, value in stats.items():
                    st.write(f"🔸 **{key.replace('_', ' ').title()}**: {value}")
            except:
                st.write("Memory stats loading...")

        # Quick tips
        st.subheader("💡 Tips")
        st.info(
            """
        **This AI remembers:**
        - Your travel preferences
        - Past trip requests
        - Budget ranges
        - Favorite destinations
        - Activity preferences

        **The more you use it, the better it gets at planning trips you'll love!**
        """
        )

        # Environment status
        st.subheader("⚙️ Configuration")
        if "travel_agent" in st.session_state:
            st.success("✅ Environment variables loaded")
            st.success("✅ Memori memory active")
            st.success("✅ CrewAI agents ready")
        else:
            st.warning("⚠️ Agent not initialized")


if __name__ == "__main__":
    main()
