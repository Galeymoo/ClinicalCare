
from pathlib import Path
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# --------------------------------------------------
# 1. KNOWLEDGE BASE LOCATION
# --------------------------------------------------

KNOWLEDGE_FOLDER = (
    Path(__file__).parent
    / "data"
    / "knowledge_base"
)


# --------------------------------------------------
# 2. LOAD KNOWLEDGE DOCUMENTS
# --------------------------------------------------

def load_documents():
    """Load Markdown documents from the knowledge base."""

    documents = []

    for file_path in sorted(KNOWLEDGE_FOLDER.glob("*.md")):
        content = file_path.read_text(encoding="utf-8")

        if content.strip():
            documents.append({
                "source": file_path.name,
                "content": content
            })

    return documents


# --------------------------------------------------
# 3. SPLIT DOCUMENTS INTO SECTIONS
# --------------------------------------------------


def split_into_chunks(documents):
    """Split documents while keeping headings in each section."""

    chunks = []

    for document in documents:

        sections = re.split(
            r"(?m)(?=^\s*(?:\*\*)?#{1,3}\s+)",
            document["content"]
        )

        for section in sections:

            section = section.strip()

            if len(section.split()) < 5:
                continue

            # Add document context to policy sections.
            # This helps policy-related questions rank the
            # formal policy document appropriately.
            if document["source"] == "appointment_policy.md":
                section = "Clinic appointment policy. " + section

            chunks.append({
                "source": document["source"],
                "content": section
            })

    return chunks



# --------------------------------------------------
# 4. NORMALIZE QUESTIONS
# --------------------------------------------------


def normalize_question(question):
    """Expand common appointment terms while preserving original words."""

    replacements = {
        "rescheduling": "rescheduling reschedule change appointment",
        "rescheduled": "rescheduled reschedule change appointment",
        "reschedules": "reschedules reschedule change appointment",
        "reschedule": "reschedule rescheduling change appointment",
        "changing": "changing change reschedule appointment",
        "changed": "changed change reschedule appointment",
        "booking": "booking book appointment",
        "bookings": "bookings book appointment",
        "cancellation": "cancellation cancel appointment",
        "cancellations": "cancellations cancel appointment",
    }

    words = question.lower().split()
    expanded_words = []

    for word in words:
        expanded_words.append(
            replacements.get(word, word)
        )

    return " ".join(expanded_words)



# --------------------------------------------------
# 5. RETRIEVE RELEVANT KNOWLEDGE
# --------------------------------------------------

def retrieve_knowledge(question, top_k=3, threshold=0.20):
    """
    Retrieve relevant sections using TF-IDF
    and cosine similarity.
    """

    if not question or not question.strip():
        return []

    documents = load_documents()

    if not documents:
        return []

    chunks = split_into_chunks(documents)

    if not chunks:
        return []

    texts = [
        chunk["content"]
        for chunk in chunks
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    try:

        document_vectors = vectorizer.fit_transform(texts)

        # Normalize the user's question before retrieval.
        normalized_question = normalize_question(question)

        question_vector = vectorizer.transform([
            normalized_question
        ])

    except ValueError:
        return []

    similarities = cosine_similarity(
        question_vector,
        document_vectors
    ).flatten()

    ranked_indices = similarities.argsort()[::-1]

    results = []

    for index in ranked_indices:

        score = float(similarities[index])

        # Reject weakly related sections.
        if score < threshold:
            break

        results.append({
            "source": chunks[index]["source"],
            "content": chunks[index]["content"],
            "score": round(score, 4)
        })

        if len(results) >= top_k:
            break

    return results


# --------------------------------------------------
# 6. FORMAT RETRIEVED KNOWLEDGE
# --------------------------------------------------

def format_retrieved_knowledge(results):
    """Format retrieved sections for the AI agent."""

    if not results:
        return (
            "No sufficiently relevant information was found "
            "in the clinic knowledge base. Do not invent an "
            "answer. Explain that the information is unavailable."
        )

    formatted = []

    for result in results:

        formatted.append(
            f"Source: {result['source']}\n"
            f"Relevance score: {result['score']}\n"
            f"Content:\n{result['content']}"
        )

    return "\n\n---\n\n".join(formatted)
