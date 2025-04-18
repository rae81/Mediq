import os
import json
import datetime
import re
import requests
import calendar
from datetime import timedelta
from dateutil import parser
from django.utils import timezone
from .models import Appointment, Doctor, DoctorBusyTime

# =============================================================================
# API & GLOBAL CONFIGURATIONS
# =============================================================================

# LLM API configuration (for MediqBot responses)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Azure Cognitive Services TTS credentials (for client-side use)
AZURE_TTS_KEY_1 = "CAPzpFr4grlCpwt9LvR3kHokXuSuQiTAppwp78AZK7UBLjo09abDJQQJ99BDAC3pKaRXJ3w3AAAYACOGLkkz"
AZURE_TTS_KEY_2 = "D3V4tLvzgg45YGyVT6gFUlNicQn4Ghl8oITmy0CvauTRrpRW9oFYJQQJ99BDAC3pKaRXJ3w3AAAYACOGjy1n"
AZURE_TTS_ENDPOINT = "https://eastasia.api.cognitive.microsoft.com/"

# For weather simulation (using Azure Maps demo)
AZURE_MAPS_CLIENT_ID = "03067322-195e-4b1c-a34f-d4c9e214f5fd"
AZURE_MAPS_PRIMARY_KEY = "DBcP1FueHQFGmQ3wwHga9niu5BMER1XlqPDfPz9YVaOkBKE9tgXaJQQJ99BDACi5YpzlUnSqAAAgAZMPot2U"

# Clinic location for Beirut
CLINIC_LOCATION = {
    "address": "Beirut Medical Center, Hamra Street, Beirut, Lebanon",
    "latitude": 33.8938,
    "longitude": 35.5018
}

# Severe weather conditions & seasonal patterns
SEVERE_WEATHER_CONDITIONS = [
    "heavyrain", "thunderstorm", "flooding", "strongwinds",
    "sandstorm", "heatwave", "extremeheat", "duststorm"
]
BEIRUT_WEATHER_PATTERNS = {
    "winter": ["rain", "heavyrain", "thunderstorm"],
    "spring": ["lightrain", "partlycloudy", "windy"],
    "summer": ["clear", "hot", "humidity"],
    "fall": ["cloudy", "lightrain", "windy"]
}

# Mock data for doctors and specialties
DOCTORS = {
    "Dr. Salim": {
        "specialty": "Cardiology",
        "available_days": ["Monday", "Wednesday", "Friday"],
        "calendar_id": "salim_cardiology@mediq.com"
    },
    "Dr. Haddad": {
        "specialty": "Dermatology",
        "available_days": ["Tuesday", "Thursday"],
        "calendar_id": "haddad_dermatology@mediq.com"
    },
    "Dr. Nassar": {
        "specialty": "Pediatrics",
        "available_days": ["Monday", "Tuesday", "Friday"],
        "calendar_id": "nassar_pediatrics@mediq.com"
    },
    "Dr. Farah": {
        "specialty": "Neurology",
        "available_days": ["Wednesday", "Thursday", "Friday"],
        "calendar_id": "farah_neurology@mediq.com"
    },
    "Dr. Kassem": {
        "specialty": "Orthopedics",
        "available_days": ["Monday", "Wednesday", "Thursday"],
        "calendar_id": "kassem_orthopedics@mediq.com"
    },
}

SPECIALTIES = {
    "Cardiology": "Heart-related issues such as chest pain, palpitations, and high blood pressure.",
    "Dermatology": "Skin conditions including rashes, acne, eczema, and skin cancer screening.",
    "Pediatrics": "Healthcare for children and adolescents.",
    "Neurology": "Brain and nervous system disorders like headaches, seizures, and dizziness.",
    "Orthopedics": "Bone and joint problems such as fractures, sprains, and back pain.",
    "General Medicine": "Routine check-ups, minor illnesses, and preventive care."
}

