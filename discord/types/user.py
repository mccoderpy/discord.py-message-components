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
    TypedDict
)
from typing_extensions import (
    NotRequired
)

from .snowflake import SnowflakeID


class BaseUser(TypedDict):
    username: str
    public_flags: int
    id: SnowflakeID
    discriminator: str
    bot: bool
    avatar: str


class ClientUser(BaseUser):
    verified: bool
    mfa_enabled: bool
    flags: int


class User(BaseUser):
    system: NotRequired[bool]
    mfa_enabled: NotRequired[bool]
    banner: NotRequired[Optional[str]]
    accent_color: NotRequired[Optional[int]]
    locale: NotRequired[str]
    verified: NotRequired[bool]
    email: NotRequired[Optional[str]]
    flags: NotRequired[int]
    premium_type: NotRequired[int]
