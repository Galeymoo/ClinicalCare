
from rag import retrieve_knowledge
from agents.knowledge_agent import KnowledgeAgent


def test_retrieve_cancellation_policy():
    results = retrieve_knowledge(
        "What is the clinic cancellation policy?"
    )

    assert len(results) > 0
    assert results[0]["source"] == "appointment_policy.md"


def test_retrieve_rescheduling_information():
    results = retrieve_knowledge(
        "Can I reschedule my appointment?"
    )

    assert len(results) > 0
    assert "appointment" in results[0]["content"].lower()


def test_unrelated_question_returns_no_results():
    results = retrieve_knowledge(
        "What is the weather forecast for tomorrow?"
    )

    assert results == []


def test_knowledge_agent_rejects_unrelated_question():
    agent = KnowledgeAgent()

    result = agent.answer_question(
        "What is the weather forecast for tomorrow?"
    )

    assert result["success"] is False
    assert result["grounded"] is False
    assert result["sources"] == []


def test_knowledge_agent_answers_grounded_question():
    agent = KnowledgeAgent()

    result = agent.answer_question(
        "What is the clinic cancellation policy?"
    )

    assert result["success"] is True
    assert result["grounded"] is True
    assert "appointment_policy.md" in result["sources"]


def test_knowledge_agent_rejects_empty_question():
    agent = KnowledgeAgent()

    result = agent.answer_question("")

    assert result["success"] is False
    assert result["grounded"] is False
