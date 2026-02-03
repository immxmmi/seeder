"""Pydantic models for Notifier inputs (acs-provisioner format)."""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class NotifierInput(BaseModel):
    """A single notifier entry in the inputs.yaml format expected by acs-provisioner."""
    name: str
    type: str
    uiEndpoint: Optional[str] = None
    labelKey: Optional[str] = None
    labelDefault: Optional[str] = None
    traits: Optional[Dict[str, str]] = None

    class Config:
        extra = "allow"

    def to_output(self) -> Dict[str, Any]:
        """Convert to the dict format for inputs.yaml output."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
