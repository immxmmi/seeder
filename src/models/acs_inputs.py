"""Pydantic models for ACS inputs.yaml (acs-provisioner format)."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .integration_input import IntegrationInput
from .notifier_input import NotifierInput


class AcsInputs(BaseModel):
    """Root inputs.yaml model for acs-provisioner."""

    notifiers: Optional[List[NotifierInput]] = None
    integrations: Optional[List[IntegrationInput]] = None

    class Config:
        extra = "forbid"

    def to_output(self) -> Dict[str, Any]:
        """Convert to dict format for inputs.yaml output."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