SYMPTOM_TO_SPECIALTY = {
    "chest pain": "Cardiology",
    "heart palpitations": "Cardiology",
    "shortness of breath": "Cardiology",
    "high blood pressure": "Cardiology",
    "irregular heartbeat": "Cardiology",
    "rash": "Dermatology",
    "acne": "Dermatology",
    "skin lesion": "Dermatology",
    "itchy skin": "Dermatology",
    "eczema": "Dermatology",
    "psoriasis": "Dermatology",
    "mole": "Dermatology",
    "child fever": "Pediatrics",
    "childhood vaccination": "Pediatrics",
    "child development": "Pediatrics",
    "child checkup": "Pediatrics",
    "headache": "Neurology",
    "migraine": "Neurology",
    "seizure": "Neurology",
    "dizziness": "Neurology",
    "numbness": "Neurology",
    "memory problems": "Neurology",
    "joint pain": "Orthopedics",
    "back pain": "Orthopedics",
    "fracture": "Orthopedics",
    "sprain": "Orthopedics",
    "bone injury": "Orthopedics",
    "arthritis": "Orthopedics",
    "fever": "General Medicine",
    "cough": "General Medicine",
    "sore throat": "General Medicine",
    "flu": "General Medicine",
    "annual checkup": "General Medicine",
    "vaccination": "General Medicine",
    "physical": "General Medicine"
}

INSURANCE_PROVIDERS = [
    "National Social Security Fund",
    "AXA Middle East",
    "Allianz SNA",
    "MEDGULF",
    "Bankers SAL",
    "AROPE",
    "LibanCare"
]

# Time slots for appointments (9:00 to 17:00)
TIME_SLOTS = [f"{hour}:00" for hour in range(9, 18)]

# Global in-memory storage for weather alerts (demo only)
weather_alerts = []


# =============================================================================
# WEATHER SYSTEM CLASS
# =============================================================================

class WeatherSystem:
    def __init__(self, api_key=AZURE_MAPS_PRIMARY_KEY):
        self.api_key = api_key

    def get_weather_forecast(self, date_str, time_str):
        try:
            appointment_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            hour, minute = map(int, time_str.split(':'))
            appointment_datetime = appointment_date.replace(hour=hour, minute=minute)
            # Determine season
            month = appointment_datetime.month
            if month in [12, 1, 2]:
                season = "winter"
            elif month in [3, 4, 5]:
                season = "spring"
            elif month in [6, 7, 8]:
                season = "summer"
            else:
                season = "fall"
            seasonal_conditions = BEIRUT_WEATHER_PATTERNS.get(season, ["clear"])
            weather_seed = (appointment_datetime.day + appointment_datetime.hour) % 10
            if weather_seed < 2:
                condition_index = (appointment_datetime.day + appointment_datetime.month) % len(SEVERE_WEATHER_CONDITIONS)
                weather_condition = SEVERE_WEATHER_CONDITIONS[condition_index]
                weather_description = f"Severe {weather_condition}"
                is_severe = True
            else:
                condition_index = (appointment_datetime.day + appointment_datetime.month) % len(seasonal_conditions)
                weather_condition = seasonal_conditions[condition_index]
                weather_description = f"Normal {weather_condition}"
                is_severe = False
            temp_ranges = {"winter": (10, 20), "spring": (15, 25), "summer": (25, 35), "fall": (20, 30)}
            temp_min, temp_max = temp_ranges.get(season, (15, 25))
            temperature = temp_min + (weather_seed % (temp_max - temp_min))
            return {
                "date": date_str,
                "time": time_str,
                "condition": weather_condition,
                "description": weather_description,
                "temperature": temperature,
                "precipitation": 60 if is_severe else 10,
                "wind_speed": 35 if is_severe else 10,
                "is_severe": is_severe
            }
        except Exception as e:
            print("Weather forecast error:", e)
            return {"date": date_str, "time": time_str, "condition": "unknown", "description": "Weather data unavailable", "is_severe": False}

    def check_weather_before_appointment(self, date_str, time_str, minutes_before=30):
        try:
            appointment_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            check_dt = appointment_dt - timedelta(minutes=minutes_before)
            check_date = check_dt.strftime("%Y-%m-%d")
            check_time = check_dt.strftime("%H:%M")
            forecast = self.get_weather_forecast(check_date, check_time)
            if forecast.get("is_severe", False):
                return {
                    "appointment_date": date_str,
                    "appointment_time": time_str,
                    "check_time": f"{check_date} {check_time}",
                    "weather_condition": forecast["condition"],
                    "weather_description": forecast["description"],
                    "alert_message": f"Severe weather alert: {forecast['description']} expected around your appointment time.",
                    "needs_rescheduling": True
                }
            return None
        except Exception as e:
            print("check_weather_before_appointment error:", e)
            return None


