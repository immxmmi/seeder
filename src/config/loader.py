import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterable

import yaml
from utils.logger import Logger as log


class ConnectorConfig:
    """Configuration for a single connector."""

    def __init__(self, data: dict, source_file: str = ""):
        self.source_file: str = source_file
        self.name: str = data["name"]
        self.enabled: bool = data.get("enabled", True)
        self.target_key: str = data.get("target_key", "")

        conn = data.get("connection", {})
        self.host: str = conn.get("host", "").rstrip("/")
        self.auth_type: str = conn.get("auth_type", "bearer")
        self.token_env: str = conn.get("token_env", "")
        self.endpoint: str = conn.get("endpoint", "/")

        raw_mapping = data.get("mapping", {})
        self.mapping_replace_object: Optional[str] = None
        self.mapping_fields: List[Dict[str, str]] = self._parse_mapping(raw_mapping)

        if not self.target_key and self.mapping_replace_object:
            self.target_key = self.mapping_replace_object
        elif self.mapping_replace_object and self.target_key != self.mapping_replace_object:
            log.warn(
                "Config",
                f"Connector '{self.name}': target_key '{self.target_key}' "
                f"differs from mapping.replace_object '{self.mapping_replace_object}'",
            )
        if not self.target_key:
            raise KeyError("target_key is required (or mapping.replace_object must be set)")

        self.defaults: Dict[str, Any] = data.get("defaults", {})
        self._validate()

    def __repr__(self):
        return f"ConnectorConfig(name={self.name}, host={self.host}, endpoint={self.endpoint})"

    def _validate(self) -> None:
        if not self.name:
            raise ValueError("connector.name is required")
        if not self.host:
            raise ValueError(f"connector '{self.name}': connection.host is required")
        if not self.endpoint:
            raise ValueError(f"connector '{self.name}': connection.endpoint is required")

        auth = (self.auth_type or "").lower()
        if auth not in {"bearer", "basic", "apikey", "none"}:
            raise ValueError(f"connector '{self.name}': auth_type must be bearer|basic|apikey|none")
        if auth in {"bearer", "basic", "apikey"} and not self.token_env:
            raise ValueError(f"connector '{self.name}': token_env is required for auth_type '{auth}'")

        if self.mapping_fields and not self.mapping_replace_object:
            raise ValueError(f"connector '{self.name}': mapping.replace_object is required")
        if self.mapping_replace_object and not self.mapping_fields:
            raise ValueError(f"connector '{self.name}': mapping.fields must not be empty")

    def _parse_mapping(self, raw_mapping: Any) -> List[Dict[str, str]]:
        """Normalize mapping to a list of {'from': ..., 'to': ...}."""
        if not raw_mapping:
            return []

        if isinstance(raw_mapping, dict) and "fields" in raw_mapping:
            self.mapping_replace_object = raw_mapping.get("replace_object")
            fields = raw_mapping.get("fields", [])
            return self._normalize_mapping_fields(fields)

        return []

    @staticmethod
    def _normalize_mapping_fields(fields: Iterable[Any]) -> List[Dict[str, str]]:
        normalized: List[Dict[str, str]] = []
        for item in fields:
            if not isinstance(item, dict):
                continue
            api_field = item.get("from")
            out_field = item.get("to")
            if api_field and out_field:
                normalized.append({"from": api_field, "to": out_field})
        return normalized


class Config:
    """Configuration singleton."""

    _instance: Optional["Config"] = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        default_config_dir = Path(__file__).parent
        config_file = Path(os.getenv("SEEDER_CONFIG_FILE", default_config_dir / "settings.yaml"))

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        try:
            data = yaml.safe_load(config_file.read_text())
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}") from e

        if not data:
            raise ValueError("Configuration file is empty")

        debug_cfg = data.get("debug", {})
        self.debug = os.getenv("DEBUG_ENABLED", str(debug_cfg.get("enabled", "false"))).lower() == "true"
        log.configure(self.debug)

        app_cfg = data.get("app", {})
        self.version = os.getenv("APP_VERSION", app_cfg.get("version", "unknown"))

        connectors_cfg = data.get("connectors")
        if connectors_cfg is None:
            raise ValueError("connectors must be defined in settings.yaml")
        self.sources: List[ConnectorConfig] = self._load_connectors(connectors_cfg)

        output_cfg = data.get("output", {})
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.output_file = Path(
            os.getenv("OUTPUT_FILE", output_cfg.get("file", str(BASE_DIR / "output" / "inputs.yaml")))
        )
        if not self.output_file.is_absolute():
            project_root = BASE_DIR.parent
            self.output_file = (project_root / self.output_file).resolve()

        disable_verify = os.getenv("DISABLE_TLS_VERIFY", "false").lower() == "true"
        ca_bundle = os.getenv("CA_BUNDLE", "")
        if disable_verify:
            self.verify = False
        elif ca_bundle:
            self.verify = ca_bundle
        else:
            self.verify = True

        if self.debug:
            log.debug("Config", f"Version: {self.version}")
            log.debug("Config", f"Connectors: {len(self.sources)}")
            log.debug("Config", f"Output file: {self.output_file}")
            log.debug("Config", f"TLS verify: {self.verify}")
            for c in self.sources:
                log.debug(
                    "Config",
                    f"Connector '{c.name}': enabled={c.enabled} target={c.target_key} "
                    f"host={c.host} endpoint={c.endpoint} auth={c.auth_type}",
                )
                log.debug(
                    "Config",
                    f"Connector '{c.name}': mapping_fields={len(c.mapping_fields)} "
                    f"replace_object={c.mapping_replace_object} defaults={list(c.defaults.keys())}",
                )

    @staticmethod
    @staticmethod
    def _load_connectors(connectors_cfg: Any) -> List[ConnectorConfig]:
        """Load connectors from a list in the main settings YAML."""
        sources: List[ConnectorConfig] = []

        if not isinstance(connectors_cfg, list):
            log.error("Config", "connectors must be a list")
            return sources

        for i, raw in enumerate(connectors_cfg, 1):
            if not isinstance(raw, dict):
                log.warn("Config", f"Invalid connector at index {i}")
                continue
            try:
                source = ConnectorConfig(raw, source_file="settings.yaml")
                sources.append(source)
                log.debug("Config", f"Loaded connector: {source.name}")
            except (KeyError, TypeError) as e:
                log.error("Config", f"Failed to load connector at index {i}: {e}")

        return sources

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
