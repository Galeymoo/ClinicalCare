from datetime import date, time, datetime, timezone

from sqlalchemy import and_

from database import (
    SessionLocal,
    Doctor,
    Appointment,
)


# Available appointment times
AVAILABLE_SLOTS = [
    "09:00",
    "10:00",
    "11:00",
    "14:00",
    "15:00",
    "16:00",
]


# Common specialty names and their database equivalents
SPECIALTY_ALIASES = {
    "cardiologist": "Cardiology",
    "cardiologists": "Cardiology",
    "cardiology": "Cardiology",

    "dermatologist": "Dermatology",
    "dermatologists": "Dermatology",
    "dermatology": "Dermatology",

    "paediatrician": "Paediatrics",
    "paediatricians": "Paediatrics",
    "pediatrician": "Paediatrics",
    "pediatricians": "Paediatrics",
    "paediatrics": "Paediatrics",
    "pediatrics": "Paediatrics",

    "general physician": "General Medicine",
    "general doctor": "General Medicine",
    "general medicine": "General Medicine",
}


# --------------------------------------------------
# 1. Search doctors
# --------------------------------------------------

def search_doctors(specialty=None, doctor_name=None):
    """Find doctors by specialty or name."""

    with SessionLocal() as db:
        query = db.query(Doctor).filter(Doctor.is_active == 1)

        if specialty:
            cleaned_specialty = specialty.strip().lower()

            # Convert common doctor titles into database specialties.
            normalized_specialty = SPECIALTY_ALIASES.get(
                cleaned_specialty,
                specialty.strip()
            )

            query = query.filter(
                Doctor.specialty.ilike(f"%{normalized_specialty}%")
            )

        if doctor_name:
            query = query.filter(
                Doctor.name.ilike(f"%{doctor_name.strip()}%")
            )

        doctors = query.all()

        return [
            {
                "doctor_id": doctor.id,
                "name": doctor.name,
                "specialty": doctor.specialty,
            }
            for doctor in doctors
        ]


# --------------------------------------------------
# 2. Check appointment availability
# --------------------------------------------------

def check_availability(doctor_name, appointment_date):
    """Check available slots for a particular doctor."""

    try:
        selected_date = date.fromisoformat(appointment_date)
    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Invalid date format. Use YYYY-MM-DD."
        }

    if selected_date < date.today():
        return {
            "success": False,
            "message": "Appointments cannot be checked for past dates."
        }

    with SessionLocal() as db:
        doctor = db.query(Doctor).filter(
            Doctor.name.ilike(f"%{doctor_name}%"),
            Doctor.is_active == 1
        ).first()

        if not doctor:
            return {
                "success": False,
                "message": "Doctor not found."
            }

        booked_appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date == selected_date,
            Appointment.status == "booked"
        ).all()

        booked_times = {
            appointment.appointment_time.strftime("%H:%M")
            for appointment in booked_appointments
        }

        available = [
            slot for slot in AVAILABLE_SLOTS
            if slot not in booked_times
        ]

        return {
            "success": True,
            "doctor": doctor.name,
            "specialty": doctor.specialty,
            "date": appointment_date,
            "available_slots": available,
            "message": (
                "Available appointment slots retrieved."
                if available
                else "No available slots for this date."
            )
        }


# --------------------------------------------------
# 3. Book appointment
# --------------------------------------------------

def book_appointment(
    patient_name,
    doctor_name,
    appointment_date,
    appointment_time,
    reason="",
    session_id=None
):
    """Create an appointment after confirmation."""

    try:
        selected_date = date.fromisoformat(appointment_date)
        selected_time = time.fromisoformat(appointment_time)
    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Invalid date or time format."
        }

    if selected_date < date.today():
        return {
            "success": False,
            "message": "Cannot book an appointment in the past."
        }

    if appointment_time not in AVAILABLE_SLOTS:
        return {
            "success": False,
            "message": "This appointment time is not offered by the clinic."
        }

    if not patient_name or not patient_name.strip():
        return {
            "success": False,
            "message": "Patient name is required."
        }

    if not doctor_name or not doctor_name.strip():
        return {
            "success": False,
            "message": "Doctor name is required."
        }

    with SessionLocal() as db:
        doctor = db.query(Doctor).filter(
            Doctor.name.ilike(f"%{doctor_name}%"),
            Doctor.is_active == 1
        ).first()

        if not doctor:
            return {
                "success": False,
                "message": "Doctor not found."
            }

        existing = db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date == selected_date,
            Appointment.appointment_time == selected_time,
            Appointment.status == "booked"
        ).first()

        if existing:
            return {
                "success": False,
                "message": "This appointment slot is already booked."
            }

        appointment = Appointment(
            patient_name=patient_name.strip(),
            doctor_id=doctor.id,
            appointment_date=selected_date,
            appointment_time=selected_time,
            reason=reason,
            status="booked",
            session_id=session_id
        )

        try:
            db.add(appointment)
            db.commit()
            db.refresh(appointment)

            return {
                "success": True,
                "appointment_id": appointment.id,
                "patient_name": appointment.patient_name,
                "doctor": doctor.name,
                "date": str(appointment.appointment_date),
                "time": appointment.appointment_time.strftime("%H:%M"),
                "message": "Appointment booked successfully."
            }

        except Exception:
            db.rollback()

            return {
                "success": False,
                "message": (
                    "This slot may have just been booked. "
                    "Please check availability again."
                )
            }


