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
    Optional,
    Union
)
from typing_extensions import (
    TypedDict,
    NotRequired,
    Literal
)

from .snowflake import SnowflakeID
from .user import BaseUser

__all__ = (
    'IntegrationType',
    'IntegrationExpireBehavior',
    'IntegrationApplication',
    'IntegrationAccount',
    'PartialIntegration',
    'BaseIntegration',
    'StreamIntegration',
    'BotIntegration',
    'Integration'
)

IntegrationType = Literal['twitch', 'youtube', 'discord', 'guild_subscription']
IntegrationExpireBehavior = Literal[0, 1]


class IntegrationApplication(TypedDict):
    id: SnowflakeID
    name: str
    icon: Optional[str]
    description: str
    summary: str
    bot: NotRequired[BaseUser]


class IntegrationAccount(TypedDict):
    id: str
    name: str


class PartialIntegration(TypedDict):
    id: SnowflakeID
    name: str
    type: IntegrationType
    account: IntegrationAccount
    application_id: SnowflakeID


class BaseIntegration(PartialIntegration):
    enabled: bool
    syncing: bool
    synced_at: str
    user: BaseUser
    expire_behavior: IntegrationExpireBehavior
    expire_grace_period: int


class StreamIntegration(BaseIntegration):
    role_id: Optional[SnowflakeID]
    enable_emoticons: bool
    subscriber_count: int
    revoked: bool


class BotIntegration(BaseIntegration):
    application: IntegrationApplication


Integration = Union[BaseIntegration, StreamIntegration, BotIntegration]
