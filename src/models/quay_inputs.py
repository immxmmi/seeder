"""Pydantic models for Quay inputs.yaml (quay-provisioner format)."""

from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel


class OrganizationInput(BaseModel):
    name: str
    email: Optional[str] = None

    class Config:
        extra = "forbid"


class RobotAccountInput(BaseModel):
    organization: str
    robot_shortname: str
    description: Optional[str] = None

    class Config:
        extra = "forbid"


class TeamInput(BaseModel):
    organization: str
    team_name: str
    role: Literal["member", "creator", "admin"]
    description: Optional[str] = None

    class Config:
        extra = "forbid"


class TeamMemberInput(BaseModel):
    organization: str
    team_name: str
    member_name: str

    class Config:
        extra = "forbid"


class TeamRepoPermissionInput(BaseModel):
    organization: str
    team_name: str
    repository: str
    permission: Literal["read", "write", "admin"]

    class Config:
        extra = "forbid"


class DelegateInput(BaseModel):
    kind: Literal["team", "user"]
    name: str

    class Config:
        extra = "forbid"


class DefaultRepoPermissionInput(BaseModel):
    organization: str
    delegate: DelegateInput
    role: Literal["read", "write", "admin"]

    class Config:
        extra = "forbid"


class TeamLdapSyncInput(BaseModel):
    organization: str
    team_name: str
    group_dn: str

    class Config:
        extra = "forbid"


class TeamLdapUnsyncInput(BaseModel):
    organization: str
    team_name: str

    class Config:
        extra = "forbid"


class TeamSyncStatusInput(BaseModel):
    organization: str
    team_name: str

    class Config:
        extra = "forbid"


class TeamMemberInviteInput(BaseModel):
    organization: str
    team_name: str
    email: str

    class Config:
        extra = "forbid"


class TeamInviteRemoveInput(BaseModel):
    organization: str
    team_name: str
    email: str

    class Config:
        extra = "forbid"


class QuayInputs(BaseModel):
    """Root inputs.yaml model for quay-provisioner."""

    organizations: Optional[List[OrganizationInput]] = None
    robot_accounts: Optional[List[RobotAccountInput]] = None
    teams: Optional[List[TeamInput]] = None
    team_members: Optional[List[TeamMemberInput]] = None
    team_repo_permissions: Optional[List[TeamRepoPermissionInput]] = None
    team_repo_permissions_to_remove: Optional[List[TeamRepoPermissionInput]] = None
    default_repo_permissions: Optional[List[DefaultRepoPermissionInput]] = None
    default_repo_permissions_to_remove: Optional[List[DefaultRepoPermissionInput]] = None
    team_ldap_sync: Optional[List[TeamLdapSyncInput]] = None
    team_members_to_remove: Optional[List[TeamMemberInput]] = None
    team_ldap_unsync: Optional[List[TeamLdapUnsyncInput]] = None
    team_sync_status: Optional[List[TeamSyncStatusInput]] = None
    team_member_invites: Optional[List[TeamMemberInviteInput]] = None
    team_invites_to_remove: Optional[List[TeamInviteRemoveInput]] = None

    class Config:
        extra = "forbid"

    def to_output(self) -> Dict[str, Any]:
        """Convert to dict format for inputs.yaml output."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
