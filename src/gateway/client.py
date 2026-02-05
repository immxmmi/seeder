import os
from typing import Any, Dict, Optional

import requests
from config.loader import ConnectorConfig
from utils.logger import Logger as log

SENSITIVE_HEADERS = {"authorization", "x-api-key", "cookie", "set-cookie"}
DEFAULT_TIMEOUT = 30


class ApiClient:
    """HTTP client for a specific source. Each source gets its own client instance."""

    def __init__(self, source: ConnectorConfig, verify=True):
        self.source = source
        self.timeout = int(os.getenv("API_TIMEOUT", DEFAULT_TIMEOUT))
        self.verify = verify

        self.base_url = source.host.rstrip("/")
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }

        token = None
        if source.token_env:
            token = os.getenv(source.token_env)
            if not token:
                log.warn("ApiClient", f"Token env var '{source.token_env}' not set for source '{source.name}'")

        if token:
            if source.auth_type.lower() == "bearer":
                self.headers["Authorization"] = f"Bearer {token}"
            elif source.auth_type.lower() == "basic":
                self.headers["Authorization"] = f"Basic {token}"
            elif source.auth_type.lower() == "apikey":
                self.headers["X-API-Key"] = token

        self._session: Optional[requests.Session] = None

        log.debug("ApiClient", f"Initialized for '{source.name}' -> {self.base_url}")

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def _mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        masked = {}
        for key, value in headers.items():
            if key.lower() in SENSITIVE_HEADERS:
                masked[key] = "***REDACTED***"
            else:
                masked[key] = value
        return masked

    def get(self, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}{endpoint}"
        log.debug("ApiClient", f"GET {url}")
        log.debug("ApiClient", f"timeout={self.timeout}s verify={self.verify}")
        log.debug("ApiClient", f"headers={self._mask_sensitive_headers(self.headers)}")

        try:
            response = self.session.get(
                url=url,
                headers=self.headers,
                verify=self.verify,
                timeout=self.timeout,
                **kwargs,
            )
        except requests.ConnectionError as e:
            log.error("ApiClient", f"Connection refused: {url}: {e}")
            raise
        except requests.Timeout as e:
            log.error("ApiClient", f"Timeout: {url}: {e}")
            raise
        except requests.RequestException as e:
            log.error("ApiClient", f"Request error: {url}: {e}")
            raise

        try:
            response.raise_for_status()
        except requests.HTTPError:
            log.error("ApiClient", f"HTTP {response.status_code} on GET {url} body={response.text}")
            raise

        log.debug(
            "ApiClient",
            f"status={response.status_code} content_type={response.headers.get('Content-Type')} length={len(response.text)}",
        )

        if not response.text or not response.text.strip():
            return {}

        try:
            return response.json()
        except ValueError:
            log.debug("ApiClient", "Non-JSON response received")
            return {"raw": response.text}
