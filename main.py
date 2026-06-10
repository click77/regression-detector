"""Main entry point for the regression detector application."""

import asyncio
import json
import logging
from typing import List, Optional
from config import settings
from db import RegressionDatabase
from detector import RegressionDetector
from evaluator import TestEvaluator

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RegressionDetectorApp:
    """Main application for regression detection."""

    def __init__(self):
        """Initialize the application."""
        self.db = RegressionDatabase()
        self.detector = RegressionDetector(self.db)
        self.evaluator = TestEvaluator()

    def add_test_case(
        self, name: str, description: str, input_data: str, expected_output: str
    ) -> int:
        """Add a new test case.
        
        Args:
            name: Test case name
            description: Test case description
            input_data: Input data
            expected_output: Expected output
            
        Returns:
            Test case ID
        """
        test_id = self.db.add_test_case(name, description, input_data, expected_output)
        logger.info(f"Added test case '{name}' with ID {test_id}")
        return test_id

    async def run_test(self, test_id: int) -> dict:
        """Run a single test.
        
        Args:
            test_id: Test case ID to run
            
        Returns:
            Test result dictionary
        """
        tests = self.db.get_all_tests()
        test = next((t for t in tests if t["id"] == test_id), None)

        if not test:
            logger.error(f"Test {test_id} not found")
            return {"error": "Test not found"}

        logger.info(f"Running test: {test['name']}")

        passed, actual_output, is_regression = await self.detector.evaluate_test(
            test_id, test["input_data"], test["expected_output"]
        )

        # Evaluate output quality
        eval_result = self.evaluator.evaluate_output(
            test["input_data"], test["expected_output"], actual_output
        )

        result = {
            "test_id": test_id,
            "name": test["name"],
            "passed": passed,
            "is_regression": is_regression,
            "actual_output": actual_output,
            "expected_output": test["expected_output"],
            "evaluation": eval_result,
        }

        return result

    async def run_all_tests(self) -> dict:
        """Run all test cases.
        
        Returns:
            Summary of all test results
        """
        tests = self.db.get_all_tests()
        test_ids = [t["id"] for t in tests]

        if not test_ids:
            logger.warning("No tests to run")
            return {"total": 0, "passed": 0, "failed": 0, "regressions": []}

        logger.info(f"Running {len(test_ids)} tests...")
        results = await self.detector.batch_evaluate(test_ids)

        return results

    def get_test_history(self, test_id: int, limit: int = 10) -> List:
        """Get execution history for a test.
        
        Args:
            test_id: Test case ID
            limit: Number of recent results to return
            
        Returns:
            List of test results
        """
        return self.db.get_test_history(test_id, limit)

    def list_all_tests(self) -> List:
        """List all test cases.
        
        Returns:
            List of all test cases
        """
        return self.db.get_all_tests()

    def print_summary(self, results: dict) -> None:
        """Print test results summary.
        
        Args:
            results: Test results dictionary
        """
        print("\n" + "=" * 60)
        print("TEST EXECUTION SUMMARY")
        print("=" * 60)

        if isinstance(results, dict) and "details" in results:
            print(f"Total Tests: {results['total']}")
            print(f"Passed: {results['passed']}")
            print(f"Failed: {results['failed']}")
            print(f"Regressions Detected: {len(results['regressions'])}")

            if results["regressions"]:
                print("\n⚠️  REGRESSIONS DETECTED:")
                for test_id in results["regressions"]:
                    detail = next(
                        (d for d in results["details"] if d["test_id"] == test_id), None
                    )
                    if detail:
                        print(f"  - {detail['name']} (ID: {test_id})")

            print("\nDetailed Results:")
            for detail in results["details"]:
                status = "✓ PASS" if detail["passed"] else "✗ FAIL"
                regression = " [REGRESSION]" if detail["is_regression"] else ""
                print(f"  {status} - {detail['name']}{regression}")

        print("=" * 60 + "\n")


async def main():
    """Main entry point with example usage."""
    app = RegressionDetectorApp()

    # Example: Add test cases
    logger.info("Adding example test cases...")

    test1_id = app.add_test_case(
        name="Calculator Add",
        description="Test addition operation",
        input_data="2 + 3",
        expected_output="5",
    )

    test2_id = app.add_test_case(
        name="String Uppercase",
        description="Test uppercase conversion",
        input_data="hello world",
        expected_output="HELLO WORLD",
    )

    # Run individual test
    logger.info(f"Running individual test: {test1_id}")
    result = await app.run_test(test1_id)
    print(json.dumps(result, indent=2, default=str))

    # Run all tests
    logger.info("Running all tests...")
    results = await app.run_all_tests()
    app.print_summary(results)

    # View test history
    logger.info("Fetching test history...")
    history = app.get_test_history(test1_id, limit=5)
    print(f"Test {test1_id} History:")
    print(json.dumps(history, indent=2, default=str))

    # List all tests
    logger.info("Listing all tests...")
    all_tests = app.list_all_tests()
    print(f"Total tests in database: {len(all_tests)}")


if __name__ == "__main__":
    asyncio.run(main())
