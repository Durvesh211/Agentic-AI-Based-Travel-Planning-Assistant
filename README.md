Agentic AI-Based Travel Planning Assistant

A LangChain-powered travel planning application that generates personalized trip itineraries using real-time data and an LLM agent.

Project Overview
This assistant helps users plan a complete trip by automatically searching flights, hotels, and tourist places, fetching live weather forecasts, calculating the total budget, and generating a day-wise itinerary — all in one click.

Built as a capstone project demonstrating LangChain tool-calling agents integrated with a Streamlit UI.

 Project Structure
travel-planner/
├── main.py              # LangChain tools, agent, and LLM setup
├── app.py               # Streamlit frontend UI
├── data/
│   ├── flights.json     # Mock flight data
│   ├── hotels.json      # Mock hotel data
│   └── places.json      # Mock tourist attractions data
├── .env                 # API keys (not committed)
├── requirements.txt     # Python dependencies
└── README.md

How It Works

The app follows a two-path architecture:

main.py — Agent + Tools

Defines five LangChain @tool functions
Creates a ChatGroq LLM (Llama 3.3 70B)
Builds a create_tool_calling_agent with a structured prompt
Can also be run directly from the terminal
app.py — Streamlit UI

Provides a clean web interface for user input
Calls each tool directly (non-agent mode), then passes results to the LLM for itinerary generation
Displays the formatted plan and offers a download button

Tools
Tool	Description
search_flights	Finds the 3 cheapest flights between source and destination from local JSON data
search_hotel	Returns top 3 hotels in the destination city, sorted by stars
search_places	Returns top 5 rated tourist attractions in the city
get_weather	Fetches live daily weather forecast via the Open-Meteo API
budget_calculator	Calculates total trip cost: flight + hotel + food (₹500/day) + local travel (₹500/day)

Getting Started

1. Clone the repository
bash
git clone https://github.com/your-username/travel-planner.git
cd travel-planner

2. Install dependencies
bash
pip install -r requirements.txt

3. Set up environment variables
Create a .env file in the root directory:

env
GROQ_API_KEY=your_groq_api_key_here
Get your free API key at console.groq.com.

4. Run the app
Streamlit UI (recommended):

bash
streamlit run app.py
Terminal (agent mode):

bash
python main.py

Supported Cities
Delhi · Mumbai · Goa · Bangalore · Chennai · Hyderabad · Kolkata · Jaipur

Output Format
The assistant returns a structured travel plan:

Trip Summary — Overview of the planned trip
Flight Selected — Airline, price, and departure time
Hotel Booked — Hotel name, stars, and nightly rate
Weather Forecast — Daily max/min temperature and precipitation
Day-Wise Itinerary — Suggested activities for each day
Budget Breakdown — Itemised cost (flight, hotel, food, travel, total)
Reason for Choices — LLM explanation of selections

Dependencies

streamlit
langchain
langchain-groq
langchain-core
langchain-classic
openmeteo-requests
requests-cache
retry-requests
pandas
python-dotenv

Environment Variables
Variable	Description
GROQ_API_KEY	API key for Groq (LLM provider)

Notes

Flight, hotel, and places data are loaded from local JSON files in the data/ directory. You can extend these files to add more routes or destinations.
Weather data is fetched live from Open-Meteo and cached for 1 hour to reduce API calls.
The Streamlit UI uses direct tool invocation (not the agent executor) for more predictable, structured output.
The terminal mode uses the full LangChain agent with tool-calling for a more autonomous experience.