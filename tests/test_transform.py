"""Tests fuer das Mapping/Transform im GenericCollector."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.loader import SourceConfig
from collectors.generic_collector import GenericCollector


def _make_collector(mapping=None, defaults=None):
    """Helper: Erstellt einen GenericCollector ohne echten API-Client."""
    source = SourceConfig({
        "name": "test-source",
        "target_key": "items",
        "connection": {
            "host": "https://example.com",
            "endpoint": "/api/test",
        },
        "mapping": mapping or {},
        "defaults": defaults or {},
    })
    collector = GenericCollector.__new__(GenericCollector)
    collector.source = source
    return collector


# ── Mapping ──────────────────────────────────────────────


class TestMappingBasic:
    """Grundlegendes Feld-Mapping."""

    def test_simple_field_rename(self):
        c = _make_collector(mapping={"title": "name", "kind": "type"})
        result = c._transform({"title": "Jira-Sec", "kind": "jira"})
        assert result == {"name": "Jira-Sec", "type": "jira"}

    def test_unmapped_fields_are_excluded(self):
        c = _make_collector(mapping={"title": "name"})
        result = c._transform({"title": "Jira-Sec", "internal_id": "xyz", "debug": True})
        assert result == {"name": "Jira-Sec"}
        assert "internal_id" not in result
        assert "debug" not in result

    def test_missing_api_field_is_skipped(self):
        c = _make_collector(mapping={"title": "name", "description": "desc"})
        result = c._transform({"title": "Jira-Sec"})
        assert result == {"name": "Jira-Sec"}
        assert "desc" not in result

    def test_no_mapping_passes_all_fields(self):
        c = _make_collector(mapping={})
        result = c._transform({"title": "Jira-Sec", "kind": "jira", "extra": 42})
        assert result == {"title": "Jira-Sec", "kind": "jira", "extra": 42}


class TestMappingComplexValues:
    """Mapping mit verschachtelten/komplexen Werten."""

    def test_nested_dict_value(self):
        c = _make_collector(mapping={"config": "jira"})
        api_data = {"config": {"url": "https://jira.example.com", "project": "SEC"}}
        result = c._transform(api_data)
        assert result == {"jira": {"url": "https://jira.example.com", "project": "SEC"}}

    def test_list_value(self):
        c = _make_collector(mapping={"tags": "categories"})
        result = c._transform({"tags": ["REGISTRY", "SCANNER"]})
        assert result == {"categories": ["REGISTRY", "SCANNER"]}

    def test_null_value_is_mapped(self):
        c = _make_collector(mapping={"title": "name"})
        result = c._transform({"title": None})
        assert result == {"name": None}

    def test_empty_string_is_mapped(self):
        c = _make_collector(mapping={"title": "name"})
        result = c._transform({"title": ""})
        assert result == {"name": ""}

    def test_boolean_value(self):
        c = _make_collector(mapping={"active": "enabled"})
        result = c._transform({"active": False})
        assert result == {"enabled": False}


# ── Defaults ─────────────────────────────────────────────


class TestDefaults:
    """Statische Default-Werte."""

    def test_defaults_are_added(self):
        c = _make_collector(
            mapping={"title": "name"},
            defaults={"traits": {"origin": "IMPERATIVE"}},
        )
        result = c._transform({"title": "X"})
        assert result == {"name": "X", "traits": {"origin": "IMPERATIVE"}}

    def test_api_value_wins_over_default(self):
        c = _make_collector(
            mapping={"title": "name", "traits": "traits"},
            defaults={"traits": {"origin": "IMPERATIVE"}},
        )
        result = c._transform({"title": "X", "traits": {"origin": "CUSTOM"}})
        assert result["traits"] == {"origin": "CUSTOM"}

    def test_multiple_defaults(self):
        c = _make_collector(
            mapping={},
            defaults={"env": "prod", "region": "eu-west-1"},
        )
        result = c._transform({"title": "X"})
        assert result["env"] == "prod"
        assert result["region"] == "eu-west-1"
        assert result["title"] == "X"

    def test_empty_defaults(self):
        c = _make_collector(mapping={"title": "name"}, defaults={})
        result = c._transform({"title": "X"})
        assert result == {"name": "X"}


# ── Kombination ──────────────────────────────────────────


class TestMappingWithDefaults:
    """Mapping + Defaults zusammen."""

    def test_full_notifier_transform(self):
        c = _make_collector(
            mapping={
                "title": "name",
                "notification_type": "type",
                "ui_endpoint": "uiEndpoint",
                "label_key": "labelKey",
                "label_default": "labelDefault",
                "config": "jira",
            },
            defaults={
                "traits": {
                    "mutabilityMode": "ALLOW_MUTATE",
                    "visibility": "VISIBLE",
                    "origin": "IMPERATIVE",
                },
            },
        )

        api_item = {
            "title": "Jira-Security",
            "notification_type": "jira",
            "ui_endpoint": "https://acs.example.com",
            "label_key": "notifier.jira",
            "label_default": "Jira Security Notifier",
            "config": {
                "url": "https://jira.example.com",
                "username": "acs-service",
                "issueType": "Bug",
            },
            "internal_id": "abc-123",
            "created_at": "2025-01-01",
        }

        result = c._transform(api_item)

        assert result["name"] == "Jira-Security"
        assert result["type"] == "jira"
        assert result["uiEndpoint"] == "https://acs.example.com"
        assert result["labelKey"] == "notifier.jira"
        assert result["jira"]["url"] == "https://jira.example.com"
        assert result["traits"]["mutabilityMode"] == "ALLOW_MUTATE"
        assert "internal_id" not in result
        assert "created_at" not in result

    def test_full_integration_transform(self):
        c = _make_collector(
            mapping={
                "title": "name",
                "integration_type": "type",
                "category_list": "categories",
                "config": "quay",
            },
            defaults={},
        )

        api_item = {
            "title": "Quay-Internal",
            "integration_type": "quay",
            "category_list": ["REGISTRY"],
            "config": {"endpoint": "quay.example.com", "insecure": False},
            "internal_id": "xyz-789",
        }

        result = c._transform(api_item)

        assert result["name"] == "Quay-Internal"
        assert result["type"] == "quay"
        assert result["categories"] == ["REGISTRY"]
        assert result["quay"]["endpoint"] == "quay.example.com"
        assert "internal_id" not in result
