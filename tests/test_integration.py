"""Optional live HTTP integration test."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.loader import ConnectorConfig
from collectors.generic_collector import GenericCollector


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="set RUN_INTEGRATION_TESTS=true to enable live HTTP test",
)
def test_live_api_list():
    source = ConnectorConfig(
        {
            "name": "apis-guru",
            "target_key": "apis",
            "connection": {
                "host": "https://api.apis.guru",
                "auth_type": "none",
                "endpoint": "/v2/list.json",
            },
            "mapping": {},
        }
    )

    collector = GenericCollector(source)
    data = collector.collect()

    assert isinstance(data, list)
    assert len(data) > 0
