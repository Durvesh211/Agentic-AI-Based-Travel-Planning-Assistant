import json
import os
import openmeteo_requests
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import requests_cache
from langchain.tools import tool
from retry_requests import retry
load_dotenv()
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate

key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

print("Running program")


def load_json(filename):
    with open(f"data/{filename}", "r") as f:
        return json.load(f)


@tool
def search_flights(source: str, destination: str) -> list:
    """Search for the cheapest flight from source to destination and return it."""
    flights = load_json("flights.json")
    results = [f for f in flights if f["from"].lower() == source.lower() and
               f["to"].lower() == destination.lower()]
    if not results:
        return []
    results.sort(key=lambda x: x["price"])
    return results[0:3]


@tool
def search_hotel(city: str) -> list:
    """ Search for available hotels in the city and return top 3 hotels"""
    hotels = load_json("hotels.json")
    results = [h for h in hotels
               if h["city"].lower() == city.lower()]
    results.sort(key=lambda x:(x["stars"], -x["price_per_night"]),reverse=True)
    return results[:3]


@tool
def search_places(place: str) -> list:
    """Search for top tourist places and attractions in a city. Returns top 5 rated places."""
    places = load_json("places.json")
    results = [p for p in places if p["city"].lower() == place.lower()]
    results.sort(key=lambda x: x["rating"], reverse=True)
    return results[:5]


@tool
def get_weather(city: str, days: int) -> str:
    """Get weather forecast for a city for given number of days. Returns daily max/min temperature and precipitation."""
    days = int(days)
    city_coords = {
        "delhi": {"lat": 28.6139, "lon": 77.2090},
        "mumbai": {"lat": 19.0760, "lon": 72.8777},
        "goa": {"lat": 15.2993, "lon": 74.1240},
        "bangalore": {"lat": 12.9716, "lon": 77.5946},
        "chennai": {"lat": 13.0827, "lon": 80.2707},
        "hyderabad": {"lat": 17.3850, "lon": 78.4867},
        "kolkata": {"lat": 22.5726, "lon": 88.3639},
        "jaipur": {"lat": 26.9124, "lon": 75.7873},
    }

    coords = city_coords.get(city.lower())
    if not coords:
        return "Weather for the city is not available."

    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "forecast_days": days
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]
    print(f"Coordinates: {response.Latitude()} {response.Longitude()}")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

    daily = response.Daily()

    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
    daily_precipitation_probability = daily.Variables(2).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    ), "temperature_2m_max": daily_temperature_2m_max, "temperature_2m_min": daily_temperature_2m_min,
        "precipitation_sum": daily_precipitation_probability}

    daily_dataframe = pd.DataFrame(data=daily_data)

    weather_summary = []

    for _, row in daily_dataframe.iterrows():
        weather_summary.append(
            f"Max:{row['temperature_2m_max']:.2f}°C "
            f"Min:{row['temperature_2m_min']:.2f}°C "
            f"Rain:{row['precipitation_sum']:.2f}mm"
        )

    return "\n".join(weather_summary)


@tool
def budget_calculator(flight_price: int, hotel_cost_per_night: int, days: int) -> dict:
    """Calculate total trip budget given flight price, hotel price per night, and number of days."""
    hotel_cost = hotel_cost_per_night * days
    food_cost = 500 * days
    travel_cost = 500 * days

    total = flight_price + hotel_cost + food_cost + travel_cost

    return {
        "flight": flight_price,
        "hotel": hotel_cost,
        "food": food_cost,
        "travel": travel_cost,
        "total": total
    }

tools = [search_flights, search_hotel, search_places, get_weather, budget_calculator]

prompt = ChatPromptTemplate.from_messages([("system", """
                                            You are an expert travel planning assistant.
                                            You must:
                                            1. Search flights
                                            2. Search hotels
                                            3. Search attractions
                                            4. Check weather
                                            5. Calculate budget
                                            Always use available tools before answering.
                                            Return:
                                            ## Trip Summary
                                            ## Flight Selected
                                            ## Hotel Booked
                                            ## Weather Forecast
                                            ## Day Wise Itinerary
                                            ## Budget Breakdown
                                            ## Why These Choices Were Made"""),
                                           ("human", "{input}"),
                                           ("placeholder", "{agent_scratchpad}")])
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
if __name__ == "__main__":
    # chain = prompt | llm
    source = input("From where are you going? \n")
    destination = input("Where do you want to go? \n")
    days = int(input("how many days for the trip? \n"))

    response = agent_executor.invoke({"input": f"Plan a {days} day trip to {destination} from {source}. Find flights, hotels, places, weather and calculate total budget. Give day-wise itinerary. Do not include IDs."})
    print(response["output"])

    # flights = search_flights(source, destination)
    # hotels = search_hotel(destination)
    # places = search_places(destination)
    # weather = get_weather(destination,days)
    # budget = budget_calculator(flights, hotels,days)
    #
    # user_Input = f"""Plan a {days} days trip to {destination} from {source}.
    # Available flights (cheapest flight first) : {flights}
    # Available hotels (Highest Rating first): {hotels}
    # Places to see : {places}
    # Weather forecast: {weather}
    # Budget breakdown:
    # - Flight cost: ₹{budget['flight']}
    # - Hotel cost: ₹{budget['hotel']}
    # - Food cost: ₹{budget['food']}
    # - Local travel cost: ₹{budget['travel']}
    # - Total estimated cost: ₹{budget['total']}
    # Give me the best flight, hotels and places and why?
    # Also give me day wise iternary and final budget.
    # Do not include ids.
    # """
    #
    # response = chain.invoke({"user_input": user_Input})
    # print(response.content)
