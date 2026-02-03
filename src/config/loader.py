import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import yaml

from utils.logger import Logger as log


class SourceConfig:
    """Configuration for a single data source, loaded from sources/*.yaml."""

    def __init__(self, data: dict, source_file: str = ""):
        self.source_file: str = source_file
        self.name: str = data["name"]
        self.enabled: bool = data.get("enabled", True)
        self.target_key: str = data["target_key"]

        # Connection
        conn = data.get("connection", {})
        self.host: str = conn.get("host", "").rstrip("/")
        self.auth_type: str = conn.get("auth_type", "bearer")
        self.token_env: str = conn.get("token_env", "")
        self.endpoint: str = conn.get("endpoint", "/")

        # Field mapping: API field name -> output field name
        self.mapping: Dict[str, str] = data.get("mapping", {})

        # Static default values to add to every item
        self.defaults: Dict[str, Any] = data.get("defaults", {})

    def __repr__(self):
        return f"SourceConfig(name={self.name}, host={self.host}, endpoint={self.endpoint})"


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

        config_file = Path(__file__).parent / "settings.yaml"

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        try:
            data = yaml.safe_load(config_file.read_text())
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}") from e

        if not data:
            raise ValueError("Configuration file is empty")

        # Debug
        debug_cfg = data.get("debug", {})
        self.debug = os.getenv("DEBUG_ENABLED", str(debug_cfg.get("enabled", "false"))).lower() == "true"
        log.configure(self.debug)

        # App
        app_cfg = data.get("app", {})
        self.version = os.getenv("APP_VERSION", app_cfg.get("version", "unknown"))

        # Load sources from sources/*.yaml
        sources_dir = Path(__file__).parent / "sources"
        self.sources: List[SourceConfig] = self._load_sources(sources_dir)

        # Output
        output_cfg = data.get("output", {})
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.output_file = Path(
            os.getenv("OUTPUT_FILE", output_cfg.get("file", str(BASE_DIR / "output" / "inputs.yaml")))
        )
        if not self.output_file.is_absolute():
            project_root = BASE_DIR.parent
            self.output_file = (project_root / self.output_file).resolve()

        # TLS
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
            log.debug("Config", f"Sources: {len(self.sources)}")
            log.debug("Config", f"Output file: {self.output_file}")
            log.debug("Config", f"TLS verify: {self.verify}")

    @staticmethod
    def _load_sources(sources_dir: Path) -> List[SourceConfig]:
        """Load all source definitions from sources/*.yaml."""
        sources = []

        if not sources_dir.exists():
            log.warn("Config", f"Sources directory not found: {sources_dir}")
            return sources

        for yaml_file in sorted(sources_dir.glob("*.yaml")):
            try:
                raw = yaml.safe_load(yaml_file.read_text())
                if not raw:
                    log.warn("Config", f"Empty source file: {yaml_file.name}")
                    continue
                source = SourceConfig(raw, source_file=yaml_file.name)
                sources.append(source)
                log.debug("Config", f"Loaded source: {source.name} ({yaml_file.name})")
            except (yaml.YAMLError, KeyError) as e:
                log.error("Config", f"Failed to load source {yaml_file.name}: {e}")

        return sources

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
