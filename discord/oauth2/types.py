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
from __future__ import annotations

from typing import (
    Dict,
    List,
    Optional
)

from typing_extensions import (
    Literal,
    NotRequired,
    TypedDict
)

from discord.types import (
    appinfo,
    integration,
    user,
    webhook
)


__all__ = (
    'AccessToken',
    'AccessTokenWithAbsoluteTime',
    'ClientCredentialsAccessToken',
    'ClientCredentialsAccessTokenWithAbsoluteTime',
    'Connection',
    'ConnectionService',
    'CurrentAuthorizationInfo',
    'IntegrationAccount',
    'PartialUser',
    'PartialGuildIntegration',
    'RoleConnection',
    'User'
)


VisibilityType = Literal[0, 1]
ConnectionService = Literal[
    'battlenet',
    'crunchyroll',
    'ebay',
    'epicgames',
    'facebook',
    'github',
    'instagram',
    'leagueoflegends',
    'paypal',
    'playstation',
    'reddit',
    'riotgames',
    'spotify',
    'skype',
    'steam',
    'tiktok',
    'twitch',
    'twitter',
    'xbox',
    'youtube'
]
PremiumType = Literal[0, 1, 2, 3]
RoleConnectionMetadataType = Literal[1, 2, 3, 4, 5, 6, 7, 8]


class _AccessToken(TypedDict):
    access_token: str
    token_type: str


class AccessToken(_AccessToken):
    refresh_token: str
    expires_in: int
    scope: str
    webhook: NotRequired[webhook.Webhook]


class AccessTokenWithAbsoluteTime(_AccessToken):
    refresh_token: str
    expires_at: str
    scopes: List[str]
    webhook_url: NotRequired[str]


class ClientCredentialsAccessToken(_AccessToken):
    expires_in: int
    scope: str
    webhook: NotRequired[webhook.Webhook]


class ClientCredentialsAccessTokenWithAbsoluteTime(_AccessToken):
    expires_at: str
    scopes: List[str]
    webhook_url: NotRequired[str]


class PartialUser(user.BaseUser):
    avatar_decoration: Optional[str]
    public_flags: NotRequired[int]


class User(user.User):
    mfa_enabled: NotRequired[bool]
    locale: NotRequired[str]
    verified: NotRequired[bool]
    email: NotRequired[Optional[str]]
    flags: NotRequired[int]
    premium_type: PremiumType


class CurrentAuthorizationInfo(TypedDict):
    application: appinfo.PartialAppInfo
    scopes: List[str]
    expires: str
    user: NotRequired[user.BaseUser]


class IntegrationAccount(TypedDict):
    id: str
    name: str


class PartialGuildIntegration(TypedDict):
    pass
    # TODO: Find out the structure of this


class Connection(TypedDict):
    id: str
    name: str
    type: ConnectionService
    revoked: NotRequired[bool]
    integrations: NotRequired[List[integration.PartialIntegration]]
    verified: bool
    friend_sync: bool
    show_activity: bool
    two_way_link: bool
    visibility: int


class RoleConnection(TypedDict):
    platform_name: Optional[str]
    platform_username: Optional[str]
    metadata: Dict[str, str]
