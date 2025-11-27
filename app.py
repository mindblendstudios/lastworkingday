import streamlit as st
from datetime import datetime, timedelta
import requests
from io import BytesIO
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# -----------------------------
# Constants & Config
# -----------------------------
API_KEY = st.secrets["calendarific"]["api_key"]  # Securely fetch API key
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

def calculate_last_working_day(resignation_date, notice_period, country_code, custom_holidays=[], company_rule="include_weekends"):
    weekend_days = get_weekend_days(country_code)
    tentative_last_day = resignation_date + timedelta(days=notice_period)
    all_holidays = fetch_public_holidays(country_code, tentative_last_day.year) + custom_holidays

    while tentative_last_day.weekday() in weekend_days or tentative_last_day.date() in all_holidays:
        if company_rule == "exclude_weekends_only":
            if tentative_last_day.weekday() in weekend_days:
                tentative_last_day += timedelta(days=1)
            else:
                break
        else:
            tentative_last_day += timedelta(days=1)
    return tentative_last_day

def generate_pdf(resignation_date, notice_period, last_working_day, country, custom_holidays):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Last Working Day Summary", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Resignation Date: {resignation_date.strftime('%A, %d %B %Y')}", ln=True)
    pdf.cell(0, 10, f"Notice Period (days): {notice_period}", ln=True)
    pdf.cell(0, 10, f"Country: {country}", ln=True)
    pdf.cell(0, 10, f"Custom Holidays: {', '.join([d.strftime('%d-%m-%Y') for d in custom_holidays]) if custom_holidays else 'None'}", ln=True)
    pdf.cell(0, 10, f"Calculated Last Working Day: {last_working_day.strftime('%A, %d %B %Y')}", ln=True)

    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return BytesIO(pdf_bytes)

def send_email(recipient_email, pdf_file, last_working_day):
    try:
        sender_email = "your_email@example.com"  # Replace with your sender
        sender_password = "your_email_password"  # Replace with your password / app password
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = f"Last Working Day Notification: {last_working_day.strftime('%d-%m-%Y')}"
        message.attach(MIMEText(f"Your calculated last working day is {last_working_day.strftime('%A, %d %B %Y')}. Please find the attached PDF.", "plain"))

        part = MIMEApplication(pdf_file.read(), Name="Last_Working_Day.pdf")
        part['Content-Disposition'] = 'attachment; filename="Last_Working_Day.pdf"'
        message.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        st.success("✅ Email sent successfully!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="Last Working Day Calculator", page_icon="🗓️", layout="centered")
st.title("🗓️ Enhanced Last Working Day Calculator")
st.markdown("Calculate your last working day considering notice period, weekends, public holidays, and company rules.")

# Inputs
resignation_date = st.date_input("📅 Date of Resignation")
notice_period = st.number_input("📏 Notice Period (in days)", min_value=1, value=30)
country = st.selectbox("🌍 Country", ["India", "USA", "UK", "Canada", "Australia", "Singapore", "UAE", "Saudi Arabia", "Qatar", "Other"])
country_code = st.text_input("ISO Country Code (for holiday API, e.g., IN, US)", value="IN" if country=="India" else "US")
custom_holidays_input = st.text_area("📌 Optional Custom Holidays (comma separated, format: YYYY-MM-DD)")
company_rule = st.selectbox("🏢 Company Notice Rule", ["include_weekends", "exclude_weekends_only"])
send_email_option = st.checkbox("📧 Send summary via email")
recipient_email = st.text_input("Recipient Email (required if sending email)")

# Parse custom holidays
custom_holidays = []
if custom_holidays_input:
    try:
        custom_holidays = [datetime.strptime(d.strip(), "%Y-%m-%d").date() for d in custom_holidays_input.split(",")]
    except:
        st.error("❌ Invalid custom holiday format. Use YYYY-MM-DD.")

# Calculate Button
if st.button("Calculate Last Working Day"):
    resignation_dt = datetime.combine(resignation_date, datetime.min.time())
    last_working_day = calculate_last_working_day(resignation_dt, notice_period, country_code, custom_holidays, company_rule)
    st.success(f"✅ **Your Last Working Day is: {last_working_day.strftime('%A, %d %B %Y')}**")

    # Generate PDF
    pdf_file = generate_pdf(resignation_date, notice_period, last_working_day, country, custom_holidays)
    st.download_button("📥 Download PDF Summary", data=pdf_file, file_name="Last_Working_Day.pdf", mime="application/pdf")

    # Send email if requested
    if send_email_option:
        if recipient_email:
            send_email(recipient_email, pdf_file, last_working_day)
        else:
            st.error("❌ Please provide recipient email to send summary.")

# Footer
st.markdown("---")
st.markdown("💡 Built with Streamlit | Powered by Calendarific API for public holidays | Customizable for company rules")
