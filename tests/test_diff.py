"""Tests fuer die Diff-Erkennung im YamlWriter."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from output.yaml_writer import YamlWriter


# ── Diff-Logik ───────────────────────────────────────────


class TestDiffDetection:
    """Erkennung von Aenderungen zwischen alt und neu."""

    def test_no_changes(self):
        old = {"notifiers": [{"name": "A", "type": "jira"}]}
        new = {"notifiers": [{"name": "A", "type": "jira"}]}
        assert YamlWriter.diff(old, new) == []

    def test_item_added(self):
        old = {"notifiers": [{"name": "A"}]}
        new = {"notifiers": [{"name": "A"}, {"name": "B"}]}
        changes = YamlWriter.diff(old, new)
        assert len(changes) == 1
        assert "+ [notifiers] added: B" in changes[0]

    def test_item_removed(self):
        old = {"notifiers": [{"name": "A"}, {"name": "B"}]}
        new = {"notifiers": [{"name": "A"}]}
        changes = YamlWriter.diff(old, new)
        assert len(changes) == 1
        assert "- [notifiers] removed: B" in changes[0]

    def test_item_changed(self):
        old = {"notifiers": [{"name": "A", "url": "old"}]}
        new = {"notifiers": [{"name": "A", "url": "new"}]}
        changes = YamlWriter.diff(old, new)
        assert len(changes) == 1
        assert "~ [notifiers] changed: A (url)" in changes[0]

    def test_multiple_fields_changed(self):
        old = {"notifiers": [{"name": "A", "url": "old", "type": "jira"}]}
        new = {"notifiers": [{"name": "A", "url": "new", "type": "email"}]}
        changes = YamlWriter.diff(old, new)
        assert len(changes) == 1
        assert "type" in changes[0]
        assert "url" in changes[0]

    def test_new_section(self):
        old = {"notifiers": [{"name": "A"}]}
        new = {"notifiers": [{"name": "A"}], "integrations": [{"name": "Q"}]}
        changes = YamlWriter.diff(old, new)
        assert len(changes) == 1
        assert "+ [integrations]" in changes[0]

    def test_section_removed(self):
        old = {"notifiers": [{"name": "A"}], "integrations": [{"name": "Q"}]}
        new = {"notifiers": [{"name": "A"}]}
        changes = YamlWriter.diff(old, new)
        assert len(changes) == 1
        assert "- [integrations]" in changes[0]

    def test_mixed_changes(self):
        old = {"notifiers": [{"name": "A", "url": "old"}, {"name": "B"}]}
        new = {"notifiers": [{"name": "A", "url": "new"}, {"name": "C"}]}
        changes = YamlWriter.diff(old, new)
        assert len(changes) == 3
        texts = " ".join(changes)
        assert "changed: A" in texts
        assert "removed: B" in texts
        assert "added: C" in texts

    def test_empty_to_data(self):
        changes = YamlWriter.diff({}, {"notifiers": [{"name": "A"}]})
        assert len(changes) == 1
        assert "+ [notifiers]" in changes[0]

    def test_data_to_empty(self):
        changes = YamlWriter.diff({"notifiers": [{"name": "A"}]}, {})
        assert len(changes) == 1
        assert "- [notifiers]" in changes[0]


# ── Write mit Diff ───────────────────────────────────────


class TestWriteWithDiff:
    """Schreiben nur bei Aenderungen."""

    def test_first_write_creates_file(self, tmp_path):
        out = tmp_path / "inputs.yaml"
        data = {"notifiers": [{"name": "A", "type": "jira"}]}
        assert YamlWriter.write(out, data) is True
        assert out.exists()

    def test_same_data_skips_write(self, tmp_path):
        out = tmp_path / "inputs.yaml"
        data = {"notifiers": [{"name": "A", "type": "jira"}]}
        YamlWriter.write(out, data)
        mtime_before = out.stat().st_mtime_ns
        assert YamlWriter.write(out, data) is False
        assert out.stat().st_mtime_ns == mtime_before

    def test_changed_data_writes(self, tmp_path):
        out = tmp_path / "inputs.yaml"
        data1 = {"notifiers": [{"name": "A", "type": "jira"}]}
        data2 = {"notifiers": [{"name": "A", "type": "email"}]}
        YamlWriter.write(out, data1)
        assert YamlWriter.write(out, data2) is True

    def test_creates_parent_dirs(self, tmp_path):
        out = tmp_path / "deep" / "nested" / "inputs.yaml"
        data = {"notifiers": [{"name": "A"}]}
        assert YamlWriter.write(out, data) is True
        assert out.exists()
