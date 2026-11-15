
import json

from openai import OpenAI

from config import (
    OPENROUTER_BASE_URL,
    MODEL_NAME,
    MAX_AGENT_STEPS,
    get_api_key,
)

from agents.appointment_agent import AppointmentAgent
from agents.knowledge_agent import KnowledgeAgent


class CoordinatorAgent:

    def __init__(self):

        api_key = get_api_key()

        if not api_key:
            raise ValueError(
                "OpenRouter API key was not found. "
                "Please check .streamlit/secrets.toml."
            )

        self.client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
            default_headers={"X-Title": "ClinicalCare"},
        )

        self.appointment_agent = AppointmentAgent()
        self.knowledge_agent = KnowledgeAgent()

        # Stores the latest API error for evaluation.
        self.last_error = None

        # --------------------------------------------------
        # COORDINATOR SYSTEM PROMPT
        # --------------------------------------------------

        self.system_prompt = """
You are the Coordinator Agent for ClinicalCare, a simulated
clinic appointment assistant developed for an academic project.

Your responsibility is to understand the user's request and
delegate it to the correct specialist agent.

SPECIALISTS:

1. Appointment Specialist:
Use appointment tools for:
- Finding doctors and their specialties.
- Checking appointment availability.
- Viewing the user's appointments.
- Preparing appointment bookings.
- Preparing appointment cancellations.
- Preparing appointment rescheduling.

2. Knowledge Specialist:
Use the knowledge tool for:
- Clinic information.
- Appointment policies.
- Frequently asked questions.
- Cancellation and rescheduling rules.
- Other information contained in the clinic knowledge base.

IMPORTANT RULES:

- Use the appropriate specialist tool instead of inventing information.
- Ask the user for missing information when necessary.
- Check availability before preparing a booking.
- Only prepare cancellation or rescheduling for an existing
  active appointment belonging to the current session.
- Never execute a booking, cancellation, or rescheduling yourself.
- The application requires explicit user confirmation before
  any appointment change is executed.
- Do not claim an appointment has been booked, cancelled,
  or rescheduled just because an action was prepared.
- Only report a completed appointment change when the application
  confirms that the database operation succeeded.
- Do not provide medical diagnosis, treatment, or medication advice.
- If the user describes an emergency or serious urgent symptoms,
  advise them to seek immediate medical help from local emergency
  services or the nearest appropriate healthcare facility.
- Do not request unnecessary sensitive medical information.
- The clinic and all doctors are fictional demonstration data.
- Be polite, clear, concise, and helpful.

BOOKING WORKFLOW:

- The required booking details are patient name, doctor name,
  appointment date, and appointment time.
- The appointment reason is optional.
- Never ask for the appointment reason as a condition for
  preparing a booking.
- If the user has already provided the patient name,
  do not ask them to confirm it again.
- When the user explicitly asks to prepare a booking and
  all required details are available, first check availability.
- If the requested slot is available, immediately call
  appointment_prepare_booking.
- Do not stop after checking availability when the user has
  already requested booking preparation.
- After preparing the booking, explain that explicit
  confirmation is required before it is saved.

KNOWLEDGE WORKFLOW:

- Use knowledge_answer_question for questions about clinic
  information and policies.
- Do not call the same knowledge tool repeatedly with the
  same question during one user request.
- Use the retrieved information to prepare one clear answer.
- Do not invent clinic policies when retrieval finds no
  sufficiently relevant information.
"""

        # --------------------------------------------------
        # SPECIALIST TOOL DEFINITIONS
        # --------------------------------------------------

        self.tools = [

            {
                "type": "function",
                "function": {
                    "name": "appointment_search_doctors",
                    "description": (
                        "Delegate to the Appointment Specialist to "
                        "find doctors by specialty or name."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "specialty": {
                                "type": "string",
                                "description": "Doctor specialty, if known."
                            },
                            "doctor_name": {
                                "type": "string",
                                "description": "Doctor name, if known."
                            },
                        },
                        "required": [],
                    },
                },
            },

            {
                "type": "function",
                "function": {
                    "name": "appointment_check_availability",
                    "description": (
                        "Delegate to the Appointment Specialist to "
                        "check available appointment slots."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doctor_name": {
                                "type": "string"
                            },
                            "appointment_date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format."
                            },
                        },
                        "required": [
                            "doctor_name",
                            "appointment_date",
                        ],
                    },
                },
            },

            {
                "type": "function",
                "function": {
                    "name": "appointment_view",
                    "description": (
                        "Delegate to the Appointment Specialist to "
                        "view appointments belonging to this session."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },

            {
                "type": "function",
                "function": {
                    "name": "appointment_prepare_booking",
                    "description": (
                        "Prepare an appointment booking after availability "
                        "has been checked. Required details are patient "
                        "name, doctor name, date and time. Reason is "
                        "optional. If the user has provided all required "
                        "details and requested booking preparation, call "
                        "this tool immediately. This does not complete "
                        "the booking; user confirmation is still required."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "patient_name": {
                                "type": "string"
                            },
                            "doctor_name": {
                                "type": "string"
                            },
                            "appointment_date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format."
                            },
                            "appointment_time": {
                                "type": "string",
                                "description": "Time in HH:MM format."
                            },
                            "reason": {
                                "type": "string",
                                "description": "Optional appointment reason."
                            },
                        },
                        "required": [
                            "patient_name",
                            "doctor_name",
                            "appointment_date",
                            "appointment_time",
                        ],
                    },
                },
            },

            {
                "type": "function",
                "function": {
                    "name": "appointment_prepare_cancellation",
                    "description": (
                        "Prepare cancellation of an existing active "
                        "appointment. Does not cancel it."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_id": {
                                "type": "integer"
                            },
                        },
                        "required": ["appointment_id"],
                    },
                },
            },

            {
                "type": "function",
                "function": {
                    "name": "appointment_prepare_rescheduling",
                    "description": (
                        "Prepare rescheduling of an existing active "
                        "appointment after checking the new slot. "
                        "Does not reschedule it."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_id": {
                                "type": "integer"
                            },
                            "new_date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format."
                            },
                            "new_time": {
                                "type": "string",
                                "description": "Time in HH:MM format."
                            },
                        },
                        "required": [
                            "appointment_id",
                            "new_date",
                            "new_time",
                        ],
                    },
                },
            },

            {
                "type": "function",
                "function": {
                    "name": "knowledge_answer_question",
                    "description": (
                        "Delegate to the Knowledge Specialist to "
                        "retrieve answers from the clinic knowledge base. "
                        "Call this tool once for a question and use "
                        "the retrieved information to answer."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string"
                            },
                        },
                        "required": ["question"],
                    },
                },
            },
        ]

    # --------------------------------------------------
    # SPECIALIST DELEGATION
    # --------------------------------------------------

    def execute_specialist_tool(
        self,
        tool_name,
        arguments,
        session_id
    ):
        """
        Execute a request through the appropriate specialist.
        Appointment changes are prepared, not directly executed.
        """

        if tool_name == "appointment_search_doctors":

            return self.appointment_agent.find_doctors(
                specialty=arguments.get("specialty"),
                doctor_name=arguments.get("doctor_name"),
            )

        if tool_name == "appointment_check_availability":

            return self.appointment_agent.find_available_slots(
                doctor_name=arguments["doctor_name"],
                appointment_date=arguments["appointment_date"],
            )

        if tool_name == "appointment_view":

            return self.appointment_agent.view_appointments(
                session_id=session_id
            )

        if tool_name == "appointment_prepare_booking":

            # First check appointment availability.
            availability = self.appointment_agent.find_available_slots(
                doctor_name=arguments["doctor_name"],
                appointment_date=arguments["appointment_date"],
            )

            if not availability.get("success"):
                return availability

            requested_time = arguments["appointment_time"]

            if requested_time not in availability.get(
                "available_slots", []
            ):

                return {
                    "success": False,
                    "message": (
                        "That time slot is not available. "
                        "Please choose one of the available slots."
                    ),
                    "available_slots": availability.get(
                        "available_slots", []
                    ),
                }

            # Prepare booking without executing it.
            result = self.appointment_agent.prepare_booking(
                patient_name=arguments["patient_name"],
                doctor_name=arguments["doctor_name"],
                appointment_date=arguments["appointment_date"],
                appointment_time=requested_time,
                reason=arguments.get("reason", ""),
                session_id=session_id,
            )

            return result

        if tool_name == "appointment_prepare_cancellation":

            return self.appointment_agent.prepare_cancellation(
                appointment_id=arguments["appointment_id"],
                session_id=session_id,
            )

        if tool_name == "appointment_prepare_rescheduling":

            return self.appointment_agent.prepare_rescheduling(
                appointment_id=arguments["appointment_id"],
                new_date=arguments["new_date"],
                new_time=arguments["new_time"],
                session_id=session_id,
            )

        if tool_name == "knowledge_answer_question":

            return self.knowledge_agent.answer_question(
                arguments["question"]
            )

        return {
            "success": False,
            "message": "Unknown specialist tool requested.",
        }

    # --------------------------------------------------
    # COORDINATOR AGENT LOOP
    # --------------------------------------------------

    def ask(self, user_message, history=None, session_id=None):
        """
        Run the Coordinator Agent's reasoning and delegation loop.

        Returns:
            answer: Final response for the user.
            history: Updated conversation history.
            events: Specialist delegation and tool execution records.
            pending_action: Appointment action awaiting confirmation.
        """

        # Reset error information for each new request.
        self.last_error = None

        if not user_message or not user_message.strip():

            return (
                "Please enter a message.",
                history or [],
                [],
                None,
            )

        if not session_id:

            return (
                "The session could not be identified. Please refresh the app.",
                history or [],
                [],
                None,
            )

        if history is None:
            history = []

        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

        messages.extend(history[-10:])

        messages.append({
            "role": "user",
            "content": user_message,
        })

        events = []
        pending_action = None

        # Cache results of identical tool calls within this request.
        executed_tools = {}

        try:

            for step in range(MAX_AGENT_STEPS):

                response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0.2,
                    max_tokens=600,
                )

                assistant_message = response.choices[0].message

                messages.append(
                    assistant_message.model_dump(exclude_none=True)
                )

                # Check whether the model has completed its response.
                if not assistant_message.tool_calls:

                    answer = assistant_message.content or (
                        "I could not generate a response. "
                        "Please try again."
                    )

                    updated_history = messages[1:]

                    return (
                        answer,
                        updated_history,
                        events,
                        pending_action,
                    )

                # Execute requested specialist tools.
                for tool_call in assistant_message.tool_calls:

                    tool_name = tool_call.function.name
                    is_duplicate = False

                    try:

                        arguments = json.loads(
                            tool_call.function.arguments or "{}"
                        )

                        # Create a consistent key for this tool request.
                        tool_key = (
                            tool_name,
                            json.dumps(arguments, sort_keys=True),
                        )

                        # Reuse a result if the same tool request
                        # was already executed during this request.
                        if tool_key in executed_tools:

                            result = executed_tools[tool_key]
                            is_duplicate = True

                        else:

                            result = self.execute_specialist_tool(
                                tool_name=tool_name,
                                arguments=arguments,
                                session_id=session_id,
                            )

                            executed_tools[tool_key] = result

                    except (ValueError, KeyError, TypeError):

                        result = {
                            "success": False,
                            "message": (
                                "The request could not be processed. "
                                "Please check the information and try again."
                            ),
                        }

                    except Exception:

                        result = {
                            "success": False,
                            "message": (
                                "An error occurred while processing "
                                "the request. Please try again."
                            ),
                        }

                    # Store actions awaiting confirmation.
                    if (
                        isinstance(result, dict)
                        and result.get("confirmation_required") is True
                    ):

                        pending_action = result

                    # Record only actual specialist executions.
                    if not is_duplicate:

                        events.append({
                            "specialist_tool": tool_name,
                            "result": result,
                        })

                    # Send tool result back to the model.
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            result,
                            default=str,
                        ),
                    })

            return (
                "I reached the maximum number of processing steps. "
                "Please try asking in a simpler way.",
                messages[1:],
                events,
                pending_action,
            )

        except Exception as error:

            # ------------------------------------------
            # API ERROR CLASSIFICATION
            # ------------------------------------------

            status_code = getattr(error, "status_code", None)

            if status_code == 429:

                error_category = "api_rate_limit"

            elif status_code in (401, 403):

                error_category = "api_authentication"

            elif status_code is not None:

                error_category = "api_error"

            elif type(error).__name__ in (
                "APIConnectionError",
                "APITimeoutError",
            ):

                error_category = "api_connection"

            else:

                error_category = "api_error"

            # Save error information for evaluation.
            self.last_error = {
                "category": error_category,
                "status_code": status_code,
                "error_type": type(error).__name__,
            }

            print(
                "Coordinator Agent error:",
                error_category,
                status_code,
            )

            return (
                "I'm having trouble connecting to the AI service. "
                "Please try again in a moment.",
                history,
                events,
                pending_action,
            )
