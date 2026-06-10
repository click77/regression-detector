# Regression Detector

An AI-powered regression detection system that uses OpenAI and deepeval to identify and track regressions in test cases.

## Features

- **Test Management**: Add, store, and manage test cases
- **Regression Detection**: Automatically detect regressions in test outputs
- **AI-Powered Evaluation**: Use OpenAI to evaluate test outputs
- **Quality Metrics**: Measure faithfulness, relevancy, and contextual relevancy
- **SQLite Storage**: Persistent storage of test cases and results
- **Async Support**: Efficient concurrent test execution

## Project Structure

```
regression-detector/
├── config.py           # Configuration management
├── db.py              # Database operations
├── detector.py        # Regression detection logic
├── evaluator.py       # Test evaluation metrics
├── main.py            # Main application entry point
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
├── .gitignore         # Git ignore patterns
└── README.md          # This file
```

## Setup

### 1. Create Virtual Environment

```bash
mkdir regression-detector && cd regression-detector
git init
python3 -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Example `.env`:
```
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
DATABASE_PATH=./regression_tests.db
LOG_LEVEL=INFO
```

## Usage

### Running the Application

```bash
python main.py
```

### Basic Example

```python
import asyncio
from main import RegressionDetectorApp

async def main():
    app = RegressionDetectorApp()
    
    # Add a test case
    test_id = app.add_test_case(
        name="Calculator Add",
        description="Test addition",
        input_data="2 + 3",
        expected_output="5"
    )
    
    # Run the test
    result = await app.run_test(test_id)
    print(result)
    
    # Get test history
    history = app.get_test_history(test_id)
    print(history)

asyncio.run(main())
```

## Module Documentation

### config.py
Manages configuration via environment variables using Pydantic.

**Key Classes:**
- `Settings`: Application configuration

### db.py
SQLite database operations for test storage and results.

**Key Classes:**
- `RegressionDatabase`: Database interface

**Key Methods:**
- `add_test_case()`: Add a new test
- `record_test_result()`: Store test results
- `set_baseline()`: Set baseline for comparison
- `get_test_history()`: Retrieve test history

### detector.py
Regression detection using OpenAI API.

**Key Classes:**
- `RegressionDetector`: Main detection logic

**Key Methods:**
- `evaluate_test()`: Evaluate single test
- `batch_evaluate()`: Evaluate multiple tests concurrently

### evaluator.py
Test evaluation using deepeval metrics.

**Key Classes:**
- `TestEvaluator`: Evaluation framework

**Key Methods:**
- `evaluate_output()`: Score test output quality
- `batch_evaluate()`: Evaluate multiple test cases

### main.py
Main application orchestrating all components.

**Key Classes:**
- `RegressionDetectorApp`: Main application class

## Database Schema

### test_cases
- `id`: Primary key
- `name`: Test name (unique)
- `description`: Test description
- `input_data`: Test input (JSON string)
- `expected_output`: Expected result (JSON string)
- `created_at`: Timestamp

### test_results
- `id`: Primary key
- `test_id`: Foreign key to test_cases
- `actual_output`: Generated output
- `passed`: Boolean result
- `regression`: Boolean regression flag
- `error_message`: Error details
- `timestamp`: Execution time

### baseline_results
- `id`: Primary key
- `test_id`: Foreign key to test_cases (unique)
- `baseline_output`: Reference output
- `timestamp`: Last updated

## Evaluation Metrics

The evaluator uses three key metrics:

1. **Faithfulness (40% weight)**: How closely actual output matches expected output
2. **Relevancy (35% weight)**: How relevant output is to the input
3. **Contextual Relevancy (25% weight)**: How relevant output is to context (if provided)

Overall score threshold for passing: 0.75 (75%)

## Error Handling

- Graceful handling of OpenAI API errors
- Detailed error logging
- Fallback mechanisms for failed tests
- Transaction safety in database operations

## Logging

Logs are configured via the `LOG_LEVEL` environment variable (INFO, DEBUG, WARNING, ERROR).

## Future Enhancements

- [ ] Web API interface
- [ ] Dashboard for visualization
- [ ] Test report generation
- [ ] Parallel test execution
- [ ] Integration with CI/CD pipelines
- [ ] Custom evaluation metrics
- [ ] Performance benchmarking

## License

MIT

## Contributing

Contributions welcome! Please follow standard GitHub workflow (fork, branch, PR).
