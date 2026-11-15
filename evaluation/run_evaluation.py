
import sys
import uuid
import pandas as pd

from pathlib import Path


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

# Project root: D:\ClinicalCare
BASE_DIR = Path(__file__).resolve().parent.parent

# Evaluation folder: D:\ClinicalCare\evaluation
EVALUATION_DIR = BASE_DIR / "evaluation"

TEST_CASES_FILE = EVALUATION_DIR / "test_cases.csv"
RESULTS_FILE = EVALUATION_DIR / "evaluation_results.csv"

# Add project root to Python import path.
sys.path.insert(0, str(BASE_DIR))

from agents.coordinator import CoordinatorAgent


# --------------------------------------------------
# LOAD TEST CASES
# --------------------------------------------------

def load_test_cases():
    """Load and validate evaluation test cases."""

    if not TEST_CASES_FILE.exists():
        raise FileNotFoundError(
            f"Test cases file not found: {TEST_CASES_FILE}"
        )

    test_cases = pd.read_csv(TEST_CASES_FILE)

    required_columns = [
        "case_id",
        "category",
        "user_message",
        "expected_tools",
        "expected_pending_action",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in test_cases.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing CSV columns: {missing_columns}"
        )

    return test_cases


# --------------------------------------------------
# CHECK TOOL EXECUTION SUCCESS
# --------------------------------------------------

def is_tool_execution_success(event):
    """Check whether a specialist tool returned a valid result."""

    result = event.get("result")

    # Successful dictionary results.
    if isinstance(result, dict):
        return (
            result.get("success") is True
            or result.get("confirmation_required") is True
        )

    # Search and viewing tools return lists.
    # An empty list is also a valid result.
    if isinstance(result, list):
        return True

    # Other result types are not accepted.
    return False


# --------------------------------------------------
# RUN ONE EVALUATION CASE
# --------------------------------------------------

def evaluate_case(coordinator, test_case):
    """Evaluate one test case and return its results."""

    case_id = test_case["case_id"]
    category = test_case["category"]

    user_message = test_case["user_message"]

    expected_tools = [
        tool.strip()
        for tool in str(test_case["expected_tools"]).split(";")
        if tool.strip()
    ]

    expected_pending = (
        str(test_case["expected_pending_action"])
        .strip()
        .lower() == "true"
    )

    # Each test case receives a separate session.
    session_id = f"evaluation-{uuid.uuid4()}"

    try:

        # Reset the previous API error before this test.
        coordinator.last_error = None

        answer, history, events, pending_action = (
            coordinator.ask(
                user_message=user_message,
                history=None,
                session_id=session_id,
            )
        )

        # --------------------------------------------------
        # CHECK API ERRORS
        # --------------------------------------------------

        api_error = coordinator.last_error

        if api_error is not None:

            return {
                "case_id": case_id,
                "category": category,
                "evaluation_status": "API_ERROR",
                "expected_tools": ";".join(expected_tools),
                "actual_tools": "",
                "tool_selection_correct": None,
                "tool_execution_success": None,
                "expected_pending_action": expected_pending,
                "actual_pending_action": None,
                "confirmation_handled_correctly": None,
                "response_completed": None,
                "task_success": None,
                "api_error_category": api_error.get("category"),
                "api_status_code": api_error.get("status_code"),
                "api_error_type": api_error.get("error_type"),
                "agent_response": answer,
            }

        # --------------------------------------------------
        # COLLECT ACTUAL TOOLS
        # --------------------------------------------------

        actual_tools = [
            event["specialist_tool"]
            for event in events
            if "specialist_tool" in event
        ]

        # Check exact tool selection and sequence.
        tool_selection_correct = (
            actual_tools == expected_tools
        )

        # --------------------------------------------------
        # CHECK TOOL EXECUTION
        # --------------------------------------------------

        tool_execution_success = (
            len(events) > 0
            and all(
                is_tool_execution_success(event)
                for event in events
            )
        )

        # A prepared booking, cancellation or rescheduling
        # counts as successful preparation.
        # It does not mean the appointment was completed.

        # --------------------------------------------------
        # CHECK CONFIRMATION
        # --------------------------------------------------

        actual_pending = (
            isinstance(pending_action, dict)
            and pending_action.get("confirmation_required") is True
        )

        confirmation_handled_correctly = (
            actual_pending == expected_pending
        )

        # --------------------------------------------------
        # CHECK RESPONSE
        # --------------------------------------------------

        response_completed = (
            isinstance(answer, str)
            and len(answer.strip()) > 0
        )

        # --------------------------------------------------
        # OVERALL TASK SUCCESS
        # --------------------------------------------------

        task_success = (
            tool_selection_correct
            and tool_execution_success
            and confirmation_handled_correctly
            and response_completed
        )

        evaluation_status = (
            "PASS" if task_success else "FAIL"
        )

        return {
            "case_id": case_id,
            "category": category,
            "evaluation_status": evaluation_status,
            "expected_tools": ";".join(expected_tools),
            "actual_tools": ";".join(actual_tools),
            "tool_selection_correct": tool_selection_correct,
            "tool_execution_success": tool_execution_success,
            "expected_pending_action": expected_pending,
            "actual_pending_action": actual_pending,
            "confirmation_handled_correctly": (
                confirmation_handled_correctly
            ),
            "response_completed": response_completed,
            "task_success": task_success,
            "api_error_category": None,
            "api_status_code": None,
            "api_error_type": None,
            "agent_response": answer,
        }

    except Exception as error:

        return {
            "case_id": case_id,
            "category": category,
            "evaluation_status": "EVALUATION_ERROR",
            "expected_tools": ";".join(expected_tools),
            "actual_tools": "",
            "tool_selection_correct": None,
            "tool_execution_success": None,
            "expected_pending_action": expected_pending,
            "actual_pending_action": None,
            "confirmation_handled_correctly": None,
            "response_completed": None,
            "task_success": None,
            "api_error_category": None,
            "api_status_code": None,
            "api_error_type": type(error).__name__,
            "agent_response": f"Evaluation error: {str(error)}",
        }


