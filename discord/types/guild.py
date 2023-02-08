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
    Optional
)

from typing_extensions import (
    Literal,
    NotRequired,
    TypedDict
)

from .snowflake import SnowflakeID

DefaultMessageNotificationLevel = Literal[0, 1]
ExplicitContentFilterLevel = Literal[0, 1, 2]
MFALevel = Literal[0, 1]
AfkTimeout = Literal[60, 300, 900, 1800, 3600]
VerificationLevel = Literal[0, 1, 2, 3, 4]
GuildNSFWLevel = Literal[0, 1, 2, 3]
PremiumTier = Literal[0, 1, 2, 3]


class UnavailableGuild(TypedDict):
    id: SnowflakeID
    unavailable: bool


class Guild(TypedDict):
    id: SnowflakeID
    name: str
    icon: str
    splash: Optional[str]
    discovery_splash: Optional[str]
    owner: NotRequired[bool]
    owner_id: SnowflakeID
    permissions: NotRequired[str]
    afk_channel_id: Optional[SnowflakeID]
    afk_timeout: AfkTimeout
    widget_enabled: NotRequired[bool]
    widget_channel_id: NotRequired[Optional[SnowflakeID]]
    verification_level: VerificationLevel
    default_message_notifications: DefaultMessageNotificationLevel
    explicit_content_filter: ExplicitContentFilterLevel
    # roles: List[Role]
    # emojis: List[Emoji]
    # features: List[GuildFeature]
    mfa_level: MFALevel
    application_id: Optional[SnowflakeID]
    system_channel_id: Optional[SnowflakeID]
    system_channel_flags: int
    rules_channel_id: Optional[SnowflakeID]
    max_presences: NotRequired[Optional[int]]
    max_members: NotRequired[int]
    vanity_url_code: Optional[str]
    description: Optional[str]
    banner: Optional[str]
    premium_tier: PremiumTier
    premium_subscription_count: NotRequired[int]
    preferred_locale: str
    public_updates_channel_id: Optional[SnowflakeID]
    max_video_channel_users: NotRequired[int]
    approximate_member_count: NotRequired[int]
    approximate_presence_count: NotRequired[int]
    # welcome_screen: NotRequired[WelcomeScreen]
    # nsfw_level: GuildNSFWLevel
    # stickers: NotRequired[List[GuildSticker]]
    premium_progress_bar_enabled: bool
