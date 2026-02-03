from typing import List, Dict, Any

from collectors.base_collector import BaseCollector
from config.loader import Config, SourceConfig
from gateway.client import ApiClient
from utils.logger import Logger as log


class GenericCollector(BaseCollector):
    """Generic REST API collector. Fetches data from any REST endpoint configured in settings.yaml."""

    def __init__(self, source: SourceConfig):
        super().__init__(source)
        cfg = Config()
        self.client = ApiClient(source, verify=cfg.verify)

    def collect(self) -> List[Dict[str, Any]]:
        log.info("GenericCollector", f"Collecting from '{self.source.name}' -> {self.source.endpoint}")

        try:
            response = self.client.get(self.source.endpoint)
        except Exception as e:
            log.error("GenericCollector", f"Failed to collect from '{self.source.name}': {e}")
            return []

        if response is None:
            log.warn("GenericCollector", f"No data returned from '{self.source.name}'")
            return []

        # Response can be a list directly or a dict with a data key
        if isinstance(response, list):
            data = response
        elif isinstance(response, dict):
            # Try common wrapper keys
            for key in ["data", "items", "results", "records"]:
                if key in response:
                    data = response[key]
                    break
            else:
                # Use the entire response as a single-item list
                data = [response]
        else:
            log.warn("GenericCollector", f"Unexpected response type from '{self.source.name}': {type(response)}")
            return []

        if not isinstance(data, list):
            data = [data]

        log.info("GenericCollector", f"Collected {len(data)} items from '{self.source.name}'")

        # Apply mapping and defaults
        if self.source.mapping or self.source.defaults:
            data = [self._transform(item) for item in data]
            log.debug("GenericCollector", f"Applied mapping/defaults to {len(data)} items")

        return data

    def _transform(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field mapping and defaults to a single item."""
        result = {}

        if self.source.mapping:
            # Only include mapped fields (explicit whitelist)
            for api_field, output_field in self.source.mapping.items():
                if api_field in item:
                    result[output_field] = item[api_field]
        else:
            # No mapping defined -> pass through all fields
            result = dict(item)

        # Apply defaults (don't overwrite values from API)
        for key, value in self.source.defaults.items():
            if key not in result:
                result[key] = value

        return result
