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

from .channel import GuildChannel
from .emoji import BaseEmoji
from .snowflake import SnowflakeID
from .sticker import GuildSticker

__all__ = (
    'PermissionFlags',
    'UnavailableGuild',
    'PartialGuild',
    'Guild',
    'GuildPreview',
    'GuildWidget',
    'GuildWidgetSettings',
    'Role',
    'RoleTag',
    'WelcomeScreen',
    'WelcomeScreenChannel',
)

DefaultMessageNotificationLevel = Literal[0, 1]
ExplicitContentFilterLevel = Literal[0, 1, 2]
MFALevel = Literal[0, 1]
AfkTimeout = Literal[60, 300, 900, 1800, 3600]
VerificationLevel = Literal[0, 1, 2, 3, 4]
GuildNSFWLevel = Literal[0, 1, 2, 3]
PremiumTier = Literal[0, 1, 2, 3]
OnlineStatus = Literal['online', 'idle', 'dnd', 'offline']
GuildFeature = Literal[
    'ANIMATED_BANNER',
    'ANIMATED_ICON',
    'APPLICATION_COMMAND_PERMISSIONS_V2',
    'AUTO_MODERATION',
    'BANNER',
    'COMMERCE',
    'COMMUNITY',
    'DISCOVERABLE',
    'ENABLED_DISCOVERABLE_BEFORE',
    'FORCE_RELAY',
    'RELAY_ENABLED',
    'INVITE_SPLASH',
    'MEMBER_VERIFICATION_GATE_ENABLED',
    'MORE_EMOJI',
    'NEWS',
    'PARTNERED',
    'VERIFIED',
    'VANITY_URL',
    'VIP_REGIONS',
    'WELCOME_SCREEN_ENABLED',
    'DISCOVERY_DISABLED',
    'PREVIEW_ENABLED',
    'MORE_STICKERS',
    'MONETIZATION_ENABLED',
    'TICKETING_ENABLED',
    'HUB',
    'LINKED_TO_HUB',
    'HAS_DIRECTORY_ENTRY',
    'THREE_DAY_THREAD_ARCHIVE',
    'SEVEN_DAY_THREAD_ARCHIVE',
    'PRIVATE_THREADS',
    'THREADS_ENABLED',
    'ROLE_ICONS',
    'INTERNAL_EMPLOYEE_ONLY',
    'PREMIUM_TIER_3_OVERRIDE',
    'FEATUREABLE',
    'MEMBER_PROFILES'
    'APPEALABLE',
    'ROLE_SUBSCRIPTIONS_ENABLED',
    'ROLE_SUBSCRIPTIONS_ENABLED_FOR_PURCHASE'
]
PermissionFlags = Literal[
    'create_instant_invite',
    'kick_members',
    'ban_members',
    'administrator',
    'manage_channels',
    'manage_guild',
    'add_reactions',
    'view_audit_log',
    'priority_speaker',
    'stream',
    'read_messages',
    'send_messages',
    'send_tts_messages',
    'manage_messages',
    'embed_links',
    'attach_files',
    'read_message_history',
    'mention_everyone',
    'external_emojis',
    'view_guild_insights',
    'connect',
    'speak',
    'mute_members',
    'deafen_members',
    'move_members',
    'use_voice_activation',
    'change_nickname',
    'manage_nicknames',
    'manage_roles',
    'manage_webhooks',
    'manage_expressions',
    'create_expressions',
    'use_slash_commands',
    'request_to_speak',
    'manage_events',
    'create_events',
    'manage_threads',
    'create_public_threads',
    'create_private_threads',
    'use_external_stickers',
    'send_messages_in_threads',
    'start_embedded_activities',
    'moderate_members',
    'view_creator_monetization_analytics',
    'use_soundboard',
    'use_external_sounds',
    'send_voice_messages'
]



class UnavailableGuild(TypedDict):
    id: SnowflakeID
    unavailable: bool


class PartialGuild(TypedDict):
    id: SnowflakeID
    name: str
    features: List[str]
    icon: NotRequired[str]
    owner: NotRequired[bool]
    permissions: NotRequired[str]


class RoleTag(TypedDict):
    bot_id: NotRequired[SnowflakeID]
    integration_id: NotRequired[SnowflakeID]
    premium_subscriber: NotRequired[Literal[None]]
    subscription_listing_id: NotRequired[SnowflakeID]
    available_for_purchase: NotRequired[Literal[None]]
    guild_connection: NotRequired[Literal[None]]


class Role(TypedDict):
    id: SnowflakeID
    name: str
    color: int
    hoist: bool
    icon: NotRequired[Optional[str]]
    unicode_emoji: NotRequired[Optional[str]]
    position: int
    permissions: str
    mentionable: bool
    tags: NotRequired[RoleTag]


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
    roles: List[Role]
    emojis: List[BaseEmoji]
    features: List[GuildFeature]
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
    welcome_screen: NotRequired[WelcomeScreen]
    nsfw_level: GuildNSFWLevel
    stickers: NotRequired[List[GuildSticker]]
    premium_progress_bar_enabled: bool


class WelcomeScreenChannel(TypedDict):
    channel_id: SnowflakeID
    description: str
    emoji_id: Optional[SnowflakeID]
    emoji_name: Optional[str]


class WelcomeScreen(TypedDict):
    description: str
    welcome_channels: List[WelcomeScreenChannel]


class GuildPreview(TypedDict):
    id: SnowflakeID
    name: str
    icon: Optional[str]
    splash: Optional[str]
    discovery_splash: Optional[str]
    emojis: List[BaseEmoji]
    features: List[GuildFeature]
    approximate_member_count: int
    approximate_presence_count: int
    description: Optional[str]
    stickers: List[GuildSticker]


class GuildWidgetSettings(TypedDict):
    enabled: bool
    channel_id: Optional[SnowflakeID]


class GuildWidgetUser(TypedDict):
    id: SnowflakeID
    username: str
    discriminator: Literal['0000']
    avatar: Literal[None]
    status: OnlineStatus
    bot: bool
    avatar_url: str


class GuildWidget(TypedDict):
    id: SnowflakeID
    name: str
    instant_invite: Optional[str]
    channels: List[GuildChannel]
    members: List[GuildWidgetUser]
    presence_count: int