# --------------------------------------------------
# CALCULATE EVALUATION METRICS
# --------------------------------------------------

def calculate_metrics(results):
    """Calculate and display agent evaluation metrics."""

    total_cases = len(results)

    if total_cases == 0:
        print("No evaluation results are available.")
        return

    # Separate successfully evaluated cases from interrupted cases.
    evaluated_results = results[
        results["evaluation_status"].isin(["PASS", "FAIL"])
    ]

    evaluated_cases = len(evaluated_results)

    passed_cases = (
        results["evaluation_status"] == "PASS"
    ).sum()

    failed_cases = (
        results["evaluation_status"] == "FAIL"
    ).sum()

    api_errors = (
        results["evaluation_status"] == "API_ERROR"
    ).sum()

    evaluation_errors = (
        results["evaluation_status"] == "EVALUATION_ERROR"
    ).sum()

    print("\n" + "=" * 60)
    print("CLINICALCARE AGENT EVALUATION RESULTS")
    print("=" * 60)

    print(f"Total test cases: {total_cases}")
    print(f"Successfully evaluated: {evaluated_cases}")
    print(f"Passed cases: {passed_cases}")
    print(f"Failed cases: {failed_cases}")
    print(f"API errors: {api_errors}")
    print(f"Evaluation errors: {evaluation_errors}")

    if evaluated_cases == 0:

        print(
            "\nNo test cases were successfully evaluated."
        )

        print(
            "Check the API connection and run the evaluation again."
        )

        print("=" * 60)
        return

    # --------------------------------------------------
    # PERFORMANCE METRICS
    # --------------------------------------------------

    tool_accuracy = (
        evaluated_results["tool_selection_correct"].mean() * 100
    )

    execution_success = (
        evaluated_results["tool_execution_success"].mean() * 100
    )

    confirmation_accuracy = (
        evaluated_results[
            "confirmation_handled_correctly"
        ].mean() * 100
    )

    response_completion = (
        evaluated_results["response_completed"].mean() * 100
    )

    task_success_rate = (
        evaluated_results["task_success"].mean() * 100
    )

    print("\nPERFORMANCE METRICS")
    print("-" * 60)

    print(
        f"Tool selection accuracy: {tool_accuracy:.2f}%"
    )

    print(
        f"Tool execution success: {execution_success:.2f}%"
    )

    print(
        f"Confirmation handling accuracy: "
        f"{confirmation_accuracy:.2f}%"
    )

    print(
        f"Response completion rate: {response_completion:.2f}%"
    )

    print(
        f"Overall task success rate: {task_success_rate:.2f}%"
    )

    print("-" * 60)

    print(
        "Metrics are calculated using successfully evaluated "
        "cases only."
    )

    print("=" * 60)


# --------------------------------------------------
# MAIN EVALUATION
# --------------------------------------------------

def main():

    print("\nStarting ClinicalCare evaluation...")

    # Load test cases.
    test_cases = load_test_cases()

    print(
        f"Loaded {len(test_cases)} evaluation cases."
    )

    # Create Coordinator Agent.
    coordinator = CoordinatorAgent()

    evaluation_results = []

    # Run each test case.
    for index, test_case in test_cases.iterrows():

        print(
            f"\nRunning test {index + 1}/{len(test_cases)}: "
            f"{test_case['case_id']}"
        )

        result = evaluate_case(
            coordinator,
            test_case,
        )

        evaluation_results.append(result)

        print(
            f"Result: {result['evaluation_status']}"
        )

        print(
            f"Expected tools: {result['expected_tools']}"
        )

        print(
            f"Actual tools: {result['actual_tools']}"
        )

        if result["evaluation_status"] == "API_ERROR":

            print(
                f"API error: {result['api_error_category']}"
            )

            print(
                f"Status code: {result['api_status_code']}"
            )

        elif result["evaluation_status"] == "EVALUATION_ERROR":

            print(result["agent_response"])

    # --------------------------------------------------
    # SAVE EVALUATION RESULTS
    # --------------------------------------------------

    results_df = pd.DataFrame(evaluation_results)

    results_df.to_csv(
        RESULTS_FILE,
        index=False,
    )

    print(
        f"\nDetailed results saved to:\n{RESULTS_FILE}"
    )

    # --------------------------------------------------
    # DISPLAY METRICS
    # --------------------------------------------------

    calculate_metrics(results_df)


# --------------------------------------------------
# PROGRAM ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
