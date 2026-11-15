
from tools import (
    search_doctors,
    check_availability,
    get_appointments,
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
)


class AppointmentAgent:
    """
    Specialist agent responsible for appointment operations.

    It prepares appointment actions and requires explicit
    confirmation before performing database changes.
    """

    def __init__(self):
        self.name = "Appointment Specialist"

    # --------------------------------------------------
    # 1. Search doctors
    # --------------------------------------------------

    def find_doctors(self, specialty=None, doctor_name=None):
        return search_doctors(
            specialty=specialty,
            doctor_name=doctor_name
        )

    # --------------------------------------------------
    # 2. Check availability
    # --------------------------------------------------

    def find_available_slots(self, doctor_name, appointment_date):
        return check_availability(
            doctor_name,
            appointment_date
        )

    # --------------------------------------------------
    # 3. View appointments
    # --------------------------------------------------

    def view_appointments(self, session_id=None):
        return get_appointments(session_id=session_id)

    # --------------------------------------------------
    # 4. Prepare a booking
    # --------------------------------------------------

    def prepare_booking(
        self,
        patient_name,
        doctor_name,
        appointment_date,
        appointment_time,
        reason="",
        session_id=None
    ):
        return {
            "action": "book_appointment",
            "details": {
                "patient_name": patient_name,
                "doctor_name": doctor_name,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "reason": reason,
                "session_id": session_id
            },
            "confirmation_required": True,
            "message": "Please review the appointment details and confirm before booking."
        }

    # --------------------------------------------------
    # 5. Prepare cancellation
    # --------------------------------------------------

    def prepare_cancellation(self, appointment_id, session_id=None):
        appointments = self.view_appointments(session_id)

        appointment = next(
            (
                item for item in appointments
                if item["appointment_id"] == appointment_id
            ),
            None
        )

        if not appointment:
            return {
                "success": False,
                "message": "Appointment not found in this session."
            }

        if appointment["status"] != "booked":
            return {
                "success": False,
                "message": "Only active appointments can be cancelled."
            }

        return {
            "action": "cancel_appointment",
            "details": {
                "appointment_id": appointment_id,
                "session_id": session_id
            },
            "appointment": appointment,
            "confirmation_required": True,
            "message": "Please confirm cancellation of this appointment."
        }

    # --------------------------------------------------
    # 6. Prepare rescheduling
    # --------------------------------------------------

    def prepare_rescheduling(
        self,
        appointment_id,
        new_date,
        new_time,
        session_id=None
    ):
        appointments = self.view_appointments(session_id)

        appointment = next(
            (
                item for item in appointments
                if item["appointment_id"] == appointment_id
            ),
            None
        )

        if not appointment:
            return {
                "success": False,
                "message": "Appointment not found in this session."
            }

        if appointment["status"] != "booked":
            return {
                "success": False,
                "message": "Only active appointments can be rescheduled."
            }

        # Check whether the requested time is valid and available.
        availability = self.find_available_slots(
            appointment["doctor"],
            new_date
        )

        if not availability["success"]:
            return availability

        if new_time not in availability["available_slots"]:
            return {
                "success": False,
                "message": "The requested new appointment slot is unavailable."
            }

        return {
            "action": "reschedule_appointment",
            "details": {
                "appointment_id": appointment_id,
                "new_date": new_date,
                "new_time": new_time,
                "session_id": session_id
            },
            "appointment": appointment,
            "confirmation_required": True,
            "message": "Please review and confirm the proposed rescheduling."
        }

    # --------------------------------------------------
    # 7. Execute a confirmed action
    # --------------------------------------------------

    def execute_confirmed_action(self, pending_action):
        """
        Execute only an action that has been explicitly
        confirmed by the user through the application.
        """

        if not pending_action:
            return {
                "success": False,
                "message": "No pending action was provided."
            }

        action = pending_action.get("action")
        details = pending_action.get("details", {})

        if action == "book_appointment":
            return book_appointment(**details)

        if action == "cancel_appointment":
            return cancel_appointment(**details)

        if action == "reschedule_appointment":
            return reschedule_appointment(**details)

        return {
            "success": False,
            "message": "Unknown appointment action."
        }
