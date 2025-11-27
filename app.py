import streamlit as st
from datetime import datetime, timedelta
import requests

# -----------------------------
# Constants
# -----------------------------
# Fetch API key securely (ensure secrets.toml exists locally or in Streamlit Cloud)
try:
    API_KEY = st.secrets["calendarific"]["api_key"]
except Exception:
    st.warning("⚠️ API key not found. Using a placeholder key for testing.")
    API_KEY = "YOUR_TEST_KEY_HERE"

HOLIDAY_API_URL = "https://calendarific.com/api/v2/holidays"

# -----------------------------
# Helper Functions
# -----------------------------

def get_weekend_days(country):
    country = country.lower()
    if country in ["india", "usa", "uk", "canada", "australia", "singapore"]:
        return [5, 6]  # Saturday, Sunday
    if country in ["uae", "saudi arabia", "qatar"]:
        return [4, 5]  # Friday, Saturday
    return [5, 6]

def fetch_public_holidays(country_code, year):
    """Fetch public holidays using Calendarific API"""
    try:
        params = {"api_key": API_KEY, "country": country_code, "year": year}
        response = requests.get(HOLIDAY_API_URL, params=params)
        data = response.json()
        holidays_list = []
        for h in data.get("response", {}).get("holidays", []):
            holidays_list.append(datetime.strptime(h["date"]["iso"], "%Y-%m-%d").date())
        return holidays_list
    except Exception as e:
        st.warning(f"Error fetching public holidays: {e}")
        return []

def calculate_last_working_day(resignation_date, notice_period, country_code):
    weekend_days = get_weekend_days(country_code)
    tentative_last_day = resignation_date + timedelta(days=notice_period)
    all_holidays = fetch_public_holidays(country_code, tentative_last_day.year)

    while tentative_last_day.weekday() in weekend_days or tentative_last_day.date() in all_holidays:
        tentative_last_day += timedelta(days=1)
    return tentative_last_day

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Last Working Day Calculator", page_icon="🗓️", layout="centered")
st.title("🗓️ Last Working Day Calculator")
st.markdown("Enter your resignation date, notice period, and country to calculate your last working day.")

# Inputs
resignation_date = st.date_input("📅 Date of Resignation")
notice_period = st.number_input("📏 Notice Period (in days)", min_value=1, value=30)
country = st.selectbox("🌍 Country", ["India", "USA", "UK", "Canada", "Australia", "Singapore", "UAE", "Saudi Arabia", "Qatar", "Other"])

# Map country to ISO code for holiday API
country_codes = {
    "India": "IN", "USA": "US", "UK": "GB", "Canada": "CA",
    "Australia": "AU", "Singapore": "SG", "UAE": "AE", "Saudi Arabia": "SA",
    "Qatar": "QA", "Other": "US"
}
country_code = country_codes.get(country, "US")

# Action button
if st.button("Calculate Last Working Day"):
    resignation_dt = datetime.combine(resignation_date, datetime.min.time())
    last_working_day = calculate_last_working_day(resignation_dt, notice_period, country_code)
    st.success(f"✅ Your Last Working Day is: {last_working_day.strftime('%A, %d %B %Y')}")
