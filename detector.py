"""Regression detection logic using OpenAI."""

import json
import logging
from typing import Dict, List, Optional, Tuple
import openai
from config import settings
from db import RegressionDatabase

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


class RegressionDetector:
    """Detect regressions by comparing current outputs against baselines."""

    def __init__(self, db: RegressionDatabase = None):
        """Initialize regression detector.
        
        Args:
            db: RegressionDatabase instance
        """
        self.db = db or RegressionDatabase()
        openai.api_key = settings.openai_api_key
        self.model = settings.openai_model

    async def evaluate_test(
        self, test_id: int, input_data: str, expected_output: str
    ) -> Tuple[bool, str, bool]:
        """Evaluate a single test and detect regressions.
        
        Args:
            test_id: Test case ID
            input_data: Input data to evaluate
            expected_output: Expected output
            
        Returns:
            Tuple of (passed, actual_output, is_regression)
        """
        try:
            # Get baseline for comparison
            baseline = self.db.get_baseline(test_id)

            # Call LLM to evaluate test
            prompt = self._build_evaluation_prompt(input_data, expected_output)
            response = await self._call_openai(prompt)
            actual_output = response.strip()

            # Check if output matches expected
            passed = self._compare_outputs(actual_output, expected_output)

            # Detect regression
            is_regression = False
            if baseline and not passed and self._compare_outputs(baseline, expected_output):
                is_regression = True
                logger.warning(
                    f"REGRESSION DETECTED in test {test_id}: "
                    f"baseline passed, current failed"
                )

            # Record result
            error_msg = None if passed else "Output does not match expected"
            self.db.record_test_result(test_id, actual_output, passed, error_msg)

            # Update baseline on first pass
            if passed and not baseline:
                self.db.set_baseline(test_id, actual_output)
                logger.info(f"Baseline set for test {test_id}")

            return passed, actual_output, is_regression

        except Exception as e:
            logger.error(f"Error evaluating test {test_id}: {str(e)}")
            self.db.record_test_result(test_id, "", False, str(e))
            return False, "", False

    async def batch_evaluate(self, test_ids: List[int]) -> Dict:
        """Evaluate multiple tests concurrently.
        
        Args:
            test_ids: List of test case IDs to evaluate
            
        Returns:
            Dictionary with results and regression summary
        """
        results = {
            "total": len(test_ids),
            "passed": 0,
            "failed": 0,
            "regressions": [],
            "details": [],
        }

        tests = self.db.get_all_tests()
        test_map = {t["id"]: t for t in tests}

        for test_id in test_ids:
            if test_id not in test_map:
                logger.warning(f"Test {test_id} not found")
                continue

            test = test_map[test_id]
            passed, actual_output, is_regression = await self.evaluate_test(
                test_id, test["input_data"], test["expected_output"]
            )

            results["passed" if passed else "failed"] += 1

            if is_regression:
                results["regressions"].append(test_id)

            results["details"].append(
                {
                    "test_id": test_id,
                    "name": test["name"],
                    "passed": passed,
                    "is_regression": is_regression,
                    "actual_output": actual_output,
                }
            )

        return results

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with retry logic.
        
        Args:
            prompt: Prompt to send to OpenAI
            
        Returns:
            Response text from OpenAI
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    def _build_evaluation_prompt(self, input_data: str, expected_output: str) -> str:
        """Build evaluation prompt for LLM.
        
        Args:
            input_data: Input to process
            expected_output: Expected output
            
        Returns:
            Formatted prompt string
        """
        return f"""
Evaluate the following test case and provide the output:

Input Data:
{input_data}

Expected Output:
{expected_output}

Please analyze this test case and provide what the actual output should be based on the input and expected behavior. 
Return only the output without any additional explanation.
"""

    def _compare_outputs(self, actual: str, expected: str) -> bool:
        """Compare actual output with expected output.
        
        Args:
            actual: Actual output
            expected: Expected output
            
        Returns:
            True if outputs match
        """
        # Normalize whitespace and compare
        actual_normalized = actual.strip().lower()
        expected_normalized = expected.strip().lower()
        return actual_normalized == expected_normalized
