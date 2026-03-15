"""Unit tests for RetryManager."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retry_manager import RetryManager


class TestShouldRetry:
    def test_allows_retry_when_below_max(self):
        rm = RetryManager()
        assert rm.should_retry("t1", "err") is True

    def test_denies_retry_at_max(self):
        rm = RetryManager()
        for _ in range(RetryManager.MAX_RETRIES):
            rm.record_attempt("t1", "err", False)
        assert rm.should_retry("t1", "err") is False


class TestRecordAttempt:
    def test_increments_count_on_failure(self):
        rm = RetryManager()
        rm.record_attempt("t1", "err", False)
        rm.record_attempt("t1", "err2", False)
        state = rm.get_state("t1")
        assert state.attempt_count == 2

    def test_does_not_increment_on_success(self):
        rm = RetryManager()
        rm.record_attempt("t1", "", True)
        state = rm.get_state("t1")
        assert state.attempt_count == 0

    def test_records_last_error(self):
        rm = RetryManager()
        rm.record_attempt("t1", "first error", False)
        rm.record_attempt("t1", "second error", False)
        state = rm.get_state("t1")
        assert state.last_error == "second error"

    def test_records_history(self):
        rm = RetryManager()
        rm.record_attempt("t1", "err", False)
        state = rm.get_state("t1")
        assert len(state.retry_history) == 1
        assert state.retry_history[0]["success"] is False


class TestGetRetryPromptModifier:
    def test_empty_for_new_task(self):
        rm = RetryManager()
        assert rm.get_retry_prompt_modifier("t1") == ""

    def test_contains_error_on_first_retry(self):
        rm = RetryManager()
        rm.record_attempt("t1", "compile error", False)
        modifier = rm.get_retry_prompt_modifier("t1")
        assert "compile error" in modifier

    def test_contains_simplification_hint_after_many_retries(self):
        rm = RetryManager()
        for i in range(4):
            rm.record_attempt("t1", f"error {i}", False)
        modifier = rm.get_retry_prompt_modifier("t1")
        assert "different approach" in modifier or "simpler" in modifier or "completely" in modifier

    def test_contains_history_after_multiple_retries(self):
        rm = RetryManager()
        for i in range(3):
            rm.record_attempt("t1", f"error {i}", False)
        modifier = rm.get_retry_prompt_modifier("t1")
        assert "Attempt" in modifier


class TestResetState:
    def test_removes_state(self):
        rm = RetryManager()
        rm.record_attempt("t1", "err", False)
        rm.reset_state("t1")
        assert rm.get_state("t1") is None

    def test_allows_fresh_start_after_reset(self):
        rm = RetryManager()
        for _ in range(RetryManager.MAX_RETRIES):
            rm.record_attempt("t1", "err", False)
        rm.reset_state("t1")
        assert rm.should_retry("t1", "err") is True

    def test_reset_nonexistent_is_noop(self):
        rm = RetryManager()
        rm.reset_state("nonexistent")  # should not raise


class TestClearAll:
    def test_clears_all_states(self):
        rm = RetryManager()
        rm.record_attempt("t1", "e", False)
        rm.record_attempt("t2", "e", False)
        rm.clear_all()
        assert rm.get_state("t1") is None
        assert rm.get_state("t2") is None
