
import uuid
import streamlit as st
import database

from agent import ClinicalCareAgent
from database import SessionLocal, Feedback
from tools import search_doctors, get_appointments


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="ClinicalCare | Appointment Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

database.init_db()


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! Welcome to ClinicalCare. "
                "I'm your appointment assistant. "
                "I can help you find doctors, check availability, "
                "book appointments, and answer clinic questions. "
                "How can I help you today?"
            ),
        }
    ]

if "agent_history" not in st.session_state:
    st.session_state.agent_history = []

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

# Store specialist activity for the latest request.
if "last_events" not in st.session_state:
    st.session_state.last_events = []

if "agent" not in st.session_state:
    try:
        st.session_state.agent = ClinicalCareAgent()
    except Exception as error:
        st.session_state.agent = None
        st.session_state.agent_error = str(error)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def display_action_details(action):
    """Display appointment details before confirmation."""

    st.write("Please review the following details:")

    st.json(action)


def get_action_title(action):
    """Return a readable appointment action name."""

    action_type = action.get("action", "")

    titles = {
        "book_appointment": "Appointment Booking",
        "cancel_appointment": "Appointment Cancellation",
        "reschedule_appointment": "Appointment Rescheduling",
    }

    return titles.get(action_type, "Appointment Action")


def save_feedback(rating, comment, category):
    """Save user feedback in the database."""

    with SessionLocal() as db:
        feedback = Feedback(
            rating=rating,
            comment=comment,
            category=category,
        )

        db.add(feedback)
        db.commit()


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.title("🩺 ClinicalCare")

    st.caption("AI-Based Clinical Appointment Assistant")

    st.divider()

    st.markdown("### About ClinicalCare")

    st.write(
        "ClinicalCare is an academic demonstration project "
        "that uses AI agents to assist with appointment-related "
        "tasks and clinic information."
    )

    st.divider()

    st.markdown("### Available Services")

    st.write("🔎 Find doctors")
    st.write("📅 Check appointment availability")
    st.write("📝 Book appointments")
    st.write("❌ Cancel appointments")
    st.write("🔄 Reschedule appointments")
    st.write("📚 Ask clinic-related questions")

    st.divider()

    st.warning(
        "ClinicalCare is a simulated clinic. "
        "All doctors and appointment information are fictional. "
        "This application does not provide medical advice."
    )

    if st.button("Clear Conversation", use_container_width=True):

        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! Welcome to ClinicalCare. "
                    "How can I help you today?"
                ),
            }
        ]

        st.session_state.agent_history = []
        st.session_state.pending_action = None
        st.session_state.last_events = []

        st.rerun()


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.title("🩺 ClinicalCare")
st.write("Your AI Appointment Assistant")

st.caption(
    "Find doctors, check available slots, manage appointments, "
    "and get answers to clinic-related questions."
)

st.divider()


# --------------------------------------------------
# CHECK AGENT CONNECTION
# --------------------------------------------------

if st.session_state.agent is None:

    st.error(
        "The AI agent could not be initialized. "
        "Please check your OpenRouter API key in "
        ".streamlit/secrets.toml."
    )

    if "agent_error" in st.session_state:

        with st.expander("Technical error"):
            st.code(st.session_state.agent_error)

    st.stop()


# --------------------------------------------------
# APPLICATION TABS
# --------------------------------------------------

chat_tab, doctors_tab, appointments_tab, feedback_tab = st.tabs(
    [
        "💬 Chat Assistant",
        "👨‍⚕️ Doctors",
        "📅 My Appointments",
        "⭐ Feedback",
    ]
)


# --------------------------------------------------
# CHAT ASSISTANT
# --------------------------------------------------

