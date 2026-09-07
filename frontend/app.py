import streamlit as st
import requests
import datetime
import os

# Try to get from Streamlit secrets first, fallback to os.getenv, and finally default
try:
    BACKEND_URL = st.secrets.get("BACKEND_URL", "https://tripgenie-hev2.onrender.com")
except Exception:
    BACKEND_URL = os.getenv("BACKEND_URL", "https://tripgenie-hev2.onrender.com")

st.set_page_config(page_title="TripGenie", layout="wide")

st.title("🌍 TripGenie: AI Travel Planner")

st.sidebar.header("Your Trip Details")
destination = st.sidebar.text_input("Destination", "Paris")
start_date = st.sidebar.date_input("Start Date", datetime.date.today() + datetime.timedelta(days=7))
end_date = st.sidebar.date_input("End Date", datetime.date.today() + datetime.timedelta(days=10))
budget = st.sidebar.number_input("Total Budget ($)", value=1200.0, step=100.0)
travelers = st.sidebar.number_input("Travelers", value=1, min_value=1)

needs_flights = st.sidebar.checkbox("Need Flights?", value=True)
origin = ""
if needs_flights:
    origin = st.sidebar.text_input("Origin", "New York")
needs_hotel = st.sidebar.checkbox("Need Hotel?", value=True)

if "plan_data" not in st.session_state:
    st.session_state.plan_data = None

if st.sidebar.button("Generate Itinerary"):
    with st.spinner("Agents are planning your trip (fetching weather, attractions, optimizing budget)..."):
        payload = {
            "user_input": {
                "origin": origin,
                "destination": destination,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "budget": budget,
                "travelers": travelers,
                "needs_flights": needs_flights,
                "needs_hotel": needs_hotel
            }
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/api/plan", json=payload)
            response.raise_for_status()
            st.session_state.plan_data = response.json()
            st.success(f"Itinerary generated! (Thread ID: {st.session_state.plan_data['thread_id']})")
        except Exception as e:
            st.error(f"API Error: {e}")

if st.session_state.plan_data:
    data = st.session_state.plan_data
    itinerary = data.get("draft_itinerary")
    if itinerary:
        st.subheader(f"Trip to {itinerary['destination']}")
        st.metric("Estimated Cost", f"${itinerary['estimated_cost']:.2f} / ${itinerary['total_budget']:.2f}")
        
        if itinerary.get("flights"):
            st.subheader("✈️ Flights")
            for f in itinerary["flights"]:
                st.write(f"**{f['airline']}** ({f['flight_number']}) | {f['departure_time']} ➔ {f['arrival_time']} | **${f['estimated_price']:.2f}**")
                
        if itinerary.get("hotels"):
            st.subheader("🏨 Hotels")
            for h in itinerary["hotels"]:
                rating = f"{h['rating']} ⭐" if h.get('rating') else "No rating"
                st.write(f"**{h['name']}** - {h['address']} | {rating} | **${h['price_per_night']:.2f}**/night")
                
        with st.expander("Agent Logs & Critic Feedback", expanded=True):
            st.write(f"**Retries needed:** {data['retry_count']}")
            st.write(f"**Is Valid Budget?** {data['is_valid']}")
            st.write(f"**Critic Notes:** {data['critic_feedback']}")
        
        for day in itinerary['daily_plans']:
            st.markdown(f"### 📅 {day['date']} (Estimated daily cost: ${day['daily_cost_estimate']})")
            st.markdown(f"**Morning:** {day['morning_activity']}")
            st.markdown(f"**Afternoon:** {day['afternoon_activity']}")
            st.markdown(f"**Evening:** {day['evening_activity']}")
            st.divider()
            
        if itinerary.get("warning_note"):
            st.warning(itinerary["warning_note"])
            
        st.divider()
        if st.button("Export to PDF & Share 📄", type="primary"):
            with st.spinner("Generating PDF and uploading to S3..."):
                try:
                    pdf_res = requests.post(f"{BACKEND_URL}/api/plan/{data['thread_id']}/export-pdf")
                    pdf_res.raise_for_status()
                    pdf_url = pdf_res.json().get("url")
                    st.success("PDF generated successfully!")
                    st.markdown(f"**[Click here to view/download your PDF Itinerary]({pdf_url})**")
                except Exception as pe:
                    st.error(f"Failed to export PDF: {pe}")
            
    else:
        st.error("Failed to generate itinerary. Check logs.")
