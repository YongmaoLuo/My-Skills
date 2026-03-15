"""Unit tests for SubTask model."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task import SubTask


class TestSubTaskDefaults:
    def test_required_fields(self):
        t = SubTask(id="1", title="T", description="D", test_command="echo ok")
        assert t.id == "1"
        assert t.title == "T"
        assert t.description == "D"
        assert t.test_command == "echo ok"

    def test_default_status_is_pending(self):
        t = SubTask(id="1", title="T", description="D", test_command="echo ok")
        assert t.status == "pending"

    def test_default_error_fields_are_none_or_zero(self):
        t = SubTask(id="1", title="T", description="D", test_command="echo ok")
        assert t.error_count == 0
        assert t.last_error is None
        assert t.failure_reason is None
        assert t.updated_time is None


class TestSubTaskModelDump:
    def test_model_dump_includes_all_fields(self):
        t = SubTask(id="1", title="T", description="D", test_command="echo ok",
                    status="completed", error_count=2,
                    last_error="err", failure_reason="fatal reason")
        d = t.model_dump()
        assert d["id"] == "1"
        assert d["title"] == "T"
        assert d["description"] == "D"
        assert d["test_command"] == "echo ok"
        assert d["status"] == "completed"
        assert d["error_count"] == 2
        assert d["last_error"] == "err"
        assert d["failure_reason"] == "fatal reason"

    def test_model_dump_none_fields_included_by_default(self):
        t = SubTask(id="1", title="T", description="D", test_command="echo ok")
        d = t.model_dump()
        assert "updated_time" in d
        assert d["updated_time"] is None
        assert "last_error" in d
        assert "failure_reason" in d

    def test_model_dump_exclude_none(self):
        t = SubTask(id="1", title="T", description="D", test_command="echo ok")
        d = t.model_dump(exclude_none=True)
        # None fields should be omitted
        assert d.get("updated_time") is None  # value None but still present by design
        assert d.get("last_error") is None
