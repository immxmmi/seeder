"""Pydantic models for Integration inputs (acs-provisioner format)."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class IntegrationInput(BaseModel):
    """A single integration entry in the inputs.yaml format expected by acs-provisioner."""
    name: str
    type: str
    categories: Optional[List[str]] = None

    class Config:
        extra = "allow"

    def to_output(self) -> Dict[str, Any]:
        """Convert to the dict format for inputs.yaml output."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
