
import json
from types import SimpleNamespace

from agents.coordinator import CoordinatorAgent


class FakeMessage:

    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):

        if self.tool_calls:
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments
                        }
                    }
                    for call in self.tool_calls
                ]
            }

        return {
            "role": "assistant",
            "content": self.content
        }


class FakeClient:

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=self.create
            )
        )

    def create(self, **kwargs):

        self.calls.append(kwargs)

        response = self.responses.pop(0)

        return SimpleNamespace(
            choices=[
                SimpleNamespace(message=response)
            ]
        )


def create_coordinator(responses):

    coordinator = CoordinatorAgent.__new__(CoordinatorAgent)

    coordinator.client = FakeClient(responses)

    coordinator.system_prompt = "Test coordinator"

    coordinator.tools = []

    return coordinator


# --------------------------------------------------
# TEST 1: COMPLETE TOOL-CALL LOOP
# --------------------------------------------------

def test_coordinator_completes_tool_call_loop():

    tool_call = SimpleNamespace(
        id="call_test_001",
        function=SimpleNamespace(
            name="appointment_search_doctors",
            arguments=json.dumps({
                "specialty": "Cardiology"
            })
        )
    )

    responses = [
        FakeMessage(
            content=None,
            tool_calls=[tool_call]
        ),
        FakeMessage(
            content="I found Dr. Tashi Dorji, a cardiologist."
        )
    ]

    coordinator = create_coordinator(responses)

    # Replace the specialist with a controlled test response.
    coordinator.appointment_agent = SimpleNamespace(
        find_doctors=lambda specialty=None, doctor_name=None: {
            "success": True,
            "doctors": [
                {
                    "name": "Dr. Tashi Dorji",
                    "specialty": "Cardiology"
                }
            ]
        }
    )

    coordinator.knowledge_agent = SimpleNamespace()

    answer, history, events, pending_action = coordinator.ask(
        user_message="Find a cardiologist.",
        session_id="test-session"
    )

    assert "Dr. Tashi Dorji" in answer

    assert len(events) == 1

    assert events[0]["specialist_tool"] == (
        "appointment_search_doctors"
    )

    assert pending_action is None

    # One request to call the tool and another for the final answer.
    assert len(coordinator.client.calls) == 2

    # The second request should contain the tool result.
    second_messages = coordinator.client.calls[1]["messages"]

    assert any(
        message.get("role") == "tool"
        for message in second_messages
    )


# --------------------------------------------------
# TEST 2: SESSION ID IS REQUIRED
# --------------------------------------------------

def test_coordinator_rejects_missing_session():

    coordinator = create_coordinator([])

    answer, history, events, pending_action = coordinator.ask(
        user_message="Find a doctor.",
        session_id=None
    )

    assert "session" in answer.lower()

    assert events == []

    assert pending_action is None

    # No OpenRouter request should be made.
    assert len(coordinator.client.calls) == 0


# --------------------------------------------------
# TEST 3: API ERROR HANDLING
# --------------------------------------------------

def test_coordinator_handles_api_error():

    coordinator = create_coordinator([])

    def raise_error(**kwargs):
        raise RuntimeError("Simulated API error")

    coordinator.client.chat.completions.create = raise_error

    answer, history, events, pending_action = coordinator.ask(
        user_message="Find a doctor.",
        session_id="test-session"
    )

    assert "trouble connecting" in answer.lower()

    assert events == []

    assert pending_action is None
