# 🌟 Personal Diary Assistant

A comprehensive personal diary assistant powered by Memori's advanced memory capabilities, designed to help you track your daily experiences, analyze patterns, and receive personalized recommendations for improving your life.

## ✨ Features

### 🧠 Advanced Memory Capabilities
- **Persistent Memory**: All conversations and diary entries are stored and analyzed using Memori
- **Pattern Recognition**: Automatically identifies trends in mood, productivity, and life events
- **Contextual Responses**: Provides personalized advice based on your complete history

### 📱 User-Friendly Interface
- **Streamlit Web App**: Beautiful, interactive web interface
- **Command Line Interface**: Terminal-based interaction for quick entries
- **Mood Tracking**: Visual mood analysis with emoji support
- **Productivity Metrics**: Track and visualize your daily productivity levels

### 📊 Analytics & Insights
- **Pattern Analysis**: Analyze mood, productivity, habits, goals, and relationships
- **Personalized Recommendations**: Get specific advice tailored to your patterns
- **Daily Summaries**: Automatic daily reflection and insights
- **Goal Tracking**: Set, monitor, and achieve personal and professional goals

### 🎯 Smart Features
- **Memory Search**: Find relevant past experiences and insights
- **Habit Analysis**: Understand your behavioral patterns
- **Progress Monitoring**: Track improvements over time
- **Automated Insights**: Receive proactive suggestions for better living

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Virtual environment (recommended)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd personal_diary_assistant
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### 🖥️ Running the Applications

#### Streamlit Web Interface (Recommended)
```bash
streamlit run streamlit_app.py
```
This will open a beautiful web interface at `http://localhost:8501`

#### Command Line Interface
```bash
python diary_assistant.py
```

#### Demo Script (See How It Works)
```bash
python demo.py
```
Run this to see a demonstration of all key features including diary entries, pattern analysis, and personalized recommendations in the CLI.

## 📚 How to Use

### 🌅 Daily Workflow

1. **Morning Setup**
   - Open the app and set your current mood
   - Add your daily goals or intentions

2. **Throughout the Day**
   - Add diary entries as things happen
   - Rate your productivity levels
   - Record important events or thoughts

3. **Evening Reflection**
   - Request a daily summary
   - Get personalized recommendations
   - Plan for tomorrow

### 💬 Example Interactions

**Diary Entry:**
```
"Had a productive day at work, finished the project proposal and got positive feedback from my manager. Feeling accomplished but also a bit stressed about the upcoming deadline."
```

**Asking for Insights:**
```
"Can you analyze my productivity patterns over the last month?"
"What recommendations do you have for managing my work stress?"
"How has my mood been trending lately?"
```

**Goal Setting:**
```
"I want to start exercising regularly - can you help me create a plan?"
"Track my progress on learning Python"
```

## 📊 Analytics Features

### 📈 Available Analysis Types
- **Mood Patterns**: Track emotional trends and triggers
- **Productivity Analysis**: Understand your most productive times and conditions
- **Habit Tracking**: Monitor recurring behaviors and their impacts
- **Goal Progress**: Measure advancement toward objectives
- **Relationship Insights**: Analyze social interactions and their effects
- **Overall Life Trends**: Comprehensive lifestyle pattern analysis

### 🎯 Recommendation Categories
- **Productivity**: Time management, work efficiency, focus improvements
- **Wellbeing**: Mental health, stress management, work-life balance
- **Relationships**: Social connections, communication improvements
- **Habits**: Behavior modification, routine optimization
- **Goals**: Achievement strategies, milestone planning
- **General**: Overall life enhancement suggestions

## 🔮 Advanced Features

### Function Calling
The assistant uses advanced function calling with these tools:
- `memory_search`: Find relevant past experiences
- `analyze_patterns`: Examine trends across different time periods
- `get_recommendations`: Generate personalized advice

### Smart Context Management
- Maintains conversation history within sessions
- Integrates past memories for contextual responses
- Balances recent context with historical patterns

### Extensibility
The modular design allows for easy addition of:
- New analysis types
- Additional data sources
- Custom visualization components
- Third-party integrations

## 🔒 Privacy & Security

- **Local Storage**: All data stored locally in SQLite databases
- **No Cloud Sync**: Your personal information stays on your device
- **API Usage**: Only OpenAI API calls for AI processing (no data retention by default)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**Start your journey to better self-awareness and personal growth today!** 🌟
