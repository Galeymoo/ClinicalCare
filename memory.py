
from datetime import datetime, timezone

from database import SessionLocal, EpisodicMemory


# --------------------------------------------------
# 1. Short-term conversational memory
# --------------------------------------------------

def add_to_short_term_memory(history, role, content):
    """
    Add a message to the conversation history.
    Keep only the most recent 10 messages.
    """

    history.append({
        "role": role,
        "content": content
    })

    return history[-10:]


def get_short_term_memory(history):
    """Return the recent conversation history."""
    return history


# --------------------------------------------------
# 2. Save an interaction to episodic memory
# --------------------------------------------------

def save_episode(
    session_id,
    user_message,
    agent_response,
    outcome="completed",
    reflection=""
):
    """Store an interaction in the database."""

    with SessionLocal() as db:
        episode = EpisodicMemory(
            session_id=session_id,
            user_message=user_message,
            agent_response=agent_response,
            outcome=outcome,
            reflection=reflection
        )

        db.add(episode)
        db.commit()
        db.refresh(episode)

        return episode.id


# --------------------------------------------------
# 3. Retrieve previous interactions
# --------------------------------------------------

def get_recent_episodes(session_id, limit=5):
    """Retrieve recent interactions for a session."""

    with SessionLocal() as db:
        episodes = (
            db.query(EpisodicMemory)
            .filter(EpisodicMemory.session_id == session_id)
            .order_by(EpisodicMemory.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": episode.id,
                "user_message": episode.user_message,
                "agent_response": episode.agent_response,
                "outcome": episode.outcome,
                "reflection": episode.reflection,
                "created_at": episode.created_at.isoformat()
                if episode.created_at else None
            }
            for episode in reversed(episodes)
        ]


# --------------------------------------------------
# 4. Update an interaction with reflection
# --------------------------------------------------

def update_episode_reflection(
    episode_id,
    reflection,
    outcome=None
):
    """Save the agent's reflection about a previous interaction."""

    with SessionLocal() as db:
        episode = db.query(EpisodicMemory).filter(
            EpisodicMemory.id == episode_id
        ).first()

        if not episode:
            return False

        episode.reflection = reflection

        if outcome:
            episode.outcome = outcome

        db.commit()

        return True


# --------------------------------------------------
# 5. Clear short-term memory
# --------------------------------------------------

def clear_short_term_memory():
    """Return an empty conversation history."""

    return []
