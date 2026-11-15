
import json
from types import SimpleNamespace

from agents.coordinator import CoordinatorAgent
from agent import ClinicalCareAgent


# --------------------------------------------------
# FAKE SPECIALIST AGENTS
# --------------------------------------------------

class FakeAppointmentAgent:

    def __init__(self):
        self.calls = []

    def find_doctors(self, specialty=None, doctor_name=None):
        self.calls.append("find_doctors")

        return {
            "success": True,
            "doctors": [
                {"name": "Dr. Tashi Dorji", "specialty": "Cardiology"}
            ]
        }

    def find_available_slots(self, doctor_name, appointment_date):
        self.calls.append("check_availability")

        return {
            "success": True,
            "available_slots": ["09:00", "10:00", "11:00"]
        }

    def prepare_booking(
        self,
        patient_name,
        doctor_name,
        appointment_date,
        appointment_time,
        reason="",
        session_id=None
    ):
        self.calls.append("prepare_booking")

        return {
            "success": True,
            "confirmation_required": True,
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "session_id": session_id
        }

    def execute_confirmed_action(self, pending_action):
        self.calls.append("execute_confirmed_action")

        return {
            "success": True,
            "message": "Appointment action executed."
        }


class FakeKnowledgeAgent:

    def answer_question(self, question):
        return {
            "success": True,
            "question": question,
            "grounded": True,
            "sources": ["clinic_faq.md"]
        }


# --------------------------------------------------
# TEST FIXTURE
# --------------------------------------------------

def create_coordinator():

    coordinator = CoordinatorAgent.__new__(CoordinatorAgent)

    coordinator.appointment_agent = FakeAppointmentAgent()
    coordinator.knowledge_agent = FakeKnowledgeAgent()

    return coordinator


# --------------------------------------------------
# TEST 1: DOCTOR SEARCH DELEGATION
# --------------------------------------------------

def test_coordinator_delegates_doctor_search():

    coordinator = create_coordinator()

    result = coordinator.execute_specialist_tool(
        tool_name="appointment_search_doctors",
        arguments={"specialty": "Cardiology"},
        session_id="test-session"
    )

    assert result["success"] is True

    assert coordinator.appointment_agent.calls == [
        "find_doctors"
    ]


# --------------------------------------------------
# TEST 2: KNOWLEDGE SPECIALIST DELEGATION
# --------------------------------------------------

def test_coordinator_delegates_knowledge_question():

    coordinator = create_coordinator()

    result = coordinator.execute_specialist_tool(
        tool_name="knowledge_answer_question",
        arguments={
            "question": "Can I cancel my appointment?"
        },
        session_id="test-session"
    )

    assert result["success"] is True
    assert result["grounded"] is True
    assert result["sources"] == ["clinic_faq.md"]


# --------------------------------------------------
# TEST 3: AVAILABILITY BEFORE BOOKING
# --------------------------------------------------

def test_booking_checks_availability_before_preparation():

    coordinator = create_coordinator()

    result = coordinator.execute_specialist_tool(
        tool_name="appointment_prepare_booking",
        arguments={
            "patient_name": "Test Patient",
            "doctor_name": "Dr. Tashi Dorji",
            "appointment_date": "2026-11-20",
            "appointment_time": "10:00",
            "reason": "General consultation"
        },
        session_id="test-session"
    )

    assert result["success"] is True
    assert result["confirmation_required"] is True

    assert coordinator.appointment_agent.calls == [
        "check_availability",
        "prepare_booking"
    ]


# --------------------------------------------------
# TEST 4: UNAVAILABLE SLOT IS NOT PREPARED
# --------------------------------------------------

def test_booking_rejects_unavailable_slot():

    coordinator = create_coordinator()

    result = coordinator.execute_specialist_tool(
        tool_name="appointment_prepare_booking",
        arguments={
            "patient_name": "Test Patient",
            "doctor_name": "Dr. Tashi Dorji",
            "appointment_date": "2026-11-20",
            "appointment_time": "16:00"
        },
        session_id="test-session"
    )

    assert result["success"] is False

    assert "prepare_booking" not in (
        coordinator.appointment_agent.calls
    )


# --------------------------------------------------
# TEST 5: UNKNOWN TOOL IS REJECTED
# --------------------------------------------------

def test_unknown_tool_is_rejected():

    coordinator = create_coordinator()

    result = coordinator.execute_specialist_tool(
        tool_name="unknown_tool",
        arguments={},
        session_id="test-session"
    )

    assert result["success"] is False


# --------------------------------------------------
# TEST 6: CONFIRMATION REQUIRED
# --------------------------------------------------

def test_agent_rejects_missing_confirmation():

    agent = ClinicalCareAgent.__new__(ClinicalCareAgent)
    coordinator = create_coordinator()

    agent.coordinator = coordinator

    result = agent.confirm_action(None)

    assert result["success"] is False

    assert "execute_confirmed_action" not in (
        coordinator.appointment_agent.calls
    )


# --------------------------------------------------
# TEST 7: INVALID ACTION IS REJECTED
# --------------------------------------------------

def test_agent_rejects_action_without_confirmation_flag():

    agent = ClinicalCareAgent.__new__(ClinicalCareAgent)
    coordinator = create_coordinator()

    agent.coordinator = coordinator

    result = agent.confirm_action({
        "confirmation_required": False
    })

    assert result["success"] is False

    assert "execute_confirmed_action" not in (
        coordinator.appointment_agent.calls
    )


# --------------------------------------------------
# TEST 8: CONFIRMED ACTION IS EXECUTED
# --------------------------------------------------

def test_agent_executes_confirmed_action():

    agent = ClinicalCareAgent.__new__(ClinicalCareAgent)
    coordinator = create_coordinator()

    agent.coordinator = coordinator

    pending_action = {
        "confirmation_required": True,
        "action": "book"
    }

    result = agent.confirm_action(pending_action)

    assert result["success"] is True

    assert "execute_confirmed_action" in (
        coordinator.appointment_agent.calls
    )
