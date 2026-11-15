
import pytest

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import tools
from database import Base, Doctor


@pytest.fixture
def test_db(monkeypatch):
    """Create a separate temporary database for each test."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    Base.metadata.create_all(bind=engine)

    # Make the tools use the temporary database.
    monkeypatch.setattr(tools, "SessionLocal", TestSession)

    with TestSession() as db:
        db.add_all([
            Doctor(
                name="Dr. Tashi Dorji",
                specialty="Cardiology"
            ),
            Doctor(
                name="Dr. Sonam Wangdi",
                specialty="Dermatology"
            )
        ])
        db.commit()

    yield TestSession

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


TEST_DATE = "2026-11-16"


def test_search_doctors(test_db):
    doctors = tools.search_doctors()

    assert len(doctors) == 2


def test_check_availability(test_db):
    result = tools.check_availability(
        "Dr. Tashi Dorji",
        TEST_DATE
    )

    assert result["success"] is True
    assert "10:00" in result["available_slots"]


def test_book_appointment(test_db):
    result = tools.book_appointment(
        patient_name="Test Patient",
        doctor_name="Dr. Tashi Dorji",
        appointment_date=TEST_DATE,
        appointment_time="10:00",
        session_id="test-session"
    )

    assert result["success"] is True
    assert result["appointment_id"] is not None


def test_prevent_duplicate_booking(test_db):
    first = tools.book_appointment(
        patient_name="Patient One",
        doctor_name="Dr. Tashi Dorji",
        appointment_date=TEST_DATE,
        appointment_time="10:00",
        session_id="session-one"
    )

    second = tools.book_appointment(
        patient_name="Patient Two",
        doctor_name="Dr. Tashi Dorji",
        appointment_date=TEST_DATE,
        appointment_time="10:00",
        session_id="session-two"
    )

    assert first["success"] is True
    assert second["success"] is False


def test_cancel_appointment(test_db):
    booking = tools.book_appointment(
        patient_name="Test Patient",
        doctor_name="Dr. Tashi Dorji",
        appointment_date=TEST_DATE,
        appointment_time="10:00",
        session_id="test-session"
    )

    result = tools.cancel_appointment(
        booking["appointment_id"],
        session_id="test-session"
    )

    assert result["success"] is True


def test_reschedule_appointment(test_db):
    booking = tools.book_appointment(
        patient_name="Test Patient",
        doctor_name="Dr. Tashi Dorji",
        appointment_date=TEST_DATE,
        appointment_time="10:00",
        session_id="test-session"
    )

    result = tools.reschedule_appointment(
        appointment_id=booking["appointment_id"],
        new_date=TEST_DATE,
        new_time="14:00",
        session_id="test-session"
    )

    assert result["success"] is True
    assert result["new_time"] == "14:00"


def test_session_cannot_access_another_session_booking(test_db):
    booking = tools.book_appointment(
        patient_name="Test Patient",
        doctor_name="Dr. Tashi Dorji",
        appointment_date=TEST_DATE,
        appointment_time="10:00",
        session_id="session-one"
    )

    result = tools.cancel_appointment(
        booking["appointment_id"],
        session_id="session-two"
    )

    assert result["success"] is False