# --------------------------------------------------
# 4. View appointments
# --------------------------------------------------

def get_appointments(session_id=None):
    """Retrieve appointments."""

    with SessionLocal() as db:
        query = db.query(Appointment, Doctor).join(
            Doctor,
            Appointment.doctor_id == Doctor.id
        )

        if session_id:
            query = query.filter(
                Appointment.session_id == session_id
            )

        appointments = query.order_by(
            Appointment.appointment_date,
            Appointment.appointment_time
        ).all()

        return [
            {
                "appointment_id": appointment.id,
                "patient_name": appointment.patient_name,
                "doctor": doctor.name,
                "specialty": doctor.specialty,
                "date": str(appointment.appointment_date),
                "time": appointment.appointment_time.strftime("%H:%M"),
                "status": appointment.status,
            }
            for appointment, doctor in appointments
        ]


# --------------------------------------------------
# 5. Cancel appointment
# --------------------------------------------------

def cancel_appointment(appointment_id, session_id=None):
    """Cancel an existing appointment."""

    with SessionLocal() as db:
        query = db.query(Appointment).filter(
            Appointment.id == appointment_id
        )

        if session_id:
            query = query.filter(
                Appointment.session_id == session_id
            )

        appointment = query.first()

        if not appointment:
            return {
                "success": False,
                "message": "Appointment not found."
            }

        if appointment.status != "booked":
            return {
                "success": False,
                "message": "This appointment is not active."
            }

        appointment.status = "cancelled"
        db.commit()

        return {
            "success": True,
            "appointment_id": appointment.id,
            "message": "Appointment cancelled successfully."
        }


# --------------------------------------------------
# 6. Reschedule appointment
# --------------------------------------------------

def reschedule_appointment(
    appointment_id,
    new_date,
    new_time,
    session_id=None
):
    """Move an existing appointment to another available slot."""

    try:
        selected_date = date.fromisoformat(new_date)
        selected_time = time.fromisoformat(new_time)
    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Invalid date or time format."
        }

    if selected_date < date.today():
        return {
            "success": False,
            "message": "Cannot reschedule to a past date."
        }

    if new_time not in AVAILABLE_SLOTS:
        return {
            "success": False,
            "message": "This appointment time is not offered by the clinic."
        }

    with SessionLocal() as db:
        query = db.query(Appointment).filter(
            Appointment.id == appointment_id
        )

        if session_id:
            query = query.filter(
                Appointment.session_id == session_id
            )

        appointment = query.first()

        if not appointment:
            return {
                "success": False,
                "message": "Appointment not found."
            }

        if appointment.status != "booked":
            return {
                "success": False,
                "message": "Only active appointments can be rescheduled."
            }

        existing = db.query(Appointment).filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.appointment_date == selected_date,
            Appointment.appointment_time == selected_time,
            Appointment.status == "booked",
            Appointment.id != appointment.id
        ).first()

        if existing:
            return {
                "success": False,
                "message": "The requested slot is already booked."
            }

        appointment.appointment_date = selected_date
        appointment.appointment_time = selected_time
        appointment.updated_at = datetime.now(timezone.utc)

        try:
            db.commit()

            return {
                "success": True,
                "appointment_id": appointment.id,
                "new_date": new_date,
                "new_time": new_time,
                "message": "Appointment rescheduled successfully."
            }

        except Exception:
            db.rollback()

            return {
                "success": False,
                "message": (
                    "The requested slot may have just been booked. "
                    "Please check availability again."
                )
            }