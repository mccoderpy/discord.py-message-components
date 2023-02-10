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

from typing_extensions import (Literal, NotRequired, TypedDict)

from ..appinfo import PartialAppInfo
from ..user import User

__all__ = (
    'AccessTokenResponse',
    'ApplicationRoleConnectionData',
    'ClientCredentialsAccessTokenResponse',
    'ConnectionData',
    'ConnectionService',
    'CurrentAuthorizationInfoResponse',
)

VisibilityType = Literal[0, 1]
ConnectionService = Literal[
    'battlenet',
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


class AccessTokenResponse(TypedDict):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str


class ClientCredentialsAccessTokenResponse(TypedDict):
    access_token: str
    token_type: str
    expires_in: int
    scope: str


class CurrentAuthorizationInfoResponse(TypedDict):
    application: PartialAppInfo
    scopes: List[str]
    expires: str
    user: NotRequired[User]


class ConnectionData(TypedDict):
    id: str
    name: str
    type: ConnectionService
    revoked: NotRequired[bool]
    integrations: List[Dict[str, str]]
    verified: bool
    friend_sync: bool
    show_activity: bool
    two_way_link: bool
    visibility: int


class ApplicationRoleConnectionData(TypedDict):
    platform_name: Optional[str]
    platform_username: Optional[str]
    metadata: Dict[str, str]
