# 🌍 Personalized Travel Planner Agent

An intelligent travel planning assistant built with CrewAI agents and Memori memory integration. This demo showcases how to create AI agents that remember user preferences and provide personalized travel recommendations.

![Personalized Travel Planner Agent Demo](./assets/Memori%20Travel%20Planner%20Agent%20Demo.cmproj.gif)

## ✨ Features

### 🤖 AI Agent Capabilities
- **Travel Research Agent**: Searches for flights, hotels, activities, and current deals using CrewAI's SerperDevTool
- **Personal Travel Planner**: Creates detailed, personalized itineraries  
- **Budget Advisor**: Provides cost estimates and money-saving tips

### 🧠 Memory Integration
- **Persistent Memory**: Remembers your travel preferences across sessions using Memori
- **Conscious Ingestion**: Automatically identifies and stores important travel information
- **Personalized Recommendations**: Gets better at planning trips you'll love over time

### 🔍 Web Search Integration
- **Real-time Data**: Uses CrewAI's SerperDevTool for current travel information
- **Flight Prices**: Searches for up-to-date flight costs and deals
- **Hotel Reviews**: Finds accommodations with recent reviews
- **Local Activities**: Discovers attractions and experiences

### 🎨 Streamlit UI
- **Interactive Interface**: Easy-to-use web application
- **Memory Search**: Search your past travel preferences and trips
- **Preference Tracking**: Set and remember travel style, budget, and accommodation preferences

## 🚀 Installation

### 1. Prerequisites
```bash
# Ensure you're in the demos/travel_planner directory
cd demos/travel_planner

# Install Python dependencies
pip install -r requirements.txt
```

### 2. API Keys Required

#### OpenAI API Key
- Visit [OpenAI Platform](https://platform.openai.com/api-keys)
- Create a new API key
- Copy the key (starts with `sk-`)

#### Serper API Key  
- Visit [Serper.dev](https://serper.dev)
- Sign up for free account (100 searches/month free)
- Get your API key

### 3. Environment Setup
Create a `.env` file in this directory:

```env
OPENAI_API_KEY=sk-your-openai-key-here
SERPER_API_KEY=your-serper-key-here
```

## 🎯 Usage

### 1. Run the Application
```bash
streamlit run app.py
```

### 2. Plan Your Trip
1. **Describe your travel plans** in the text area
2. **Set your preferences**: budget, travel style, accommodation, group size
3. **Click "Plan My Trip"** and watch the AI agents work together
4. **Review your personalized itinerary** with research, planning, and budget breakdown

### 3. Memory Features
- **Search Past Trips**: Use the memory search to find previous travel plans
- **Preference Learning**: The system remembers your travel style and preferences
- **Continuous Improvement**: Each interaction makes future recommendations more personalized

## 📋 Example Interactions

### First Time User
```
Input: "I want to visit Japan for 10 days in April. I love anime, traditional culture, and great food."

The agents will:
1. Research flights to Japan in April using SerperDevTool
2. Find anime-related attractions (Tokyo, Akihabara)
3. Suggest traditional cultural experiences (temples, tea ceremonies)
4. Recommend food experiences (ramen tours, sushi classes)
5. Create a 10-day itinerary within $3000 budget
6. Store preferences in Memori: Japan interest, cultural activities, food experiences, $3000 budget range
```

### Returning User  
```
Input: "Plan a 5-day trip to Thailand"

The system remembers from Memori:
- Previous budget preferences
- Interest in cultural activities
- Food experiences preference
- Travel style from past trips

Result: Personalized Thailand itinerary matching your established preferences
```

## 📈 Future Enhancements

### Planned Features
- **Multi-destination trips**: Plan complex itineraries across multiple countries
- **Group travel coordination**: Handle different preferences for group trips
- **Booking integration**: Direct links to booking platforms
- **Photo integration**: Visual itinerary with destination photos
- **Weather integration**: Real-time weather considerations

### Advanced Memory Features
- **Trip comparison**: Compare multiple trip options using Memori
- **Seasonal preferences**: Remember preferred travel seasons
- **Activity clustering**: Group similar activities you enjoy using memory analysis
- **Budget learning**: AI learns your spending patterns from memory

## 🤝 Contributing

This demo is part of the Memori project. To contribute:

1. Fork the repository
2. Create your feature branch
3. Test with the travel planner demo
4. Submit a pull request

## 🙏 Acknowledgments

- **Memori SDK**: For providing the memory layer
- **CrewAI**: For the multi-agent framework
- **Streamlit**: For the user interface
