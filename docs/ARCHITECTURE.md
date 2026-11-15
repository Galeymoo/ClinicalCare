# ClinicalCare System Architecture

## 1. Overview

ClinicalCare uses a multi-agent architecture to support clinic appointment management and clinic information retrieval. The system consists of a Coordinator Agent, an Appointment Specialist Agent, and a Knowledge Specialist Agent.

The agents work together through a conversational interface to understand user requests, perform appointment-related operations, and retrieve information from the clinic knowledge base.

## 2. Main Components

### 2.1 User Interface

The user interacts with ClinicalCare through a web-based chatbot developed using Streamlit. Users can submit natural-language requests and receive responses from the system.

### 2.2 Coordinator Agent

The Coordinator Agent acts as the central controller. It interprets user requests, uses the language model to determine the appropriate actions, delegates tasks to the relevant tools or specialist agents, and generates responses.

### 2.3 Appointment Specialist Agent

The Appointment Specialist handles appointment-related operations, including:

- Searching for doctors.
- Checking appointment availability.
- Preparing appointment bookings.
- Viewing existing appointments.
- Preparing appointment cancellations and rescheduling.

The appointment operations interact with the database through dedicated tools. Booking, cancellation, and rescheduling require explicit user confirmation before the requested action is completed.

### 2.4 Knowledge Specialist Agent

The Knowledge Specialist handles questions about clinic policies and frequently asked questions. It uses the local knowledge base and the RAG retrieval process to find relevant information before generating an answer.

### 2.5 OpenRouter Language Model

The system uses an OpenRouter language model to support natural-language understanding, request interpretation, and tool selection.

### 2.6 Memory Component

The memory component supports short-term conversational memory and episodic memory. Short-term memory retains recent conversation messages, while episodic memory stores information about previous interactions and their outcomes.

### 2.7 Database

The database stores doctor and appointment information. SQLAlchemy is used for database operations and interaction with the application.

### 2.8 Knowledge Base and RAG

The knowledge base contains clinic policy and FAQ documents. The RAG component processes the documents using text chunking, TF-IDF vectorization, and cosine similarity to retrieve relevant information for user questions.

## 3. Agent Interaction Workflow

The general interaction process follows these steps:

1. The user submits a request through the Streamlit interface.
2. The Coordinator Agent interprets the request using the language model.
3. The Coordinator selects the appropriate specialist or tool.
4. The Appointment Specialist handles appointment operations, or the Knowledge Specialist retrieves relevant clinic information.
5. The required database or knowledge base operation is performed.
6. The result is returned to the Coordinator Agent.
7. The Coordinator generates a response for the user.
8. The conversation and relevant interaction information are maintained through the memory component.

## 4. Architecture Design Justification

The multi-agent architecture separates appointment management from clinic information retrieval. This separation makes the system easier to organize, maintain, and test.

The Coordinator Agent provides a central point for handling user requests, while specialized agents focus on their assigned responsibilities. The RAG component helps ground policy responses in the available clinic documents, and explicit confirmation requirements help prevent unintended appointment actions.

## 5. System Limitations

ClinicalCare is an academic prototype that uses simulated clinic information. It is not connected to a real healthcare facility and is not intended for real patient management or medical advice.