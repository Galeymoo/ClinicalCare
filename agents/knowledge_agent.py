
from rag import (
    retrieve_knowledge,
    format_retrieved_knowledge
)


class KnowledgeAgent:
    """
    Specialist agent responsible for answering clinic
    questions using the local knowledge base.
    """

    def __init__(self):
        self.name = "Knowledge Specialist"

    # --------------------------------------------------
    # 1. RETRIEVE RELEVANT INFORMATION
    # --------------------------------------------------

    def retrieve_information(self, question, top_k=3):

        return retrieve_knowledge(
            question,
            top_k=top_k
        )

    # --------------------------------------------------
    # 2. PREPARE KNOWLEDGE CONTEXT
    # --------------------------------------------------

    def prepare_answer_context(self, question):

        results = self.retrieve_information(question)

        grounded = len(results) > 0

        context = format_retrieved_knowledge(results)

        return {
            "question": question,
            "retrieved_information": context,
            "sources": list(set(
                result["source"]
                for result in results
            )),
            "retrieval_scores": [
                result["score"]
                for result in results
            ],
            "grounded": grounded
        }

    # --------------------------------------------------
    # 3. ANSWER KNOWLEDGE QUESTIONS
    # --------------------------------------------------

    def answer_question(self, question):
        """
        Return relevant knowledge and source details.

        The Coordinator Agent uses this information
        to prepare a grounded response.
        """

        # Validate the question.
        if not question or not question.strip():

            return {
                "success": False,
                "question": question,
                "grounded": False,
                "message": "Please provide a valid question.",
                "sources": [],
                "retrieval_scores": [],
                "retrieved_information": ""
            }

        # Retrieve relevant information.
        result = self.prepare_answer_context(
            question.strip()
        )

        # Handle questions with no relevant information.
        if not result["grounded"]:

            return {
                "success": False,
                "question": question,
                "grounded": False,
                "message": (
                    "I could not find sufficiently relevant "
                    "information in the clinic knowledge base. "
                    "I cannot provide an unsupported answer. "
                    "Please contact the clinic for clarification."
                ),
                "retrieved_information": (
                    result["retrieved_information"]
                ),
                "sources": [],
                "retrieval_scores": []
            }

        # Return grounded retrieval results.
        return {
            "success": True,
            "question": question,
            "retrieved_information": (
                result["retrieved_information"]
            ),
            "sources": result["sources"],
            "retrieval_scores": result["retrieval_scores"],
            "grounded": True
        }
