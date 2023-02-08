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
    Any,
    List,
    Dict,
    Optional,
    TypedDict,
)
from typing_extensions import Literal

from .appinfo import GatewayAppInfo
from .guild import UnavailableGuild
from .user import ClientUser


class GatewayPayload(TypedDict):
    op: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    d: Optional[Dict[str, Any]]
    s: Optional[int]
    t: Optional[str]


class ReadyEvent(TypedDict):
    v: int  # gateway version
    user: ClientUser
    shard: List[int]  # shard id, total shards
    session_id: str
    resume_gateway_url: str
    application: GatewayAppInfo
    guilds: List[UnavailableGuild]
    _trace: List[str]


# voice gateway
class VoiceGatewayPayload(TypedDict):
    op: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    d: Optional[Dict[str, Any]]
    s: Optional[int]
    t: Optional[str]