# =============================================================================
# NOTIFICATION SYSTEM CLASS
# =============================================================================

class NotificationSystem:
    def __init__(self):
        self.sent_notifications = []

    def send_appointment_confirmation(self, appointment_data):
        # Do not reveal internal data to the patient
        notif = {
            "type": "appointment_confirmation",
            "message": f"Your appointment on {appointment_data['date']} at {appointment_data['time']} is confirmed."
        }
        self.sent_notifications.append(notif)
        return {"success": True}

    def send_weather_alert(self, alert):
        notif = {
            "type": "weather_alert",
            "message": f"Severe weather alert: Your appointment at {alert['appointment_time']} may be affected."
        }
        self.sent_notifications.append(notif)
        return {"success": True}

    def send_rescheduling_confirmation(self, old_appointment, new_appointment):
        notif = {
            "type": "rescheduling_confirmation",
            "message": f"Your appointment has been rescheduled from {old_appointment['date']} {old_appointment['time']} to {new_appointment['date']} {new_appointment['time']}."
        }
        self.sent_notifications.append(notif)
        return {"success": True}


# =============================================================================
# CALENDAR SYSTEM CLASS
# =============================================================================

class CalendarSystem:
    def __init__(self, user):
        self.user = user
        self.weather_system = WeatherSystem()
        self.notification_system = NotificationSystem()

    def check_time_slot_available(self, doctor_name, date_str, time_str):
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            time_obj = datetime.datetime.strptime(time_str, "%H:%M").time()
        except Exception as e:
            print("Time conversion error:", e)
            return False
        
        # Check for appointment conflicts
        appointment_conflict = Appointment.objects.filter(doctor=doctor_name, date=date_obj, time=time_obj).exists()
        
        # Check for doctor busy time conflicts - first get the Doctor instance
        try:
            doctor_instances = Doctor.objects.filter(name__icontains=doctor_name)
            busy_time_conflict = False
            
            for doctor_instance in doctor_instances:
                # Check if this time falls within any busy time periods
                busy_times = DoctorBusyTime.objects.filter(
                    doctor=doctor_instance,
                    date=date_obj
                )
                
                for busy_time in busy_times:
                    # Convert time_str to datetime.time object for comparison
                    appointment_time = datetime.datetime.strptime(time_str, "%H:%M").time()
                    
                    # Check if appointment time falls within the busy time period
                    if busy_time.start_time <= appointment_time <= busy_time.end_time:
                        busy_time_conflict = True
                        break
                
                if busy_time_conflict:
                    break
        except Exception as e:
            print(f"Error checking doctor busy times: {e}")
            busy_time_conflict = False
        
        # Time is available only if there are no conflicts
        return not (appointment_conflict or busy_time_conflict)

    def get_available_slots(self, doctor_name, date_str):
        available = []
        if doctor_name not in DOCTORS:
            return available
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception as e:
            print("Date conversion error:", e)
            return available
        day_of_week = calendar.day_name[date_obj.weekday()]
        if day_of_week not in DOCTORS[doctor_name]["available_days"]:
            return available
        for slot in TIME_SLOTS:
            if self.check_time_slot_available(doctor_name, date_str, slot):
                available.append(slot)
        return available

    def add_appointment(self, appointment_data):
        doc = appointment_data.get("doctor", "TBA")
        date_obj = datetime.datetime.strptime(appointment_data["date"], "%Y-%m-%d").date()
        time_obj = datetime.datetime.strptime(appointment_data["time"], "%H:%M").time()
        if doc in DOCTORS and not self.check_time_slot_available(doc, appointment_data["date"], appointment_data["time"]):
            return {"success": False, "message": "That time slot is already booked."}
        appt = Appointment.objects.create(
            user=self.user,
            doctor=doc,
            specialty=appointment_data.get("specialty", "General Medicine"),
            date=date_obj,
            time=time_obj,
            reason=appointment_data.get("reason", ""),
            contact=appointment_data.get("contact", ""),
            insurance=appointment_data.get("insurance", "")
        )
        self.notification_system.send_appointment_confirmation(appointment_data)
        self.schedule_weather_check(appointment_data)
        return {"success": True, "appointment": appt}

    def schedule_weather_check(self, appointment_data):
        alert = self.weather_system.check_weather_before_appointment(
            appointment_data["date"], appointment_data["time"], minutes_before=30
        )
        if alert:
            alert["patient_name"] = appointment_data["patient_name"]
            alert["contact"] = appointment_data["contact"]
            alert["doctor"] = appointment_data.get("doctor", "")
            alert["specialty"] = appointment_data.get("specialty", "")
            alert["original_appointment"] = appointment_data
            alert["rescheduling_options"] = self.generate_rescheduling_options(
                appointment_data["doctor"], appointment_data["date"], appointment_data["time"]
            )
            weather_alerts.append(alert)
            self.notification_system.send_weather_alert(alert)

    def generate_rescheduling_options(self, doctor_name, date_str, time_str):
        options = {"same_day": [], "next_day": []}
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        hour, minute = map(int, time_str.split(':'))
        new_hour = hour + 1
        if new_hour < 17:
            new_time = f"{new_hour:02d}:{minute:02d}"
            if self.check_time_slot_available(doctor_name, date_str, new_time):
                options["same_day"].append(new_time)
        next_day = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        next_day_slots = self.get_available_slots(doctor_name, next_day)[:3]
        options["next_day"] = {"date": next_day, "slots": next_day_slots}
        return options

    def reschedule_appointment(self, alert_id, option_type, new_time=None):
        if alert_id >= len(weather_alerts):
            return {"success": False, "message": "Alert not found."}
        alert = weather_alerts[alert_id]
        original = alert["original_appointment"]
        new_appt = original.copy()
        if option_type == "same_day":
            if new_time and new_time in alert["rescheduling_options"]["same_day"]:
                new_appt["time"] = new_time
            else:
                if alert["rescheduling_options"]["same_day"]:
                    new_appt["time"] = alert["rescheduling_options"]["same_day"][0]
                else:
                    return {"success": False, "message": "No same-day options available."}
        elif option_type == "next_day":
            next_day = alert["rescheduling_options"]["next_day"]
            new_appt["date"] = next_day["date"]
            if new_time and new_time in next_day["slots"]:
                new_appt["time"] = new_time
            else:
                if next_day["slots"]:
                    new_appt["time"] = next_day["slots"][0]
                else:
                    return {"success": False, "message": "No next-day options available."}
        else:
            return {"success": False, "message": "Invalid option."}
        try:
            date_obj = datetime.datetime.strptime(original["date"], "%Y-%m-%d").date()
            time_obj = datetime.datetime.strptime(original["time"], "%H:%M").time()
            Appointment.objects.filter(user=self.user, doctor=original["doctor"], date=date_obj, time=time_obj).delete()
        except Exception as e:
            print("Error deleting original appointment:", e)
        res = self.add_appointment(new_appt)
        if res.get("success"):
            alert["resolved"] = True
            alert["new_appointment"] = new_appt
            self.notification_system.send_rescheduling_confirmation(original, new_appt)
            return {"success": True, "message": "Appointment rescheduled.", "new_appointment": new_appt}
        return {"success": False, "message": "Failed to reschedule appointment."}

    def generate_calendar_html(self, doctor_name, date_str):
        available_slots = self.get_available_slots(doctor_name, date_str)
        booked_slots = list(set(TIME_SLOTS) - set(available_slots))
        html = f"""
<div class="calendar-view">
  <h3>Appointment Calendar for {doctor_name} on {date_str}</h3>
  <table class="table table-bordered table-hover">
    <thead class="thead-light">
      <tr>
        <th>Time</th>
        <th>Status</th>
        <th>Weather</th>
      </tr>
    </thead>
    <tbody>
"""
        for slot in TIME_SLOTS:
            forecast = self.weather_system.get_weather_forecast(date_str, slot)
            status = "Available" if slot in available_slots else "Booked"
            row_class = "table-success" if slot in available_slots else "table-danger"
            weather_class = "bg-warning" if forecast.get("is_severe") else ""
            html += f"""
      <tr class="{row_class}">
        <td>{slot}</td>
        <td>{status}</td>
        <td class="{weather_class}">{forecast.get('description', 'Unknown')} {forecast.get('temperature', '')}°C</td>
      </tr>
"""
        html += """
    </tbody>
  </table>
</div>
"""
        return html


