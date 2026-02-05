"""Pydantic models for Notifier inputs (acs-provisioner format)."""

from typing import Optional, Dict, Any, Literal

from pydantic import BaseModel


class NotifierInput(BaseModel):
    """A single notifier entry in the inputs.yaml format expected by acs-provisioner."""
    id: Optional[str] = None
    name: str
    type: Literal[
        "jira",
        "email",
        "splunk",
        "syslog",
        "pagerduty",
        "generic",
        "cscc",
        "sumologic",
        "awsSecurityHub",
        "microsoftSentinel",
    ]
    uiEndpoint: Optional[str] = None
    labelKey: Optional[str] = None
    labelDefault: Optional[str] = None
    traits: Optional[Dict[str, str]] = None
    jira: Optional[Dict[str, Any]] = None
    email: Optional[Dict[str, Any]] = None
    splunk: Optional[Dict[str, Any]] = None
    syslog: Optional[Dict[str, Any]] = None
    pagerduty: Optional[Dict[str, Any]] = None
    generic: Optional[Dict[str, Any]] = None
    cscc: Optional[Dict[str, Any]] = None
    sumologic: Optional[Dict[str, Any]] = None
    awsSecurityHub: Optional[Dict[str, Any]] = None
    microsoftSentinel: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"

    def to_output(self) -> Dict[str, Any]:
        """Convert to the dict format for inputs.yaml output."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
