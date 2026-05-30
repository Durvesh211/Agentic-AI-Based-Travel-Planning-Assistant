import streamlit as st

from main import search_flights, search_hotel, search_places, get_weather, budget_calculator, llm
st.set_page_config(page_title="Travel Planner")

st.title("Agentic AI-Based Travel Planning Assistant ")
st.subheader("Build your Holiday plan in seconds!")

cities = [
    "Delhi",
    "Mumbai",
    "Goa",
    "Bangalore",
    "Chennai",
    "Hyderabad",
    "Kolkata",
    "Jaipur"
]

source = st.selectbox("From where are you going?", cities)
destination = st.selectbox("Where do you want to go?", cities)

days = st.slider("How many days for the trip?", min_value=1, max_value=8)
budget = st.number_input(
    "Maximum Total Trip Budget (₹)",
    min_value=5000,
    value=25000
)

if st.button("Give me plan"):
    if source == destination:
        st.error("Source and destination cannot be the same.")
        st.stop()
    if not source or not destination:
        st.error("Please enter both source and destination.")
    else:
        st.write(f"Planning your trip to {destination} from {source} for {days} days.")
        with st.spinner("Loading"):
            try:
                flights = search_flights.invoke({
                    "source": source,
                    "destination": destination
                })
                if not flights:
                    st.error("No flights found.")
                    st.stop()

                hotels = search_hotel.invoke({
                    "city": destination
                })
                if not hotels:
                    st.error("No hotels found.")
                    st.stop()
                places = search_places.invoke({
                    "place": destination
                })

                weather = get_weather.invoke({
                    "city": destination,
                    "days": days
                })
                selected_flight = flights[0]
                selected_hotel = hotels[0]
                budget_data = budget_calculator.invoke({
                    "flight_price": selected_flight["price"],
                    "hotel_cost_per_night": selected_hotel["price_per_night"],
                    "days": days
                })
                if budget_data["total"] > budget:
                    st.error(
                        f"Trip cost ₹{budget_data['total']} exceeds your budget of ₹{budget}"
                    )
                    st.stop()

                places_text = "\n".join(
                    [f"- {p['name']} ({p['type']}, Rating: {p['rating']})"
                     for p in places]
                )
                response = llm.invoke(f"""
                Plan a {days}-day trip to {destination} from {source}.
                Flight Selected:
                Airline: {selected_flight["airline"]}
                Price: ₹{selected_flight["price"]}
                Departure: {selected_flight["departure_time"]}
                Hotel Selected:
                Name: {selected_hotel["name"]}
                Price Per Night: ₹{selected_hotel["price_per_night"]}
                Stars: {selected_hotel["stars"]}
                Places:
                {places_text}
                Weather:
                {weather}
                Budget:
                Flight: ₹{budget_data["flight"]}
                Hotel: ₹{budget_data["hotel"]}
                Food: ₹{budget_data["food"]}
                Travel: ₹{budget_data["travel"]}
                Total: ₹{budget_data["total"]}
                Return in this format:
                ### Trip Summary
                ### Flight Selected
                ### Hotel Booked
                ### Weather Forecast
                ### Day Wise Itinerary
                ### Budget Breakdown
                ### Reason for these Choices 
                Do not include IDs.
                """)

                st.markdown(response.content)
            except Exception as e:
                st.error(f"Something is wrong:{e}")

            st.download_button(
                "Download Itinerary",
                response.content,
                file_name="trip_plan.txt"
            )