with chat_tab:

    st.subheader("Chat with ClinicalCare")

    # Display previous messages.
    for message in st.session_state.chat_messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    # --------------------------------------------------
    # PENDING APPOINTMENT ACTION
    # --------------------------------------------------

    pending_action = st.session_state.pending_action

    if pending_action:

        st.divider()

        st.warning(
            "An appointment action is waiting for your confirmation."
        )

        st.subheader(get_action_title(pending_action))

        display_action_details(pending_action)

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Confirm Action",
                type="primary",
                use_container_width=True,
            ):

                # Remove the pending action before execution to
                # prevent repeated submission during reruns.
                st.session_state.pending_action = None

                with st.spinner("Processing your confirmation..."):

                    result = st.session_state.agent.confirm_action(
                        pending_action
                    )

                if result.get("success"):

                    confirmation_message = result.get(
                        "message",
                        "The appointment action was completed successfully."
                    )

                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": "✅ " + confirmation_message,
                    })

                    # Inform the Coordinator about the completed action.
                    st.session_state.agent_history.append({
                        "role": "user",
                        "content": (
                            "System update: The user explicitly confirmed "
                            "the pending appointment action. The database "
                            "returned this result: "
                            + str(result)
                        ),
                    })

                    st.success(confirmation_message)

                else:

                    error_message = result.get(
                        "message",
                        "The appointment action could not be completed."
                    )

                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": "❌ " + error_message,
                    })

                    st.error(error_message)

                st.rerun()


        with col2:

            if st.button(
                "Don't Proceed",
                use_container_width=True,
            ):

                st.session_state.pending_action = None

                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": (
                        "No appointment changes were made. "
                        "Let me know if you need anything else."
                    ),
                })

                st.rerun()


    # --------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------

    user_message = st.chat_input(
        "Ask me about doctors or appointments..."
    )

    if user_message:

        if st.session_state.pending_action:

            st.warning(
                "Please confirm or decline the pending appointment "
                "action before starting another request."
            )

        else:

            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_message,
            })

            # Clear previous activity before processing a new request.
            st.session_state.last_events = []

            with st.spinner("ClinicalCare is thinking..."):

                answer, history, events, pending = (
                    st.session_state.agent.chat(
                        user_message=user_message,
                        history=st.session_state.agent_history,
                        session_id=st.session_state.session_id,
                    )
                )

            st.session_state.agent_history = history

            st.session_state.pending_action = pending

            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": answer,
            })

            # Store only the activity from the current request.
            st.session_state.last_events = events or []

            st.rerun()


    # --------------------------------------------------
    # SPECIALIST AGENT ACTIVITY
    # --------------------------------------------------

    if st.session_state.last_events:

        with st.expander("View Agent Activity"):

            for event in st.session_state.last_events:

                st.markdown(
                    f"**Specialist Tool:** "
                    f"`{event['specialist_tool']}`"
                )

                st.json(event["result"])


# --------------------------------------------------
# DOCTOR DIRECTORY
# --------------------------------------------------

with doctors_tab:

    st.subheader("Our Doctors")

    st.write(
        "Explore the doctors and their available specialties."
    )

    doctors = search_doctors()

    if doctors:

        for doctor in doctors:

            with st.container(border=True):

                st.markdown(f"### 👨‍⚕️ {doctor['name']}")

                st.write(
                    f"**Specialty:** {doctor['specialty']}"
                )

    else:

        st.info("No doctors are currently available.")


# --------------------------------------------------
# APPOINTMENT HISTORY
# --------------------------------------------------

with appointments_tab:

    st.subheader("My Appointments")

    st.write(
        "View appointments associated with your current demo session."
    )

    appointments = get_appointments(
        session_id=st.session_state.session_id
    )

    if appointments:

        st.dataframe(
            appointments,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "You do not have any appointments in this session yet."
        )


# --------------------------------------------------
# USER FEEDBACK
# --------------------------------------------------

with feedback_tab:

    st.subheader("Share Your Feedback")

    st.write(
        "Your feedback will help evaluate and improve ClinicalCare."
    )

    with st.form("feedback_form"):

        rating = st.slider(
            "How would you rate your experience?",
            min_value=1,
            max_value=5,
            value=4,
        )

        category = st.selectbox(
            "Feedback category",
            [
                "General",
                "Chat Assistant",
                "Appointment Management",
                "Doctor Information",
                "Other",
            ],
        )

        comment = st.text_area(
            "Additional comments",
            placeholder="Share your experience...",
        )

        submitted = st.form_submit_button(
            "Submit Feedback",
            use_container_width=True,
        )

        if submitted:

            try:

                save_feedback(
                    rating=rating,
                    comment=comment,
                    category=category,
                )

                st.success(
                    "Thank you! Your feedback has been saved."
                )

            except Exception as error:

                st.error(
                    "Feedback could not be saved. "
                    "Please try again."
                )

                st.write(str(error))


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "ClinicalCare | Academic Demonstration Project | "
    "Simulated Clinic | Not for real medical use"
)
