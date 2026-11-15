# ClinicalCare – Multi-Agent Clinic Appointment Assistant

## Project Overview

ClinicalCare is a multi-agent AI-based clinic appointment management assistant developed as part of the Intelligent and Generative Agents module at Sherubtse College.

The system helps users search for doctors, check appointment availability, prepare bookings, view appointments, and retrieve clinic policy information through a conversational interface.

## Features

- Doctor search by name or medical specialty.
- Appointment availability checking.
- Appointment booking with explicit user confirmation.
- Appointment viewing, cancellation, and rescheduling.
- Clinic policy and FAQ retrieval using Retrieval-Augmented Generation (RAG).
- Short-term conversational memory and episodic memory.
- Multi-agent coordination between specialized agents.

## Technologies Used

- Python
- Streamlit
- OpenRouter API
- SQLAlchemy
- SQLite
- Scikit-learn
- TF-IDF and cosine similarity
- Git and GitHub

## Project Structure

```text
ClinicalCare/
├── agents/
│   ├── __init__.py
│   ├── appointment_agent.py
│   ├── coordinator.py
│   └── knowledge_agent.py
├── data/
│   └── knowledge_base/
├── docs/
├── evaluation/
├── tests/
├── .streamlit/
├── agent.py
├── app.py
├── config.py
├── database.py
├── memory.py
├── rag.py
├── requirements.txt
└── README.md
```

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/Galeymoo/ClinicalCare.git
cd ClinicalCare
```

2. Create and activate a virtual environment.

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Configure the OpenRouter API key using Streamlit secrets or the appropriate environment variable.

5. Run the application:

```bash
streamlit run app.py
```

## Deployment

The application is deployed using Streamlit Community Cloud and its source code is maintained on GitHub.

Repository: https://github.com/Galeymoo/ClinicalCare

## Evaluation

The project was evaluated using automated test cases and unit tests. The automated evaluation achieved 6 out of 6 successful cases, while the unit test suite passed 24 out of 24 tests.

Manual testing was also conducted on the deployed application to verify doctor search, policy retrieval, appointment availability, booking confirmation, and appointment retrieval.

## Project Scope

ClinicalCare is an academic demonstration using simulated clinic data. It is not connected to a real healthcare facility and is not intended to store real patient information or provide medical diagnosis or treatment advice.