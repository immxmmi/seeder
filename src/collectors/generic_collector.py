from typing import List, Dict, Any

from collectors.base_collector import BaseCollector
from config.loader import Config, ConnectorConfig
from gateway.client import ApiClient
from utils.logger import Logger as log


class GenericCollector(BaseCollector):
    """Generic REST API collector. Fetches data from any REST endpoint configured in settings.yaml."""

    def __init__(self, source: ConnectorConfig):
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

        response_type = type(response).__name__
        if isinstance(response, list):
            data = response
        elif isinstance(response, dict):
            wrapper_key = None
            for key in ["data", "items", "results", "records"]:
                if key in response:
                    data = response[key]
                    wrapper_key = key
                    break
            else:
                data = self._dict_to_list(response)
        else:
            log.warn("GenericCollector", f"Unexpected response type from '{self.source.name}': {type(response)}")
            return []

        if not isinstance(data, list):
            if isinstance(data, dict):
                data = self._dict_to_list(data)
            else:
                data = [data]

        log.info("GenericCollector", f"Collected {len(data)} items from '{self.source.name}'")
        log.debug(
            "GenericCollector",
            f"response_type={response_type} wrapper_key={wrapper_key if isinstance(response, dict) else None}",
        )

        if self.source.mapping_fields or self.source.defaults:
            data = [self._transform(self._preprocess(item)) for item in data]
            log.debug("GenericCollector", f"Applied mapping/defaults to {len(data)} items")

        return data

    def _transform(self, item: Dict[str, Any]) -> Dict[str, Any]:
        result = {}

        if self.source.mapping_fields:
            for mapping in self.source.mapping_fields:
                api_field = mapping.get("from")
                output_field = mapping.get("to")
                value = self._get_path(item, api_field)
                if value is not None or api_field in item:
                    result[output_field] = value
        else:
            result = dict(item)

        for key, value in self.source.defaults.items():
            if key not in result:
                result[key] = value

        return result

    def _preprocess(self, item: Dict[str, Any]) -> Dict[str, Any]:
        if not self.source.options:
            return item

        if self.source.options.get("flatten_preferred_version") is True:
            return self._flatten_preferred_version(item)

        return item

    @staticmethod
    def _flatten_preferred_version(item: Dict[str, Any]) -> Dict[str, Any]:
        preferred = item.get("preferred")
        versions = item.get("versions", {})
        if not preferred or not isinstance(versions, dict):
            return item

        preferred_entry = versions.get(preferred)
        if not isinstance(preferred_entry, dict):
            return item

        info = preferred_entry.get("info", {})
        out = dict(item)
        out["preferred_info"] = info
        out["preferred_spec"] = {
            "swaggerUrl": preferred_entry.get("swaggerUrl"),
            "swaggerYamlUrl": preferred_entry.get("swaggerYamlUrl"),
            "openapiVer": preferred_entry.get("openapiVer"),
            "link": preferred_entry.get("link"),
            "updated": preferred_entry.get("updated"),
            "added": preferred_entry.get("added"),
        }
        return out

    @staticmethod
    def _get_path(item: Dict[str, Any], path: str):
        if not path or "." not in path:
            return item.get(path)

        current = item
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    @staticmethod
    def _dict_to_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for key, value in data.items():
            if isinstance(value, dict):
                item = {"api_id": key}
                item.update(value)
                out.append(item)
            else:
                out.append({"api_id": key, "value": value})
        return out