# =============================================================================
# MEDIQCHATBOT CLASS
# =============================================================================

class MediqChatbot:
    def __init__(self, user):
        self.user = user
        self.calendar_system = CalendarSystem(user)
        # Prepopulate appointment info from the virtual check‑in (logged‑in user) data.
        self.current_appointment = {
            "patient_name": f"{user.first_name} {user.last_name}",
            "specialty": None,
            "doctor": None,
            "date": None,
            "time": None,
            "reason": None,
            "contact": user.email,
            "insurance": None,
            "symptoms": [],
            "need_human_assistance": False
        }
        self.conversation_history = []  # Store full conversation history
        self.weather_alert_active = False
        self.current_weather_alert = None
        self.confirmation_needed = False
        self.current_state = "initial"
        self.symptom_assessment_mode = False

    def add_to_conversation(self, role, content):
        self.conversation_history.append({"role": role, "content": content})

    def get_ai_response(self, prompt):
        # Update API key
        api_key = "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"
        
        # Add database context
        database_context = {
            "doctors": self.get_doctors_from_database(),
            "user_appointments": self.get_user_appointments()
        }
        
        system_message = {
            "role": "system",
            "content": f"""You are MediqBot, a concise medical appointment assistant with database access. Be direct and brief.

Available doctors from database: {database_context['doctors']}
User's recent appointments: {database_context['user_appointments']}

Keep responses under 2-3 sentences. Focus only on answering the patient's immediate question."""
        }
        
        messages_for_llm = [system_message] + self.conversation_history
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-70b-8192",
            "messages": messages_for_llm,
            "temperature": 0.7,
            "max_tokens": 512
        }
        
        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=data)
            resp.raise_for_status()
            ai_msg = resp.json()["choices"][0]["message"]["content"]
            self.extract_appointment_info(prompt, ai_msg)
            return ai_msg
        except Exception as e:
            return f"Error calling LLM: {str(e)}"

    def extract_appointment_info(self, user_input, ai_response):
        # Update appointment info based on user input and LLM response
        combined_text = f"{user_input} {ai_response}".lower()
        
        # Extract symptoms from user message
        symptoms_mentioned = []
        for symptom in SYMPTOM_TO_SPECIALTY.keys():
            if symptom.lower() in combined_text:
                symptoms_mentioned.append(symptom)
                self.current_appointment["symptoms"].append(symptom)
        
        # If symptoms were mentioned but no specialty is set, recommend a specialty
        if symptoms_mentioned and not self.current_appointment["specialty"]:
            specialty_counts = {}
            for symptom in symptoms_mentioned:
                specialty = SYMPTOM_TO_SPECIALTY.get(symptom)
                if specialty:
                    specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1
            
            # Get the specialty with the most symptoms
            if specialty_counts:
                recommended_specialty = max(specialty_counts.items(), key=lambda x: x[1])[0]
                self.current_appointment["specialty"] = recommended_specialty
        
        # Check for direct specialty mention
        if not self.current_appointment["specialty"]:
            for spec in SPECIALTIES:
                if spec.lower() in combined_text:
                    self.current_appointment["specialty"] = spec
                    break
        
        # Check for doctor mention
        if not self.current_appointment["doctor"]:
            for doc in DOCTORS:
                if doc.lower() in combined_text or (len(doc.split()) > 1 and doc.split()[1].lower() in combined_text):
                    self.current_appointment["doctor"] = doc
                    if not self.current_appointment["specialty"]:
                        self.current_appointment["specialty"] = DOCTORS[doc]["specialty"]
                    break
        
        # Extract date and time information using regex
        date_pattern = r'(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}-\d{1,2}-\d{4})'
        time_pattern = r'(\d{1,2}:\d{2})\s*(am|pm)?'
        
        # Look for dates
        if not self.current_appointment["date"]:
            date_matches = re.findall(date_pattern, combined_text)
            if date_matches:
                try:
                    # Attempt to parse the date
                    date_obj = parser.parse(date_matches[0])
                    self.current_appointment["date"] = date_obj.strftime("%Y-%m-%d")
                except:
                    pass
        
        # Look for times
        if not self.current_appointment["time"]:
            time_matches = re.findall(time_pattern, combined_text, re.IGNORECASE)
            if time_matches:
                try:
                    time_str, meridian = time_matches[0]
                    if meridian and meridian.lower() == 'pm':
                        # Convert to 24-hour format
                        hour, minute = map(int, time_str.split(':'))
                        if hour < 12:
                            hour += 12
                        time_str = f"{hour:02d}:{minute:02d}"
                    self.current_appointment["time"] = time_str
                except:
                    pass
        
        # Check if appointment info is complete
        if self.is_appointment_complete():
            self.confirmation_needed = True

    def is_appointment_complete(self):
        required = ["patient_name", "specialty", "doctor", "date", "time", "contact"]
        return all(self.current_appointment.get(field) for field in required)

    def book_appointment(self):
        if not self.is_appointment_complete():
            return "I still need more information to book your appointment."
        weather_alert = self.calendar_system.weather_system.check_weather_before_appointment(
            self.current_appointment["date"], self.current_appointment["time"], minutes_before=30
        )
        if weather_alert:
            self.weather_alert_active = True
            self.current_weather_alert = weather_alert
            same_day = weather_alert.get("rescheduling_options", {}).get("same_day", [])
            next_day = weather_alert.get("rescheduling_options", {}).get("next_day", {}).get("slots", [])
            return (f"⚠️ WEATHER ALERT ⚠️\n{weather_alert['alert_message']}\n"
                    f"Same-day options: {same_day}\nNext-day options: {next_day}\n"
                    "Would you like to: 1) Reschedule same day, 2) Reschedule next day, 3) Keep original?")
        result = self.calendar_system.add_appointment(self.current_appointment)
        if result.get("success"):
            msg = (f"✅ Appointment Confirmed!\n"
                   f"Your appointment with {self.current_appointment['doctor']} is scheduled for {self.current_appointment['date']} at {self.current_appointment['time']}.")
            self.confirmation_needed = False
            # Reset appointment info while keeping user details prefilled.
            self.current_appointment = {
                "patient_name": self.current_appointment["patient_name"],
                "specialty": None,
                "doctor": None,
                "date": None,
                "time": None,
                "reason": None,
                "contact": self.current_appointment["contact"],
                "insurance": None,
                "symptoms": [],
                "need_human_assistance": False
            }
            return msg
        else:
            return result.get("message", "Unable to book your appointment.")

    def get_doctors_from_database(self):
        """Get real-time doctor information from database"""
        doctors_data = {}
        try:
            for doctor in Doctor.objects.all():
                doctors_data[doctor.name] = {
                    "specialty": doctor.specialty,
                    "id": doctor.id
                }
            return doctors_data
        except Exception as e:
            print(f"Error fetching doctors: {e}")
            return {}

    def get_user_appointments(self):
        """Get current user's appointments"""
        appointments_data = []
        try:
            if self.user:
                for appt in Appointment.objects.filter(user=self.user).order_by('-date', '-time')[:5]:
                    appointments_data.append({
                        "id": appt.id,
                        "doctor": appt.doctor,
                        "date": appt.date.strftime("%Y-%m-%d"),
                        "time": appt.time.strftime("%H:%M")
                    })
            return appointments_data
        except Exception as e:
            print(f"Error fetching appointments: {e}")
            return []

# End of file
