
from agents.coordinator import CoordinatorAgent


class ClinicalCareAgent:
    def __init__(self):
        self.coordinator = CoordinatorAgent()

    def chat(self, user_message, history=None, session_id=None):
        """
        Send a user message to the Coordinator Agent.

        Returns:
            answer: Agent response.
            history: Updated conversation history.
            events: Specialist tool execution records.
            pending_action: Appointment action awaiting confirmation.
        """

        return self.coordinator.ask(
            user_message=user_message,
            history=history,
            session_id=session_id,
        )

    def confirm_action(self, pending_action):
        """
        Execute an appointment action only after explicit confirmation.
        """

        if not pending_action:
            return {
                "success": False,
                "message": "There is no pending appointment action.",
            }

        if pending_action.get("confirmation_required") is not True:
            return {
                "success": False,
                "message": "This action is not awaiting confirmation.",
            }

        return self.coordinator.appointment_agent.execute_confirmed_action(
            pending_action
        )
