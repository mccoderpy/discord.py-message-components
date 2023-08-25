# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2021-present mccoderpy

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from typing import (
    List,
    Optional
)
from typing_extensions import (
    TypedDict,
    NotRequired,
    Literal
)

from .snowflake import SnowflakeID
from .user import User

__all__ = (
    'TeamMember',
    'Team',
    'GatewayAppInfo',
    'PartialAppInfo',
    'AppInfo',
)

TeamMembershipState = Literal[1, 2]
TeamRole = Literal['owner', 'admin', 'developer', 'read_only']

class TeamMember(TypedDict):
    membership_state: TeamMembershipState
    permissions: List[str]
    team_id: SnowflakeID
    user: User
    role: TeamRole


class Team(TypedDict):
    id: SnowflakeID
    name: str
    icon: Optional[str]
    members: List[TeamMember]
    owner_user_id: SnowflakeID


class GatewayAppInfo(TypedDict):
    id: SnowflakeID
    flags: int


class PartialAppInfo(TypedDict):
    id: SnowflakeID
    name: str
    icon: NotRequired[str]
    description: str
    type: int
    hook: bool
    bot_public: bool
    bot_require_code_grant: bool
    verify_key: str
    flags: NotRequired[int]
    tags: List[str]


class InstallParams(TypedDict):
    scopes: List[str]
    permissions: str


class AppInfo(PartialAppInfo):
    rpc_origins: NotRequired[List[str]]
    terms_of_service_url: NotRequired[str]
    privacy_policy_url: NotRequired[str]
    owner: NotRequired[User]
    team: Optional[Team]
    guild_id: NotRequired[SnowflakeID]
    primary_sku_id: NotRequired[SnowflakeID]
    slug: NotRequired[str]
    cover_image: NotRequired[str]
    install_params: NotRequired[InstallParams]
    custom_install_url: NotRequired[str]
    role_connections_verification_url: NotRequired[str]
    interactions_endpoint_url: NotRequired[str]
