
import os
import streamlit as st

# Application settings
APP_NAME = "ClinicalCare"
APP_VERSION = "1.0.0"

# OpenRouter settings
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openrouter/free"

# Retrieve API key securely
def get_api_key():
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        return os.getenv("OPENROUTER_API_KEY")


# Database settings
# Uses SQLite locally by default.
# A PostgreSQL URL can be supplied later for cloud deployment.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///clinicalcare.db"
)

# Agent settings
MAX_AGENT_STEPS = 8
MAX_MEMORY_MESSAGES = 10

# Safety settings
REQUIRE_CONFIRMATION = True

# Clinic information
CLINIC_NAME = "ClinicalCare Demo Clinic"
CLINIC_LOCATION = "Bhutan"

# This project uses fictional doctors and simulated appointments.
SIMULATION_MODE = True
