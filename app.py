import streamlit as st
import pandas as pd
import openai
from serpapi import GoogleSearch

# Replace with your actual OpenAI API key
openai.api_key = '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'

# SERP API key for search functionality
serp_api_key = "55b7da9dbcdc19d7921b8d84e59ab34bcba8df3013dd056a605f7269ae0f9a24"

# IATA codes for cities
city_codes = {
    'Sydney': 'SYD',
    'Bangkok': 'BKK',
    'New York': 'JFK',
    'Dhaka': 'DAC',
    'Los Angeles': 'LAX',
    'London': 'LHR',
    'Bali': 'DPS'
}

############ General #############
def general(user_input):
    system_message = """
    You are a helpful, professional, and knowledgeable travel assistant. Your role is to assist users with any travel-related inquiries by providing accurate, high-quality, and detailed answers.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ]
    )
    return response['choices'][0]['message']['content']

################### Plan ##############
def plan(user_input):
    day, city2 = [item.strip() for item in user_input.split(",")]
    system_message = f"""
        You are an expert travel assistant, specializing in creating personalized and detailed travel itineraries. The user plans to stay for {day} days in {city2}. Based on the destination and the length of the stay, your task is to generate a complete, day-by-day itinerary that covers activities from morning to night.
        """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ]
    )
    return response['choices'][0]['message']['content']

########### Flight Search (SERP API) #############
def flight(user_input):
    try:
        # Split the input into components
        travel_start_date, return_date, adults, children, destination_city_temp, departure_city_temp, flight_class, price_range = [item.strip() for item in user_input.split(",")]

        # Convert the city name into IATA code
        destination_city = city_codes.get(destination_city_temp.strip().title())
        departure_city = city_codes.get(departure_city_temp.strip().title())

        if not destination_city or not departure_city:
            return "Invalid city name(s). Please provide valid city names."

        params = {
            "engine": "google_flights",
            "q": f"flights from {departure_city} to {destination_city}",
            "departure_date": travel_start_date,
            "return_date": return_date,
            "adults": adults,
            "children": children,
            "api_key": serp_api_key
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        flight_data = []

        for flight in results.get("flight_results", []):
            flight_info = {
                "Departure": flight.get("departure_airport", "N/A"),
                "Arrival": flight.get("arrival_airport", "N/A"),
                "Duration": flight.get("duration", "N/A"),
                "Price": flight.get("price", {}).get("total", "N/A")
            }
            flight_data.append(flight_info)

        if not flight_data:
            return f"No flights found from {departure_city_temp} to {destination_city_temp}."

        # Convert results to a pandas DataFrame for easier display
        df_flights = pd.DataFrame(flight_data)
        return df_flights

    except Exception as e:
        return f"An error occurred: {str(e)}"

############### Hotel Search (SERP API) #############
def hotel(user_input):
    try:
        # Split the input into components
        checkin, checkout, adults, price, city = [item.strip() for item in user_input.split(",")]

        params = {
            "engine": "google_hotels",
            "q": f"hotels in {city}",
            "check_in_date": checkin,
            "check_out_date": checkout,
            "adults": adults,
            "api_key": serp_api_key
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        hotel_data = []

        for hotel in results.get("hotel_results", []):
            hotel_info = {
                "Name": hotel.get("name", "N/A"),
                "Price per Night": hotel.get("price", {}).get("total", "N/A"),
                "Rating": hotel.get("rating", "N/A")
            }
            hotel_data.append(hotel_info)

        if not hotel_data:
            return f"No hotels found in {city}."

        # Convert results to a pandas DataFrame for easier display
        df_hotels = pd.DataFrame(hotel_data)
        return df_hotels

    except Exception as e:
        return f"An error occurred: {str(e)}"

# Function to classify user queries into 'hotel', 'flight', or 'general'
def classify_travel_query(user_input):
    system_message = """
    You are an advanced travel assistant specialized in classifying questions related to travel.
    The categories of questions you classify are:

    1. 'hotel': If the query is related to hotel information, booking, or accommodation-related services.
    2. 'flight': If the query is related to flight information, booking, airline services, or flight-related inquiries.
    3. 'general': If the query is about general travel-related information that does not fall into the above categories.
    4. 'plan': If the query is about creating a plan for the trip (itineraries, things to do, or places to visit).
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ],
        max_tokens=10,
        temperature=0
    )

    classification = response['choices'][0]['message']['content'].strip().lower().strip("'\"")
    return classification

################### Streamlit Interface ###################
################### Streamlit Interface ###################
def main():
    st.title("Travel Chatbot Assistant")

    st.write("""
    Welcome to your personal travel assistant! Ask me about flights, hotels, trip planning, or general travel inquiries, and I'll help you find the information you need.
    """)

    # Initialize the conversation
    if 'history' not in st.session_state:
        st.session_state.history = []

    # User input for chat
    user_input = st.text_input("You: ", placeholder="Ask me anything related to travel...")

    # If the user submits input
    if st.button("Send"):
        if user_input:
            # Classify the query (using the backend function)
            query_type = classify_travel_query(user_input)

            # Respond based on classification
            if query_type == 'general':
                response = general(user_input)
            elif query_type == 'plan':
                response = plan(user_input)
            elif query_type == "flight":
                response = flight(user_input)
            elif query_type == "hotel":
                response = hotel(user_input)
            else:
                response = "Sorry, I couldn't classify your query. Please ask again."

            # Append user input and bot response to session state history
            st.session_state.history.append(f"You: {user_input}")
            st.session_state.history.append(f"Bot: {response}")

    # Display the conversation history
    if st.session_state.history:
        for message in st.session_state.history:
            st.write(message)
