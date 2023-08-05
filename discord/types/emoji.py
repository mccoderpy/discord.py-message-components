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
    Literal,
    TypedDict,
    NotRequired
)

from .snowflake import SnowflakeID, SnowflakeList
from .user import BaseUser

__all__ = (
    'PartialEmoji',
    'BaseEmoji',
)


class PartialEmoji(TypedDict):
    id: Optional[SnowflakeID]  # The ID of the emoji
    name: Optional[str]        # The emoji name
    animated: NotRequired[bool]  # Whether this emoji is animated


class BaseEmoji(TypedDict):
    id: Optional[SnowflakeID]          # The ID of the emoji
    name: Optional[str]                # The emoji name
    roles: NotRequired[SnowflakeList]  # The roles allowed to use this emoji
    user: NotRequired[BaseUser]        # The user that created this emoji
    require_colons: NotRequired[bool]  # Whether this emoji must be wrapped in colons
    managed: NotRequired[bool]         # Whether this emoji is managed
    animated: NotRequired[bool]        # Whether this emoji is animated
    available: NotRequired[bool]       # Whether this emoji can be used, may be false due to loss of Server Boosts
