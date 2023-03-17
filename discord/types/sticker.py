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
    List,
    Optional
)

from typing_extensions import (
    Literal,
    NotRequired,
    TypedDict
)

from .snowflake import SnowflakeID
from .user import BaseUser

__all__ = (
    'StickerPack',
    'Sticker',
    'GuildSticker'
)

StickerFormatType = Literal[1, 2, 3, 4]


class StickerPack(TypedDict):
    id: SnowflakeID
    stickers: List[Sticker]
    name: str
    sku_id: SnowflakeID
    cover_sticker_id: NotRequired[SnowflakeID]
    description: str
    banner_asset_id: NotRequired[SnowflakeID]


class Sticker(TypedDict):
    id: SnowflakeID
    pack_id: NotRequired[SnowflakeID]
    type: Literal[1]
    name: str
    description: Optional[str]
    tags: str
    format_type: StickerFormatType
    sort_value: NotRequired[int]


class GuildSticker(TypedDict):
    id: SnowflakeID
    type: Literal[2]
    name: str
    description: Optional[str]
    tags: str
    format_type: StickerFormatType
    available: bool
    guild_id: SnowflakeID
    user: NotRequired[BaseUser]
