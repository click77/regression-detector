"""Database operations for storing regression test results."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from config import settings


class RegressionDatabase:
    """Handle SQLite database operations for regression tests."""

    def __init__(self, db_path: str = None):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or settings.database_path
        self.init_db()

    def init_db(self) -> None:
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Test cases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                input_data TEXT NOT NULL,
                expected_output TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Test results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                actual_output TEXT NOT NULL,
                passed BOOLEAN NOT NULL,
                regression BOOLEAN DEFAULT FALSE,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES test_cases(id)
            )
        """)

        # Baseline results table (for comparison)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS baseline_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL UNIQUE,
                baseline_output TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES test_cases(id)
            )
        """)

        conn.commit()
        conn.close()

    def add_test_case(
        self, name: str, description: str, input_data: str, expected_output: str
    ) -> int:
        """Add a new test case to the database.
        
        Args:
            name: Test case name
            description: Test case description
            input_data: Input data as JSON string
            expected_output: Expected output as JSON string
            
        Returns:
            Test case ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO test_cases (name, description, input_data, expected_output)
            VALUES (?, ?, ?, ?)
            """,
            (name, description, input_data, expected_output),
        )

        conn.commit()
        test_id = cursor.lastrowid
        conn.close()

        return test_id

    def record_test_result(
        self,
        test_id: int,
        actual_output: str,
        passed: bool,
        error_message: str = None,
    ) -> int:
        """Record a test execution result.
        
        Args:
            test_id: Test case ID
            actual_output: Actual output from execution
            passed: Whether test passed
            error_message: Error message if test failed
            
        Returns:
            Result record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO test_results (test_id, actual_output, passed, error_message)
            VALUES (?, ?, ?, ?)
            """,
            (test_id, actual_output, passed, error_message),
        )

        conn.commit()
        result_id = cursor.lastrowid
        conn.close()

        return result_id

    def set_baseline(self, test_id: int, baseline_output: str) -> None:
        """Set or update baseline result for a test case.
        
        Args:
            test_id: Test case ID
            baseline_output: Baseline output to store
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO baseline_results (test_id, baseline_output)
            VALUES (?, ?)
            """,
            (test_id, baseline_output),
        )

        conn.commit()
        conn.close()

    def get_baseline(self, test_id: int) -> Optional[str]:
        """Get baseline result for a test case.
        
        Args:
            test_id: Test case ID
            
        Returns:
            Baseline output or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT baseline_output FROM baseline_results WHERE test_id = ?",
            (test_id,),
        )

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def get_test_history(self, test_id: int, limit: int = 10) -> List[Dict]:
        """Get recent test results for a test case.
        
        Args:
            test_id: Test case ID
            limit: Number of recent results to return
            
        Returns:
            List of test results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, actual_output, passed, error_message, timestamp
            FROM test_results
            WHERE test_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (test_id, limit),
        )

        columns = ["id", "actual_output", "passed", "error_message", "timestamp"]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()

        return results

    def get_all_tests(self) -> List[Dict]:
        """Get all test cases.
        
        Returns:
            List of all test cases
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, description, input_data, expected_output, created_at
            FROM test_cases
            ORDER BY created_at DESC
            """
        )

        columns = ["id", "name", "description", "input_data", "expected_output", "created_at"]
        tests = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()

        return tests
