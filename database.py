
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Date,
    Time,
    DateTime,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL


# --------------------------------------------------
# 1. Database connection
# --------------------------------------------------

# Convert common PostgreSQL URLs into the SQLAlchemy
# format supported by psycopg2.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg2://",
        1
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

# SQLite needs this setting for Streamlit.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# --------------------------------------------------
# 2. Doctor table
# --------------------------------------------------

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    specialty = Column(String(100), nullable=False)
    is_active = Column(Integer, default=1)


# --------------------------------------------------
# 3. Appointment table
# --------------------------------------------------

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    patient_name = Column(String(100), nullable=False)

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False
    )

    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)

    reason = Column(Text, default="")
    status = Column(String(20), default="booked", nullable=False)

    # Identifies the Streamlit session for basic session tracking.
    # This is not a substitute for user authentication.
    session_id = Column(String(100), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


# Prevents two active bookings for the same doctor,
# date and time. Cancelled appointments do not block the slot.
Index(
    "uq_active_doctor_slot",
    Appointment.doctor_id,
    Appointment.appointment_date,
    Appointment.appointment_time,
    unique=True,
    sqlite_where=text("status = 'booked'"),
    postgresql_where=text("status = 'booked'")
)


# --------------------------------------------------
# 4. Feedback table
# --------------------------------------------------

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)

    rating = Column(Integer, nullable=False)
    comment = Column(Text, default="")
    category = Column(String(50), default="general")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )


# --------------------------------------------------
# 5. Episodic memory table
# --------------------------------------------------

class EpisodicMemory(Base):
    __tablename__ = "episodic_memory"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(String(100), nullable=False)

    user_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)

    outcome = Column(String(50), default="completed")
    reflection = Column(Text, default="")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )


# --------------------------------------------------
# 6. Initial fictional doctors
# --------------------------------------------------

INITIAL_DOCTORS = [
    {
        "name": "Dr. Sonam Wangdi",
        "specialty": "Dermatology"
    },
    {
        "name": "Dr. Tashi Dorji",
        "specialty": "Cardiology"
    },
    {
        "name": "Dr. Dechen Zangmo",
        "specialty": "Paediatrics"
    },
    {
        "name": "Dr. Karma Tshering",
        "specialty": "General Medicine"
    },
    {
        "name": "Dr. Pema Choden",
        "specialty": "General Medicine"
    }
]


# --------------------------------------------------
# 7. Initialize database
# --------------------------------------------------

def init_db():
    # Create tables if they do not already exist.
    Base.metadata.create_all(bind=engine)

    # Insert the initial doctors only once.
    with SessionLocal() as session:
        for doctor_data in INITIAL_DOCTORS:
            existing_doctor = session.query(Doctor).filter_by(
                name=doctor_data["name"]
            ).first()

            if existing_doctor is None:
                doctor = Doctor(
                    name=doctor_data["name"],
                    specialty=doctor_data["specialty"]
                )
                session.add(doctor)

        session.commit()


# --------------------------------------------------
# 8. Database session helper
# --------------------------------------------------

def get_db():
    """Provide a database session and close it afterwards."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
