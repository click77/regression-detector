"""Test evaluation and scoring using quality metrics."""

import logging
from typing import Dict, List
from config import settings

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


class TestEvaluator:
    """Evaluate test results using quality metrics."""

    def __init__(self):
        """Initialize evaluator with metrics."""
        pass

    def evaluate_output(
        self,
        input_data: str,
        expected_output: str,
        actual_output: str,
        context: str = None,
    ) -> Dict:
        """Evaluate output quality using multiple metrics.
        
        Args:
            input_data: Input data for the test
            expected_output: Expected output
            actual_output: Actual output generated
            context: Optional context for evaluation
            
        Returns:
            Dictionary with evaluation scores and metrics
        """
        try:
            results = {
                "input": input_data,
                "expected": expected_output,
                "actual": actual_output,
                "scores": {},
                "passed": False,
            }

            # Evaluate faithfulness (consistency with expected output)
            faithfulness_score = self._evaluate_faithfulness(actual_output, expected_output)
            results["scores"]["faithfulness"] = faithfulness_score

            # Evaluate relevancy
            relevancy_score = self._evaluate_relevancy(input_data, actual_output)
            results["scores"]["relevancy"] = relevancy_score

            # Evaluate contextual relevancy if context provided
            if context:
                contextual_score = self._evaluate_contextual_relevancy(
                    actual_output, context
                )
                results["scores"]["contextual_relevancy"] = contextual_score

            # Calculate overall score
            overall_score = self._calculate_overall_score(results["scores"])
            results["scores"]["overall"] = overall_score

            # Determine pass/fail (threshold: 0.75)
            results["passed"] = overall_score >= 0.75

            logger.info(f"Evaluation complete. Overall score: {overall_score:.2f}")
            return results

        except Exception as e:
            logger.error(f"Error during evaluation: {str(e)}")
            return {
                "input": input_data,
                "expected": expected_output,
                "actual": actual_output,
                "error": str(e),
                "passed": False,
            }

    def batch_evaluate(
        self, test_cases: List[Dict], context: str = None
    ) -> List[Dict]:
        """Evaluate multiple test cases.
        
        Args:
            test_cases: List of test cases with input, expected, actual
            context: Optional context for evaluation
            
        Returns:
            List of evaluation results
        """
        results = []
        for test_case in test_cases:
            result = self.evaluate_output(
                test_case.get("input", ""),
                test_case.get("expected", ""),
                test_case.get("actual", ""),
                context,
            )
            results.append(result)

        return results

    def _evaluate_faithfulness(self, actual: str, expected: str) -> float:
        """Evaluate how faithful actual output is to expected output.
        
        Args:
            actual: Actual output
            expected: Expected output
            
        Returns:
            Faithfulness score (0-1)
        """
        try:
            # Simple similarity-based scoring
            actual_words = set(actual.lower().split())
            expected_words = set(expected.lower().split())

            if not expected_words:
                return 1.0

            overlap = len(actual_words & expected_words)
            union = len(actual_words | expected_words)

            faithfulness = overlap / union if union > 0 else 0
            return min(faithfulness, 1.0)

        except Exception as e:
            logger.warning(f"Error calculating faithfulness: {str(e)}")
            return 0.0

    def _evaluate_relevancy(self, input_data: str, actual: str) -> float:
        """Evaluate how relevant actual output is to input.
        
        Args:
            input_data: Input data
            actual: Actual output
            
        Returns:
            Relevancy score (0-1)
        """
        try:
            # Check if output contains key terms from input
            input_words = set(w.lower() for w in input_data.split() if len(w) > 3)
            output_words = set(w.lower() for w in actual.split() if len(w) > 3)

            if not input_words:
                return 1.0

            overlap = len(input_words & output_words)
            relevancy = overlap / len(input_words)

            return min(relevancy, 1.0)

        except Exception as e:
            logger.warning(f"Error calculating relevancy: {str(e)}")
            return 0.0

    def _evaluate_contextual_relevancy(self, actual: str, context: str) -> float:
        """Evaluate how relevant output is to provided context.
        
        Args:
            actual: Actual output
            context: Context information
            
        Returns:
            Contextual relevancy score (0-1)
        """
        try:
            context_words = set(w.lower() for w in context.split() if len(w) > 3)
            output_words = set(w.lower() for w in actual.split() if len(w) > 3)

            if not context_words:
                return 1.0

            overlap = len(context_words & output_words)
            contextual_relevancy = overlap / len(context_words)

            return min(contextual_relevancy, 1.0)

        except Exception as e:
            logger.warning(f"Error calculating contextual relevancy: {str(e)}")
            return 0.0

    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """Calculate overall evaluation score from individual metrics.
        
        Args:
            scores: Dictionary of metric scores
            
        Returns:
            Overall score (0-1)
        """
        if not scores:
            return 0.0

        # Weight individual scores
        weights = {
            "faithfulness": 0.4,
            "relevancy": 0.35,
            "contextual_relevancy": 0.25,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for metric, weight in weights.items():
            if metric in scores:
                weighted_sum += scores[metric] * weight
                total_weight += weight

        overall = weighted_sum / total_weight if total_weight > 0 else 0.0
        return min(overall, 1.0)
