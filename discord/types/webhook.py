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
    Optional
)

from typing_extensions import (
    Literal,
    NotRequired,
    TypedDict
)
from . import (
    channel,
    guild,
    user
)
from .snowflake import SnowflakeID

WebhookType = Literal[1, 2, 3]


class PartialWebhook(TypedDict):
    id: SnowflakeID
    type: WebhookType
    token: NotRequired[str]


class Webhook(PartialWebhook, total=False):
    guild_id: str
    channel_id: str
    user: user.User
    name: str
    avatar: str
    application_id: str
    source_guild: guild.PartialGuild
    source_channel: channel.PartialChannel
    url: str


class FollowedChannel(TypedDict):
    channel_id: SnowflakeID
    webhook_id: SnowflakeID
