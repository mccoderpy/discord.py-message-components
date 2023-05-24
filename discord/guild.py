# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz & (c) 2021-present mccoderpy

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

import copy
from datetime import datetime
from typing import (
    Union,
    Optional,
    overload,
    List,
    Tuple,
    Dict,
    Any,
    Awaitable,
    Iterable,
    Iterator,
    NamedTuple,
    TYPE_CHECKING
)
from typing_extensions import Literal

if TYPE_CHECKING:
    from os import PathLike
    from .state import ConnectionState
    from .abc import Snowflake, GuildChannel
    from .ext.commands import Cog
    from .automod import AutoModRule
    from .voice_client import VoiceProtocol
    from .template import Template
    from .webhook import Webhook
    from .application_commands import ApplicationCommand, SlashCommandOption, SubCommandGroup, SubCommand

from . import utils
from .file import UploadFile
from .role import Role
from .member import Member, VoiceState
from .emoji import Emoji
from .errors import InvalidData
from .permissions import PermissionOverwrite, Permissions
from .colour import Colour
from .errors import InvalidArgument, ClientException
from .channel import *
from .enums import (
    VoiceRegion,
    ChannelType,
    Locale,
    VerificationLevel,
    ContentFilter,
    NotificationLevel,
    EventEntityType,
    AuditLogAction,
    AutoModTriggerType,
    AutoModEventType,
    AutoArchiveDuration,
    IntegrationType,
    try_enum
)
from .mixins import Hashable
from .scheduled_event import GuildScheduledEvent
from .user import User
from .invite import Invite
from .iterators import AuditLogIterator, MemberIterator, BanIterator, BanEntry
from .welcome_screen import *
from .widget import Widget
from .asset import Asset
from .flags import SystemChannelFlags
from .integrations import _integration_factory, Integration
from .sticker import GuildSticker
from .automod import AutoModRule, AutoModTriggerMetadata, AutoModAction
from .application_commands import SlashCommand, MessageCommand, UserCommand, Localizations

MISSING = utils.MISSING

__all__ = (
    'GuildFeatures',
    'Guild',
)


class _GuildLimit(NamedTuple):
    emoji: int
    sticker: int
    bitrate: float
    filesize: int


async def default_callback(interaction, *args, **kwargs):
    await interaction.respond(
        'This command has no callback set.'
        'Probably something is being tested with him and he is not yet fully developed.',
        hidden=True
    )


class GuildFeatures(Iterable[str], dict):
    """
    Represents a guild's features.
    
    This class mainly exists to make it easier to edit a guild's features.
    
    .. versionadded:: 2.0
    
    .. container:: operations
    
        .. describe:: 'FEATURE_NAME' in features
        
            Checks if the guild has the feature.
        
        .. describe:: features.FEATURE_NAME
        
            Checks if the guild has the feature. Returns ``False`` if it doesn't.
        
        .. describe:: features.FEATURE_NAME = True
        
            Enables the feature in the features object, but does not enable it in the guild itself except if you pass it to :meth:`Guild.edit`.
        
        .. describe:: features.FEATURE_NAME = False
        
            Disables the feature in the features object, but does not disable it in the guild itself except if you pass it to :meth:`Guild.edit`.
        
        .. describe:: del features.FEATURE_NAME
        
            The same as ``features.FEATURE_NAME = False``
        
        .. describe:: features.parsed()
        
            Returns a list of all features that are/should be enabled.
        
        .. describe:: features.merge(other)
        
            Returns a new object with the features of both objects merged.
            If a feature is missing in the other object, it will be ignored.
        
        .. describe:: features == other
        
            Checks if two feature objects are equal.
        
        .. describe:: features != other
        
            Checks if two feature objects are not equal.
        
        .. describe:: iter(features)
        
            Returns an iterator over the enabled features.
    """
    def __init__(self, /, initial: List[str] = [], **features: bool):
        """
        Parameters
        -----------
        initial: :class:`list`
            The initial features to set.
        **features: :class:`bool`
            The features to set. If the value is ``True`` then the feature is/will be enabled.
            If the value is ``False`` then the feature will be disabled.
        """
        for feature in initial:
            features[feature] = True
        self.__dict__.update(features)
    
    def __iter__(self) -> Iterator[str]:
        return [feature for feature, value in self.__dict__.items() if value is True].__iter__()
    
    def __contains__(self, item: str) -> bool:
        return item in self.__dict__ and self.__dict__[item] is True
    
    def __getattr__(self, item: str) -> bool:
        return self.__dict__.get(item, False)
    
    def __setattr__(self, key: str, value: bool) -> None:
        self.__dict__[key] = value
    
    def __delattr__(self, item: str) -> None:
        self.__dict__[item] = False
        
    def __repr__(self) -> str:
        return f'<GuildFeatures {self.__dict__!r}>'
    
    def __str__(self) -> str:
        return str(self.__dict__)
    
    def keys(self) -> Iterator[str]:
        return self.__dict__.keys().__iter__()
    
    def values(self) -> Iterator[bool]:
        return self.__dict__.values().__iter__()
    
    def items(self) -> Iterator[Tuple[str, bool]]:
        return self.__dict__.items().__iter__()
    
    def merge(self, other: GuildFeatures) -> GuildFeatures:
        base = copy.copy(self.__dict__)
        
        for key, value in other.items():
            base[key] = value
            
        return GuildFeatures(**base)
    
    def parsed(self) -> List[str]:
        return [name for name, value in self.__dict__.items() if value is True]
    
    def __eq__(self, other: GuildFeatures) -> bool:
        current = self.__dict__
        other = other.__dict__
        
        all_keys = set(current.keys()) | set(other.keys())
        
        for key in all_keys:
            try:
                current_value = current[key]
            except KeyError:
                if other[key] is True:
                    return False
            else:
                try:
                    other_value = other[key]
                except KeyError:
                    pass
                else:
                    if current_value != other_value:
                        return False
        
        return True
    
    def __ne__(self, other: GuildFeatures) -> bool:
        return not self.__eq__(other)


class Guild(Hashable):
    """Represents a Discord guild.

    This is referred to as a "server" in the official Discord UI.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    Attributes
    ----------
    name: :class:`str`
        The guild name.
    emojis: Tuple[:class:`Emoji`, ...]
        All emojis that the guild owns.
    afk_timeout: :class:`int`
        The timeout to get sent to the AFK channel.
    afk_channel: Optional[:class:`VoiceChannel`]
        The channel that denotes the AFK channel. ``None`` if it doesn't exist.
    icon: Optional[:class:`str`]
        The guild's icon.
    id: :class:`int`
        The guild's ID.
    owner_id: :class:`int`
        The guild owner's ID. Use :attr:`Guild.owner` instead.
    unavailable: :class:`bool`
        Indicates if the guild is unavailable. If this is ``True`` then the
        reliability of other attributes outside of :attr:`Guild.id` is slim, and they might
        all be ``None``. It is best to not do anything with the guild if it is unavailable.

        Check the :func:`on_guild_unavailable` and :func:`on_guild_available` events.
    max_presences: Optional[:class:`int`]
        The maximum amount of presences for the guild.
    max_members: Optional[:class:`int`]
        The maximum amount of members for the guild.

        .. note::

            This attribute is only available via :meth:`.Client.fetch_guild`.
    max_video_channel_users: Optional[:class:`int`]
        The maximum amount of users in a video channel.

        .. versionadded:: 1.4
    banner: Optional[:class:`str`]
        The guild's banner.
    description: Optional[:class:`str`]
        The guild's description.
    mfa_level: :class:`int`
        Indicates the guild's two-factor authorisation level. If this value is 0 then
        the guild does not require 2FA for their administrative members. If the value is
        1 then they do.
    verification_level: :class:`VerificationLevel`
        The guild's verification level.
    explicit_content_filter: :class:`ContentFilter`
        The guild's explicit content filter.
    default_notifications: :class:`NotificationLevel`
        The guild's notification settings.
    features: List[:class:`str`]
        A list of features that the guild has. They are currently as follows:

        - ``VIP_REGIONS``: Guild has VIP voice regions
        - ``VANITY_URL``: Guild can have a vanity invite URL (e.g. discord.gg/discord-api)
        - ``INVITE_SPLASH``: Guild's invite page can have a special splash.
        - ``VERIFIED``: Guild is a verified server.
        - ``PARTNERED``: Guild is a partnered server.
        - ``MORE_EMOJI``: Guild is allowed to have more than 50 custom emoji.
        - ``MORE_STICKER``: Guild is allowed to have more than 60 custom sticker.
        - ``DISCOVERABLE``: Guild shows up in Server Discovery.
        - ``FEATURABLE``: Guild is able to be featured in Server Discovery.
        - ``COMMUNITY``: Guild is a community server.
        - ``PUBLIC``: Guild is a public guild.
        - ``NEWS``: Guild can create news channels.
        - ``BANNER``: Guild can upload and use a banner (i.e. :meth:`banner_url`).
        - ``ANIMATED_ICON``: Guild can upload an animated icon.
        - ``PUBLIC_DISABLED``: Guild cannot be public.
        - ``WELCOME_SCREEN_ENABLED``: Guild has enabled the welcome screen
        - ``MEMBER_VERIFICATION_GATE_ENABLED``: Guild has Membership Screening enabled.
        - ``PREVIEW_ENABLED``: Guild can be viewed before being accepted via Membership Screening.

    splash: Optional[:class:`str`]
        The guild's invite splash.
    premium_tier: :class:`int`
        The premium tier for this guild. Corresponds to "Nitro Server" in the official UI.
        The number goes from 0 to 3 inclusive.
    premium_subscription_count: :class:`int`
        The number of "boosts" this guild currently has.
    preferred_locale: Optional[:class:`str`]
        The preferred locale for the guild. Used when filtering Server Discovery
        results to a specific language.
    discovery_splash: :class:`str`
        The guild's discovery splash.
        .. versionadded:: 1.3
    premium_progress_bar_enabled: :class:`bool`
        Whether the guild has the boost progress bar enabled.
    """

    __slots__ = ('afk_timeout', 'afk_channel', '_members', '_channels', 'icon',
                 'name', 'id', 'unavailable', 'banner', 'region', '_state',
                 '_application_commands', '_roles', '_events', '_member_count', '_large',
                 'owner_id', 'mfa_level', 'emojis', 'features',
                 'verification_level', 'explicit_content_filter', 'splash',
                 '_voice_states', '_system_channel_id', 'default_notifications',
                 'description', 'max_presences', 'max_members', 'max_video_channel_users',
                 'premium_tier', 'premium_subscription_count', '_system_channel_flags',
                 'preferred_locale', 'discovery_splash', '_rules_channel_id',
                 '_public_updates_channel_id', 'premium_progress_bar_enabled',
                 '_welcome_screen', 'stickers', '_automod_rules')

    _PREMIUM_GUILD_LIMITS = {
        None: _GuildLimit(emoji=50, sticker=5, bitrate=96e3, filesize=8388608),
        0: _GuildLimit(emoji=50, sticker=5, bitrate=96e3, filesize=8388608),
        1: _GuildLimit(emoji=100, sticker=15, bitrate=128e3, filesize=8388608),
        2: _GuildLimit(emoji=150, sticker=30, bitrate=256e3, filesize=52428800),
        3: _GuildLimit(emoji=250, sticker=60, bitrate=384e3, filesize=104857600),
    }

    def __init__(self, *, data, state: ConnectionState):
        self._channels: Dict[int, Union[GuildChannel, ThreadChannel]] = {}
        self._members: Dict[int, Member] = {}
        self._events: Dict[int, GuildScheduledEvent] = {}
        self._automod_rules: Dict[int, AutoModRule] = {}
        self._voice_states: Dict[int, VoiceState] = {}
        self._state: ConnectionState = state
        self._application_commands: Dict[int, ApplicationCommand] = {}
        self._from_data(data)

    def _add_channel(self, channel: Union[GuildChannel, ThreadChannel]):
        self._channels[channel.id] = channel

    def _remove_channel(self, channel: Union[GuildChannel, ThreadChannel]):
        self._channels.pop(channel.id, None)

    def _add_thread(self, thread: ThreadChannel):
        self._channels[thread.id] = thread
        thread.parent_channel._add_thread(thread)

    def _remove_thread(self, thread: ThreadChannel):
        self._channels.pop(thread.id, None)
        try:
            thread.parent_channel._remove_thread(thread)
        except AttributeError:  # parent channel was deleted
            pass

    def _add_post(self, post: ForumPost):
        self._channels[post.id] = post
        post.parent_channel._add_post(post)

    def _remove_post(self, post: ForumPost):
        self._channels.pop(post.id, None)
        try:
            post.parent_channel._remove_post(post)
        except AttributeError:  # parent channel was deleted
            pass

    def _add_event(self, event: GuildScheduledEvent):
        self._events[event.id] = event

    def _remove_event(self, event: GuildScheduledEvent):
        self._events.pop(event.id, None)

    def _add_automod_rule(self, rule: AutoModRule):
        self._automod_rules[rule.id] = rule

    def _remove_automod_rule(self, rule: AutoModRule):
        self._automod_rules.pop(rule.id, None)

    def _voice_state_for(self, user_id: int):
        return self._voice_states.get(user_id)

    def _add_member(self, member: Member):
        self._members[member.id] = member

    def _remove_member(self, member: Member):
        self._members.pop(member.id, None)

    def __str__(self):
        return self.name or ''

    def __repr__(self):
        attrs = (
            'id', 'name', 'shard_id', 'chunked'
        )
        resolved = ['%s=%r' % (attr, getattr(self, attr)) for attr in attrs]
        resolved.append('member_count=%r' % getattr(self, '_member_count', None))
        return f"<Guild {' '.join(resolved)}>"

    def _update_voice_state(self, data, channel_id):
        user_id = int(data['user_id'])
        channel = self.get_channel(channel_id)
        try:
            # check if we should remove the voice state from cache
            if channel is None:
                after = self._voice_states.pop(user_id)
            else:
                after = self._voice_states[user_id]

            before = copy.copy(after)
            after._update(data, channel)
        except KeyError:
            # if we're here then we're getting added into the cache
            after = VoiceState(data=data, channel=channel)
            before = VoiceState(data=data, channel=None)
            self._voice_states[user_id] = after

        member = self.get_member(user_id)
        if member is None:
            try:
                member = Member(data=data['member'], state=self._state, guild=self)
            except KeyError:
                member = None

        return member, before, after

    def _add_role(self, role: Role):
        # roles get added to the bottom (position 1, pos 0 is @everyone)
        # so since self.roles has the @everyone role, we can't increment
        # its position because it's stuck at position 0. Luckily x += False
        # is equivalent to adding 0. So we cast the position to a bool and
        # increment it.
        for r in self._roles.values():
            r.position += (not r.is_default())

        self._roles[role.id] = role

    def _remove_role(self, role_id: int) -> Role:
        # this raises KeyError if it fails..
        role = self._roles.pop(role_id)

        # since it didn't, we can change the positions now
        # basically the same as above except we only decrement
        # the position if we're above the role we deleted.
        for r in self._roles.values():
            r.position -= r.position > role.position

        return role

    def _from_data(self, guild):
        # according to Stan, this is always available even if the guild is unavailable
        # I don't have this guarantee when someone updates the guild.
        member_count = guild.get('member_count', None)
        if member_count is not None:
            self._member_count = member_count

        self.name = guild.get('name')
        self.region = try_enum(VoiceRegion, guild.get('region'))
        self.verification_level = try_enum(VerificationLevel, guild.get('verification_level'))
        self.default_notifications = try_enum(NotificationLevel, guild.get('default_message_notifications'))
        self.explicit_content_filter = try_enum(ContentFilter, guild.get('explicit_content_filter', 0))
        self.afk_timeout = guild.get('afk_timeout')
        self.icon = guild.get('icon')
        self.banner = guild.get('banner')
        self.unavailable = guild.get('unavailable', False)
        self.id = int(guild['id'])
        self._roles = {}
        state = self._state  # speed up attribute access
        for r in guild.get('roles', []):
            role = Role(guild=self, data=r, state=state)
            self._roles[role.id] = role
        for e in guild.get('guild_scheduled_events', []):
            state.store_event(guild=self, data=e)
        self.mfa_level = guild.get('mfa_level')
        self.emojis = tuple(map(lambda d: state.store_emoji(self, d), guild.get('emojis', [])))
        self.features = guild.get('features', [])
        self.splash = guild.get('splash')
        self._system_channel_id = utils._get_as_snowflake(guild, 'system_channel_id')
        self.description = guild.get('description')
        self.max_presences = guild.get('max_presences')
        self.max_members = guild.get('max_members')
        self.max_video_channel_users = guild.get('max_video_channel_users')
        self.premium_tier = guild.get('premium_tier', 0)
        self.premium_subscription_count = guild.get('premium_subscription_count') or 0
        self._system_channel_flags = guild.get('system_channel_flags', 0)
        self.preferred_locale = try_enum(Locale, guild.get('preferred_locale'))
        self.discovery_splash = guild.get('discovery_splash')
        self._rules_channel_id = utils._get_as_snowflake(guild, 'rules_channel_id')
        self._public_updates_channel_id = utils._get_as_snowflake(guild, 'public_updates_channel_id')
        self.premium_progress_bar_enabled: bool = guild.get('premium_progress_bar_enabled')
        cache_online_members = self._state.member_cache_flags.online
        cache_joined = self._state.member_cache_flags.joined
        self_id = self._state.self_id
        for mdata in guild.get('members', []):
            member = Member(data=mdata, guild=self, state=state)
            if cache_joined or (cache_online_members and member.raw_status != 'offline') or member.id == self_id:
                self._add_member(member)

        self._sync(guild)
        self._large = None if member_count is None else self._member_count >= 250

        self.owner_id = utils._get_as_snowflake(guild, 'owner_id')
        self.afk_channel = self.get_channel(utils._get_as_snowflake(guild, 'afk_channel_id'))
        if welcome_screen := guild.get('welcome_screen', None):
            self._welcome_screen = WelcomeScreen(guild=self, state=self._state, data=welcome_screen)
        else:
            self._welcome_screen = None
        self.stickers: Tuple['GuildSticker'] = tuple(map(lambda d: state.store_sticker(d), guild.get('stickers', [])))  # type: ignore
        for obj in guild.get('voice_states', []):
            self._update_voice_state(obj, int(obj['channel_id']))

    def _sync(self, data):
        try:
            self._large = data['large']
        except KeyError:
            pass

        empty_tuple = tuple()
        for presence in data.get('presences', []):
            user_id = int(presence['user']['id'])
            member = self.get_member(user_id)
            if member is not None:
                member._presence_update(presence, empty_tuple)

        if 'channels' in data:
            channels = data['channels']
            for c in channels:
                factory, ch_type = _channel_factory(c['type'])
                if factory:
                    self._add_channel(factory(guild=self, data=c, state=self._state))

        if 'threads' in data:
            threads = data['threads']
            for t in threads:
                factory, ch_type = _channel_factory(t['type'])
                if factory:
                    parent_channel = self.get_channel(int(t['parent_id']))
                    thread = factory(guild=self, data=t, state=self._state)
                    if isinstance(parent_channel, ForumChannel):
                        post = ForumPost(state=self._state, guild=self, data=t)
                        self._add_channel(post)
                        parent_channel._add_post(post)
                    else:
                        self._add_channel(thread)
                        parent_channel._add_thread(thread)

    @property
    def application_commands(self) -> List[ApplicationCommand]:
        """List[:class:`~discord.ApplicationCommand`]: A list of application-commands from this application that are registered only in this guild.
        """
        return list(self._application_commands.values())

    def get_application_command(self, id: int) -> Optional[ApplicationCommand]:
        """Optional[:class:`~discord.ApplicationCommand`]: Returns an application-command from this application that are registered only in this guild with the given id"""
        return self._application_commands.get(id, None)

    @property
    def channels(self) -> List[Union[GuildChannel, ThreadChannel, ForumPost]]:
        """List[:class:`abc.GuildChannel`, :class:`ThreadChannel`, :class:`ForumPost`]: A list of channels that belongs to this guild."""
        return list(self._channels.values())

    @property
    def events(self) -> List[GuildScheduledEvent]:
        """List[:class:`~discord.GuildScheduledEvent`]: A list of scheduled events that belong to this guild."""
        return list(self._events.values())

    scheduled_events = events

    @property
    def cached_automod_rules(self) -> List[AutoModRule]:
        """
        List[:class:`AutoModRules`]: A list of auto moderation rules that are cached.

        .. admonition:: Reliable Fetching
            :class: helpful
            
            This property is only reliable if :meth:`~Guild.automod_rules` was used before.
            To ensure that the rules are up-to-date, use :meth:`~Guild.automod_rules` instead.
        """
        return list(self._automod_rules.values())

    def get_event(self, id: int) -> Optional[GuildScheduledEvent]:
        """
        Returns a scheduled event with the given ID.

        Parameters
        ----------
        id: :class:`int`
            The ID of the event to get.

        Returns
        -------
        Optional[:class:`~discord.GuildScheduledEvent`]
            The scheduled event or ``None`` if not found.
        """
        return self._events.get(id)

    get_scheduled_event = get_event

    @property
    def large(self) -> bool:
        """:class:`bool`: Indicates if the guild is a 'large' guild.

        A large guild is defined as having more than ``large_threshold`` count
        members, which for this library is set to the maximum of 250.
        """
        if self._large is None:
            try:
                return self._member_count >= 250
            except AttributeError:
                return len(self._members) >= 250
        return self._large

    @property
    def voice_channels(self) -> List[VoiceChannel]:
        """List[:class:`VoiceChannel`]: A list of voice channels that belongs to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, VoiceChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def stage_channels(self) -> List[StageChannel]:
        """List[:class:`StageChannel`]: A list of voice channels that belongs to this guild.

        .. versionadded:: 1.7

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, StageChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def me(self) -> Member:
        """:class:`Member`: Similar to :attr:`Client.user` except an instance of :class:`Member`.
        This is essentially used to get the member version of yourself.
        """
        self_id = self._state.user.id
        return self.get_member(self_id)

    @property
    def voice_client(self) -> Optional[VoiceProtocol]:
        """Optional[:class:`VoiceProtocol`]: Returns the :class:`VoiceProtocol` associated with this guild, if any."""
        return self._state._get_voice_client(self.id)

    @property
    def text_channels(self) -> List[TextChannel]:
        """List[:class:`TextChannel`]: A list of text channels that belongs to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, TextChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def thread_channels(self) -> List[ThreadChannel]:
        """List[:class:`ThreadChannel`]: A list of **cached** thread channels the guild has.

        This is sorted by the position of the threads :attr:`~discord.ThreadChannel.parent` and are in UI order from top to bottom.
        """
        r = []
        [r.extend(ch.threads) for ch in self._channels.values() if isinstance(ch, TextChannel)]
        r.sort(key=lambda t: (t.parent_channel.position, t.id))
        return r
    
    @property
    def forum_channels(self) -> List[ForumChannel]:
        """List[:class:`ForumChannel`]: A list of forum channels the guild has.

        This is sorted by the position of the forums :attr:`~discord.ForumChannel.parent` and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, ForumChannel)]
        r.sort(key=lambda f: (f.parent_channel.position, f.id))
        return r
    
    @property
    def forum_posts(self) -> List[ForumPost]:
        """List[:class:`ForumPost`]: A list of **cached** forum posts the guild has.

        This is sorted by the position of the forums :attr:`~discord.ForumPost.parent` and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, ForumPost)]
        r.sort(key=lambda f: (f.parent_channel.position, f.id))
        return r

    @property
    def categories(self) -> List[CategoryChannel]:
        """List[:class:`CategoryChannel`]: A list of categories that belongs to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, CategoryChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    def by_category(self) -> List[Tuple[Optional[CategoryChannel], List[GuildChannel]]]:
        """Returns every :class:`CategoryChannel` and their associated channels.

        These channels and categories are sorted in the official Discord UI order.

        If the channels do not have a category, then the first element of the tuple is
        ``None``.

        Returns
        --------
        List[Tuple[Optional[:class:`CategoryChannel`], List[:class:`abc.GuildChannel`]]]:
            The categories and their associated channels.
        """
        grouped = {}
        for channel in self._channels.values():
            if isinstance(channel, CategoryChannel):
                grouped.setdefault(channel.id, [])
                continue
            if isinstance(channel, ThreadChannel):
                continue
            try:
                grouped[channel.category_id].append(channel)
            except KeyError:
                grouped[channel.category_id] = [channel]

        def key(t):
            k, v = t
            return ((k.position, k.id) if k else (-1, -1), v)

        _get = self._channels.get
        as_list = [(_get(k), v) for k, v in grouped.items()]
        as_list.sort(key=key)
        for _, channels in as_list:
            channels.sort(key=lambda c: (c._sorting_bucket, c.position, c.id))
        return as_list

    def get_channel(self, channel_id: int) -> Optional[Union[CategoryChannel, TextChannel, StageChannel, VoiceChannel, ThreadChannel, ForumPost]]:
        """Returns a channel with the given ID.

        Parameters
        -----------
        channel_id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[Union[:class:`.abc.GuildChannel`, :class:`ThreadChannel`, :class:`ForumPost`]]
            The returned channel or ``None`` if not found.
        """
        return self._channels.get(channel_id)

    @property
    def system_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Returns the guild's channel used for system messages.

        If no channel is set, then this returns ``None``.
        """
        channel_id = self._system_channel_id
        return channel_id and self._channels.get(channel_id)

    @property
    def system_channel_flags(self) -> SystemChannelFlags:
        """:class:`SystemChannelFlags`: Returns the guild's system channel settings."""
        return SystemChannelFlags._from_value(self._system_channel_flags)

    async def welcome_screen(self) -> Optional[WelcomeScreen]:
        """Optional[:class:`WelcomeScreen`]: fetches the welcome screen from the guild if any."""
        data = await self._state.http.get_welcome_screen(guild_id=self.id)
        if data:
            self._welcome_screen = WelcomeScreen(state=self._state, guild=self, data=data)
            return self._welcome_screen

    @property
    def rules_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Return's the guild's channel used for the rules.
        The guild must be a Community guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 1.3
        """
        channel_id = self._rules_channel_id
        return channel_id and self._channels.get(channel_id)

    @property
    def public_updates_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Return's the guild's channel where admins and
        moderators of the guilds receive notices from Discord. The guild must be a
        Community guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 1.4
        """
        channel_id = self._public_updates_channel_id
        return channel_id and self._channels.get(channel_id)

    @property
    def emoji_limit(self) -> int:
        """:class:`int`: The maximum number of emoji slots this guild has."""
        more_emoji = 200 if 'MORE_EMOJI' in self.features else 50
        return max(more_emoji, self._PREMIUM_GUILD_LIMITS[self.premium_tier].emoji)

    @property
    def sticker_limit(self) -> int:
        """:class:`int`: The maximum number of sticker slots this guild has."""
        more_sticker = 60 if 'MORE_STICKER' in self.features else 5
        return max(more_sticker, self._PREMIUM_GUILD_LIMITS[self.premium_tier].sticker)

    @property
    def bitrate_limit(self) -> float:
        """:class:`float`: The maximum bitrate for voice channels this guild can have."""
        vip_guild = self._PREMIUM_GUILD_LIMITS[1].bitrate if 'VIP_REGIONS' in self.features else 96e3
        return max(vip_guild, self._PREMIUM_GUILD_LIMITS[self.premium_tier].bitrate)

    @property
    def filesize_limit(self) -> int:
        """:class:`int`: The maximum number of bytes files can have when uploaded to this guild."""
        return self._PREMIUM_GUILD_LIMITS[self.premium_tier].filesize

    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: A list of members that belong to this guild."""
        return list(self._members.values())

    def get_member(self, user_id: int) -> Optional[Member]:
        """Returns a member with the given ID.

        Parameters
        -----------
        user_id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`Member`]
            The member or ``None`` if not found.
        """
        return self._members.get(user_id)

    @property
    def premium_subscribers(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who have "boosted" this guild."""
        return [member for member in self.members if member.premium_since is not None]

    @property
    def roles(self) -> List[Role]:
        """List[:class:`Role`]: Returns a :class:`list` of the guild's roles in hierarchy order.

        The first element of this list will be the lowest role in the
        hierarchy.
        """
        return sorted(self._roles.values())

    def get_role(self, role_id) -> Optional[Role]:
        """Returns a role with the given ID.

        Parameters
        -----------
        role_id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`Role`]
            The role or ``None`` if not found.
        """
        return self._roles.get(role_id)

    @property
    def default_role(self) -> Role:
        """:class:`Role`: Gets the @everyone role that all members have by default."""
        return self.get_role(self.id)

    @property
    def premium_subscriber_role(self) -> Optional[Role]:
        """Optional[:class:`Role`]: Gets the premium subscriber role, AKA "boost" role, in this guild.

        .. versionadded:: 1.6
        """
        return next(
            (
                role
                for role in self._roles.values()
                if role.is_premium_subscriber()
            ),
            None,
        )

    @property
    def self_role(self) -> Optional[Role]:
        """Optional[:class:`Role`]: Gets the role associated with this client's user, if any.

        .. versionadded:: 1.6
        """
        self_id = self._state.self_id
        for role in self._roles.values():
            tags = role.tags
            if tags and tags.bot_id == self_id:
                return role
        return None

    @property
    def owner(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member that owns the guild."""
        return self.get_member(self.owner_id)

    @property
    def icon_url(self) -> Asset:
        """:class:`Asset`: Returns the guild's icon asset."""
        return self.icon_url_as()

    def is_icon_animated(self) -> bool:
        """:class:`bool`: Returns True if the guild has an animated icon."""
        return bool(self.icon and self.icon.startswith('a_'))

    def icon_url_as(
            self,
            *,
            format: Literal['webp', 'jpeg', 'jpg', 'png', 'gif'] = None,
            static_format: Literal['webp', 'jpeg', 'jpg', 'png'] = 'webp',
            size: int = 1024
    ) -> Asset:
        """Returns an :class:`Asset` for the guild's icon.

        The format must be one of 'webp', 'jpeg', 'jpg', 'png' or 'gif', and
        'gif' is only valid for animated avatars. The size must be a power of 2
        between 16 and 4096.

        Parameters
        -----------
        format: Optional[:class:`str`]
            The format to attempt to convert the icon to.
            If the format is ``None``, then it is automatically
            detected into either 'gif' or static_format depending on the
            icon being animated or not.
        static_format: Optional[:class:`str`]
            Format to attempt to convert only non-animated icons to.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_guild_icon(self._state, self, format=format, static_format=static_format, size=size)

    @property
    def banner_url(self) -> Asset:
        """:class:`Asset`: Returns the guild's banner asset."""
        return self.banner_url_as()

    def banner_url_as(
            self,
            *,
            format: Literal['webp', 'jpeg', 'jpg', 'png'] = 'webp',
            size: int = 2048
    ) -> Asset:
        """Returns an :class:`Asset` for the guild's banner.

        The format must be one of 'webp', 'jpeg', or 'png'. The
        size must be a power of 2 between 16 and 4096.

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the banner to.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_guild_image(self._state, self.id, self.banner, 'banners', format=format, size=size)

    @property
    def splash_url(self) -> Asset:
        """:class:`Asset`: Returns the guild's invite splash asset."""
        return self.splash_url_as()

    def splash_url_as(
            self,
            *,
            format: Literal['webp', 'jpeg', 'jpg', 'png'] = 'webp',
            size: int = 2048
    ) -> Asset:
        """Returns an :class:`Asset` for the guild's invite splash.

        The format must be one of 'webp', 'jpeg', 'jpg', or 'png'. The
        size must be a power of 2 between 16 and 4096.

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the splash to.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_guild_image(self._state, self.id, self.splash, 'splashes', format=format, size=size)

    @property
    def discovery_splash_url(self) -> Asset:
        """:class:`Asset`: Returns the guild's discovery splash asset.

        .. versionadded:: 1.3
        """
        return self.discovery_splash_url_as()

    def discovery_splash_url_as(
            self,
            *,
            format: Literal['webp', 'jpeg', 'jpg', 'png'] = 'webp',
            size: int = 2048
    ) -> Asset:
        """Returns an :class:`Asset` for the guild's discovery splash.

        The format must be one of 'webp', 'jpeg', 'jpg', or 'png'. The
        size must be a power of 2 between 16 and 4096.

        .. versionadded:: 1.3

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the splash to.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_guild_image(
            self._state,
            self.id,
            self.discovery_splash,
            'discovery-splashes',
            format=format,
            size=size
        )

    @property
    def member_count(self) -> int:
        """:class:`int`: Returns the true member count regardless of it being loaded fully or not.

        .. warning::

            Due to a Discord limitation, in order for this attribute to remain up-to-date and
            accurate, it requires :attr:`Intents.members` to be specified.

        """
        return self._member_count

    @property
    def chunked(self) -> bool:
        """:class:`bool`: Returns a boolean indicating if the guild is "chunked".

        A chunked guild means that :attr:`member_count` is equal to the
        number of members stored in the internal :attr:`members` cache.

        If this value returns ``False``, then you should request for
        offline members.
        """
        count = getattr(self, '_member_count', None)
        return False if count is None else count == len(self._members)

    @property
    def shard_id(self) -> Optional[int]:
        """Optional[:class:`int`]: Returns the shard ID for this guild if applicable."""
        count = self._state.shard_count
        return None if count is None else (self.id >> 22) % count

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the guild's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def get_member_named(self, name: str) -> Optional[Member]:
        """Returns the first member found that matches the name provided.

        The name can have an optional discriminator argument, e.g. "Jake#0001"
        or "Jake" will both do the lookup. However, the former will give a more
        precise result. Note that the discriminator must have all 4 digits
        for this to work.

        If a nickname is passed, then it is looked up via the nickname. Note
        however, that a nickname + discriminator combo will not lookup the nickname
        but rather the username + discriminator combo due to nickname + discriminator
        not being unique.

        If no member is found, ``None`` is returned.

        Parameters
        -----------
        name: :class:`str`
            The name of the member to lookup with an optional discriminator.

        Returns
        --------
        Optional[:class:`Member`]
            The member in this guild with the associated name. If not found
            then ``None`` is returned.
        """

        result = None
        members = self.members
        if len(name) > 5 and name[-5] == '#':
            # The 5 length is checking to see if #0000 is in the string,
            # as a#0000 has a length of 6, the minimum for a potential
            # discriminator lookup.
            potential_discriminator = name[-4:]

            # do the actual lookup and return if found
            # if it isn't found then we'll do a full name lookup below.
            result = utils.get(members, name=name[:-5], discriminator=potential_discriminator)
            if result is not None:
                return result

        def pred(m: Member):
            return m.nick == name or m.name == name

        return utils.find(pred, members)

    def _create_channel(
            self,
            name: str,
            overwrites: Dict[Union[Role, Member], PermissionOverwrite],
            channel_type: ChannelType,
            category: Optional[CategoryChannel] = None,
            reason: Optional[str] = None,
            **options: Any
    ):
        if overwrites is None:
            overwrites = {}
        elif not isinstance(overwrites, dict):
            raise InvalidArgument('overwrites parameter expects a dict.')

        perms = []
        for target, perm in overwrites.items():
            if not isinstance(target, (Role, Member)):
                raise InvalidArgument('Expected Member or Role received {0.__name__}'.format(type(target)))
            if not isinstance(perm, PermissionOverwrite):
                raise InvalidArgument('Expected PermissionOverwrite received {0.__name__}'.format(type(perm)))

            allow, deny = perm.pair()
            payload = {
                'allow': allow.value,
                'deny': deny.value,
                'id': target.id,
                'type': 'role' if isinstance(target, Role) else 'member',
            }

            perms.append(payload)

        try:
            options['rate_limit_per_user'] = options.pop('slowmode_delay')
        except KeyError:
            pass

        try:
            rtc_region = options.pop('rtc_region')
        except KeyError:
            pass
        else:
            options['rtc_region'] = None if rtc_region is None else str(rtc_region)

        if channel_type.text or channel_type.forum_channel:
            try:
                default_auto_archive_duration: AutoArchiveDuration = options.pop('default_auto_archive_duration')
            except KeyError:
                pass
            else:
                default_auto_archive_duration = try_enum(AutoArchiveDuration, default_auto_archive_duration)
                if not isinstance(default_auto_archive_duration, AutoArchiveDuration):
                    raise InvalidArgument(
                        f'{default_auto_archive_duration} is not a valid default_auto_archive_duration'
                    )
                else:
                    options['default_auto_archive_duration'] = default_auto_archive_duration.value

            try:
                options['default_thread_rate_limit_per_user']: int = options.pop('default_thread_slowmode_delay')
            except KeyError:
                pass

        parent_id = category.id if category else None
        return self._state.http.create_channel(
            self.id, channel_type.value, name=name, parent_id=parent_id, permission_overwrites=perms, reason=reason, **options
        )

    async def create_text_channel(
            self,
            name: str,
            *,
            overwrites: Optional[Dict[Union[Member, Role], PermissionOverwrite]] = None,
            category: Optional[CategoryChannel] = None,
            reason: Optional[str] = None,
            **options
            ):
        """|coro|

        Creates a :class:`TextChannel` for the guild.

        Note that you need the :attr:`~Permissions.manage_channels` permission
        to create the channel.

        The ``overwrites`` parameter can be used to create a 'secret'
        channel upon creation. This parameter expects a :class:`dict` of
        overwrites with the target (either a :class:`Member` or a :class:`Role`)
        as the key and a :class:`PermissionOverwrite` as the value.

        .. note::

            Creating a channel of a specified position will not update the position of
            other channels to follow suit. A follow-up call to :meth:`~TextChannel.edit`
            will be required to update the position of the channel in the channel list.

        Examples
        ----------

        Creating a basic channel:

        .. code-block:: python3

            channel = await guild.create_text_channel('cool-channel')

        Creating a "secret" channel:

        .. code-block:: python3

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }

            channel = await guild.create_text_channel('secret', overwrites=overwrites)

        Parameters
        -----------
        name: :class:`str`
            The channel's name.
        overwrites
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply upon creation of a channel.
            Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        topic: Optional[:class:`str`]
            The new channel's topic.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
            The maximum value possible is `21600`.
        default_thread_slowmode_delay: :class:`int`
            The initial ``slowmode_delay`` to set on newly created threads in the channel.
            This field is copied to the thread at creation time and does not live update.
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`TextChannel`
            The channel that was just created.
        """
        data = await self._create_channel(name, overwrites, ChannelType.text, category, reason=reason, **options)
        channel = TextChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_voice_channel(
            self,
            name: str,
            *,
            overwrites: Optional[Dict[Union[Member, Role], PermissionOverwrite]] = None,
            category: Optional[CategoryChannel] = None,
            reason: Optional[str] = None,
            **options
            ):
        """|coro|

        This is similar to :meth:`create_text_channel` except makes a :class:`VoiceChannel` instead, in addition
        to having the following new parameters.

        Parameters
        -----------
        bitrate: :class:`int`
            The channel's preferred audio bitrate in bits per second.
        user_limit: :class:`int`
            The channel's limit for number of members that can be in a voice channel.
        rtc_region: Optional[:class:`VoiceRegion`]
            The region for the voice channel's voice communication.
            A value of ``None`` indicates automatic voice region detection.

            .. versionadded:: 1.7

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`VoiceChannel`
            The channel that was just created.
        """
        data = await self._create_channel(name, overwrites, ChannelType.voice, category, reason=reason, **options)
        channel = VoiceChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_stage_channel(
            self,
            name: str,
            *,
            topic: Optional[str] = None,
            category: Optional[CategoryChannel] = None,
            overwrites: Optional[Dict[Union[Member, Role], PermissionOverwrite]] = None,
            reason: Optional[str] = None,
            position: Optional[int] = None
            ):
        """|coro|

        This is similar to :meth:`create_text_channel` except makes a :class:`StageChannel` instead, in addition
        to having the following new parameters.

        Parameters
        ----------
        topic: Optional[:class:`str`]
            The topic of the Stage instance (1-120 characters)

        .. note::

            The ``slowmode_delay`` and ``nsfw`` parameters are not supported in this function.

        .. versionadded:: 1.7

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`StageChannel`
            The channel that was just created.
        """
        data = await self._create_channel(
            name, overwrites, ChannelType.stage_voice, category, reason=reason, position=position, topic=topic
        )
        channel = StageChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_forum_channel(
            self,
            name: str,
            *,
            topic: Optional[str] = None,
            slowmode_delay: Optional[int] = None,
            default_post_slowmode_delay: Optional[int] = None,
            default_auto_archive_duration: Optional[AutoArchiveDuration] = None,
            overwrites: Optional[Dict[Union[Member, Role], PermissionOverwrite]] = None,
            nsfw: Optional[bool] = None,
            category: Optional[CategoryChannel] = None,
            position: Optional[int] = None,
            reason: Optional[str] = None
    ) -> ForumChannel:
        """|coro|

        Same as :meth:`create_text_channel` excepts that it creates a forum channel instead

        Parameters
        ----------
        name: :class:`str`
            The name of the channel
        overwrites
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply upon creation of a channel.
            Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        topic: Optional[:class:`str`]
            The new channel's topic.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
            The maximum value possible is `21600`.
        default_post_slowmode_delay: :class:`int`
            The initial ``slowmode_delay`` to set on newly created threads in the channel.
            This field is copied to the thread at creation time and does not live update.
        default_auto_archive_duration: :class:`AutoArchiveDuration`
            The default duration that the clients use (not the API) for newly created threads in the channel,
            in minutes, to automatically archive the thread after recent activity
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form,
            or the ``default_auto_archive_duration`` is not a valid member of :class:`AutoArchiveDuration`

        Returns
        -------
        :class:`ForumChannel`
            The channel that was just created
        """
        data = await self._create_channel(
            name,
            overwrites,
            ChannelType.forum_channel,
            category,
            topic=topic,
            slowmode_delay=slowmode_delay,
            default_thread_slowmode_delay=default_post_slowmode_delay,
            default_auto_archive_duration=default_auto_archive_duration,
            nsfw=nsfw,
            position=position,
            reason=reason
        )
        channel = ForumChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_category(
            self,
            name: str,
            *,
            overwrites: Optional[Dict[Union[Member, Role], PermissionOverwrite]] = None,
            reason: Optional[str] = None,
            position: Optional[int] = None
    ) -> CategoryChannel:
        """|coro|

        Same as :meth:`create_text_channel` except makes a :class:`CategoryChannel` instead.

        .. note::

            The ``category`` parameter is not supported in this function since categories
            cannot have categories.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`CategoryChannel`
            The channel that was just created.
        """
        data = await self._create_channel(name, overwrites, ChannelType.category, reason=reason, position=position)
        channel = CategoryChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    create_category_channel = create_category

    async def leave(self):
        """|coro|

        Leaves the guild.

        .. note::

            You cannot leave the guild that you own, you must delete it instead
            via :meth:`delete`.

        Raises
        --------
        HTTPException
            Leaving the guild failed.
        """
        await self._state.http.leave_guild(self.id)

    async def delete(self):
        """|coro|

        Deletes the guild. You must be the guild owner to delete the
        guild.

        Raises
        --------
        HTTPException
            Deleting the guild failed.
        Forbidden
            You do not have permissions to delete the guild.
        """

        await self._state.http.delete_guild(self.id)

    async def edit(
            self,
            name: str = MISSING,
            description: str = MISSING,
            features: GuildFeatures = MISSING,
            icon: Optional[bytes] = MISSING,
            banner: Optional[bytes] = MISSING,
            splash: Optional[bytes] = MISSING,
            discovery_splash: Optional[bytes] = MISSING,
            region: Optional[VoiceRegion] = MISSING,
            afk_channel: Optional[VoiceChannel] = MISSING,
            afk_timeout: Optional[int] = MISSING,
            system_channel: Optional[TextChannel] = MISSING,
            system_channel_flags: Optional[SystemChannelFlags] = MISSING,
            rules_channel: Optional[TextChannel] = MISSING,
            public_updates_channel: Optional[TextChannel] = MISSING,
            preferred_locale: Optional[Union[str, Locale]] = MISSING,
            verification_level: Optional[VerificationLevel] = MISSING,
            default_notifications: Optional[NotificationLevel] = MISSING,
            explicit_content_filter: Optional[ContentFilter] = MISSING,
            vanity_code: Optional[str] = MISSING,
            owner: Optional[Union[Member, User]] = MISSING,
            *,
            reason: Optional[str] = None,
    ) -> None:
        """|coro|

        Edits the guild.

        You must have the :attr:`~Permissions.manage_guild` permission
        to edit the guild.

        .. versionchanged:: 1.4
            The `rules_channel` and `public_updates_channel` keyword-only parameters were added.

        Parameters
        ----------
        name: :class:`str`
            The new name of the guild.
        description: :class:`str`
            The new description of the guild. This is only available to guilds that
            contain ``PUBLIC`` in :attr:`Guild.features`.
        features: :class:`GuildFeatures`
            Features to enable/disable will be merged in to the current features.
            See the `discord api documentation <https://discord.com/developers/docs/resources/guild#guild-object-mutable-guild-features>`_
            for a list of currently mutable features and the required permissions.
        icon: :class:`bytes`
            A :term:`py:bytes-like object` representing the icon. Only PNG/JPEG is supported.
            GIF is only available to guilds that contain ``ANIMATED_ICON`` in :attr:`Guild.features`.
            Could be ``None`` to denote removal of the icon.
        banner: :class:`bytes`
            A :term:`py:bytes-like object` representing the banner.
            Could be ``None`` to denote removal of the banner.
        splash: :class:`bytes`
            A :term:`py:bytes-like object` representing the invite splash.
            Only PNG/JPEG supported. Could be ``None`` to denote removing the
            splash. This is only available to guilds that contain ``INVITE_SPLASH``
            in :attr:`Guild.features`.
        discovery_splash: :class:`bytes`
            A :term:`py:bytes-like object` representing the discovery splash.
            Only PNG/JPEG supported. Could be ``None`` to denote removing the splash.
            This is only available to guilds that contain ``DISCOVERABLE`` in :attr:`Guild.features`.
        region: :class:`VoiceRegion`
            Deprecated: The new region for the guild's voice communication.
        afk_channel: Optional[:class:`VoiceChannel`]
            The new channel that is the AFK channel. Could be ``None`` for no AFK channel.
        afk_timeout: :class:`int`
            The number of seconds until someone is moved to the AFK channel.
        owner: :class:`Member`
            The new owner of the guild to transfer ownership to. Note that you must
            be owner of the guild to do this.
        verification_level: :class:`VerificationLevel`
            The new verification level for the guild.
        default_notifications: :class:`NotificationLevel`
            The new default notification level for the guild.
        explicit_content_filter: :class:`ContentFilter`
            The new explicit content filter for the guild.
        vanity_code: :class:`str`
            The new vanity code for the guild.
        system_channel: Optional[:class:`TextChannel`]
            The new channel that is used for the system channel. Could be ``None`` for no system channel.
        system_channel_flags: :class:`SystemChannelFlags`
            The new system channel settings to use with the new system channel.
        preferred_locale: :class:`str`
            The new preferred locale for the guild. Used as the primary language in the guild.
            If set, this must be an ISO 639 code, e.g. ``en-US`` or ``ja`` or ``zh-CN``.
        rules_channel: Optional[:class:`TextChannel`]
            The new channel that is used for rules. This is only available to
            guilds that contain ``PUBLIC`` in :attr:`Guild.features`. Could be ``None`` for no rules
            channel.
        public_updates_channel: Optional[:class:`TextChannel`]
            The new channel that is used for public updates from Discord. This is only available to
            guilds that contain ``PUBLIC`` in :attr:`Guild.features`. Could be ``None`` for no
            public updates channel.
        reason: Optional[:class:`str`]
            The reason for editing this guild. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to edit the guild.
        HTTPException
            Editing the guild failed.
        InvalidArgument
            The image format passed in to ``icon`` is invalid. It must be
            PNG or JPG. This is also raised if you are not the owner of the
            guild and request an ownership transfer.
        """

        http = self._state.http
        
        fields = {}
        
        if name is not MISSING:
            fields['name'] = name
        
        if description is not MISSING:
            fields['description'] = description
        
        if icon is not MISSING:
            fields['icon'] = utils._bytes_to_base64_data(icon)
        
        if banner is not MISSING:
            fields['banner'] = utils._bytes_to_base64_data(banner)
        
        if splash is not MISSING:
            fields['splash'] = utils._bytes_to_base64_data(splash)
        
        if features is not MISSING:
            current_features = GuildFeatures(self.features)
            fields['features'] = current_features.merge(features).parsed()
        
        if discovery_splash is not MISSING:
            fields['discovery_splash'] = utils._bytes_to_base64_data(discovery_splash)
        
        if region is not MISSING:
            import warnings
            warnings.warn('The region parameter is deprecated and will be removed in a future version.', DeprecationWarning)
            if not isinstance(region, VoiceRegion):
                raise InvalidArgument('region field must be of type VoiceRegion')
            fields['region'] = region.value
        
        if afk_channel is not MISSING:
            fields['afk_channel_id'] = afk_channel.id if afk_channel else None
        
        if afk_timeout is not MISSING:
            fields['afk_timeout'] = afk_timeout
        
        if owner is not MISSING:
            fields['owner_id'] = owner.id
        
        if verification_level is not MISSING:
            if not isinstance(verification_level, VerificationLevel):
                raise InvalidArgument('verification_level field must be of type VerificationLevel')
            fields['verification_level'] = verification_level.value
        
        if default_notifications is not MISSING:
            if not isinstance(default_notifications, NotificationLevel):
                raise InvalidArgument('default_notifications field must be of type NotificationLevel')
            fields['default_message_notifications'] = default_notifications.value
        
        if explicit_content_filter is not MISSING:
            if not isinstance(explicit_content_filter, ContentFilter):
                raise InvalidArgument('explicit_content_filter field must be of type ContentFilter')
            fields['explicit_content_filter'] = explicit_content_filter.value
        
        if vanity_code is not MISSING:
            fields['vanity_url_code'] = vanity_code
        
        if system_channel is not MISSING:
            fields['system_channel_id'] = system_channel.id if system_channel else None
        
        if system_channel_flags is not MISSING:
            if not isinstance(system_channel_flags, SystemChannelFlags):
                raise InvalidArgument('system_channel_flags field must be of type SystemChannelFlags')
            fields['system_channel_flags'] = system_channel_flags.value
        
        if preferred_locale is not MISSING:
            fields['preferred_locale'] = preferred_locale
        
        if rules_channel is not MISSING:
            fields['rules_channel_id'] = rules_channel.id if rules_channel else None
        
        if public_updates_channel is not MISSING:
            fields['public_updates_channel_id'] = public_updates_channel.id if public_updates_channel else None
        
        await http.edit_guild(self.id, reason=reason, **fields)

    async def fetch_channels(self) -> List[GuildChannel]:
        """|coro|

        Retrieves all :class:`abc.GuildChannel` that the guild has.

        .. note::

            This method is an API call. For general usage, consider :attr:`channels` instead.

        .. versionadded:: 1.2

        Raises
        -------
        InvalidData
            An unknown channel type was received from Discord.
        HTTPException
            Retrieving the channels failed.

        Returns
        -------
        List[:class:`abc.GuildChannel`]
            All channels in the guild.
        """
        data = await self._state.http.get_all_guild_channels(self.id)

        def convert(d):
            factory, ch_type = _channel_factory(d['type'])
            if factory is None:
                raise InvalidData('Unknown channel type {type} for channel ID {id}.'.format_map(d))

            channel = factory(guild=self, state=self._state, data=d)
            return channel

        return [convert(d) for d in data]

    def fetch_members(
            self,
            *,
            limit: int = 1000,
            after: Optional[Union[Snowflake, datetime]] = None
    ) -> MemberIterator:
        """Retrieves an :class:`.AsyncIterator` that enables receiving the guild's members. In order to use this,
        :meth:`Intents.members` must be enabled.

        .. note::

            This method is an API call. For general usage, consider :attr:`members` instead.

        .. versionadded:: 1.3

        All parameters are optional.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of members to retrieve. Defaults to 1000.
            Pass ``None`` to fetch all members. Note that this is potentially slow.
        after: Optional[Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve members after this date or object.
            If a date is provided it must be a timezone-naive datetime representing UTC time.

        Raises
        ------
        ClientException
            The members intent is not enabled.
        HTTPException
            Getting the members failed.

        Yields
        ------
        :class:`.Member`
            The member with the member data parsed.

        Examples
        --------

        Usage ::

            async for member in guild.fetch_members(limit=150):
                print(member.name)

        Flattening into a list ::

            members = await guild.fetch_members(limit=150).flatten()
            # members is now a list of Member...
        """

        if not self._state._intents.members:
            raise ClientException('Intents.members must be enabled to use this.')

        return MemberIterator(self, limit=limit, after=after)

    async def fetch_member(self, member_id: id) -> Member:
        """|coro|

        Retrieves a :class:`Member` from a guild ID, and a member ID.

        .. note::

            This method is an API call. If you have :attr:`Intents.members` and member cache enabled, consider :meth:`get_member` instead.

        Parameters
        -----------
        member_id: :class:`int`
            The member's ID to fetch from.

        Raises
        -------
        Forbidden
            You do not have access to the guild.
        HTTPException
            Fetching the member failed.

        Returns
        --------
        :class:`Member`
            The member from the member ID.
        """
        data = await self._state.http.get_member(self.id, member_id)
        return Member(data=data, state=self._state, guild=self)

    async def fetch_ban(self, user: Snowflake) -> BanEntry:
        """|coro|

        Retrieves the :class:`BanEntry` for a user.

        You must have the :attr:`~Permissions.ban_members` permission
        to get this information.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to get ban information from.

        Raises
        ------
        Forbidden
            You do not have proper permissions to get the information.
        NotFound
            This user is not banned.
        HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        :class:`BanEntry`
            The :class:`BanEntry` object for the specified user.
        """
        data = await self._state.http.get_ban(user.id, self.id)  # type: ignore
        return BanEntry(
            user=User(state=self._state, data=data['user']),
            reason=data['reason']
        )

    def bans(
            self,
            limit: Optional[int] = None,
            before: Optional[Union['Snowflake', datetime]] = None,
            after: Optional[Union['Snowflake', datetime]] = None
    ) -> BanIterator:
        """Retrieves an :class:`.AsyncIterator` that enables receiving the guild's bans.

        You must have the :attr:`~Permissions.ban_members` permission
        to get this information.

        .. note::

            This method is an API call. Use it careful.

        All parameters are optional.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of bans to retrieve. Defaults to all.
            Note that this is potentially slow.
        before: Optional[Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve members before this date or object.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after: Optional[Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve members after this date or object.
            If a date is provided it must be a timezone-naive datetime representing UTC time.

        Raises
        ------
        Forbidden
            You do not have proper permissions to get the information.
        HTTPException
            Getting the bans failed.

        Yields
        ------
        :class:`.BanEntry`
            The ban entry containing the user and an optional reason.

        Examples
        --------

        Usage ::

            async for ban_entry in guild.bans(limit=150):
                print(ban_entry.user)

        Flattening into a list ::

            ban_entries = await guild.bans(limit=150).flatten()
            # ban_entries is now a list of BanEntry...
        """
        return BanIterator(self, limit=limit, before=before, after=after)
    
    @overload
    async def prune_members(
            self,
            *,
            days: int,
            roles: Optional[List[Snowflake]],
            reason: Optional[str]
    ) -> int:
        ...
    
    @overload
    async def prune_members(
            self,
            *,
            days: int,
            compute_prune_count: Literal[True],
            roles: Optional[List[Snowflake]],
            reason: Optional[str]
    ) -> int:
        ...
    
    @overload
    async def prune_members(
        self,
        *,
        days: int,
        compute_prune_count: Literal[False],
        roles: Optional[List[Snowflake]],
        reason: Optional[str]
    ) -> None:
        ...
    
    async def prune_members(
            self,
            *,
            days: int,
            compute_prune_count: bool = True,
            roles: List[Snowflake] = None,
            reason: Optional[str] = None
    ) -> Optional[int]:
        r"""|coro|

        Prunes the guild from its inactive members.

        The inactive members are denoted if they have not logged on in
        ``days`` number of days, and they have no roles.

        You must have the :attr:`~Permissions.kick_members` permission
        to use this.

        To check how many members you would prune without actually pruning,
        see the :meth:`estimate_pruned_members` function.

        To prune members that have specific roles see the ``roles`` parameter.

        .. versionchanged:: 1.4
            The ``roles`` keyword-only parameter was added.

        Parameters
        -----------
        days: :class:`int`
            The number of days before counting as inactive.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.
        compute_prune_count: :class:`bool`
            Whether to compute the prune count. This defaults to ``True``
            which makes it prone to timeouts in very large guilds. In order
            to prevent timeouts, you must set this to ``False``. If this is
            set to ``False``\, then this function will always return ``None``.
        roles: Optional[List[:class:`abc.Snowflake`]]
            A list of :class:`abc.Snowflake` that represent roles to include in the pruning process. If a member
            has a role that is not specified, they'll be excluded.

        Raises
        -------
        Forbidden
            You do not have permissions to prune members.
        HTTPException
            An error occurred while pruning members.
        InvalidArgument
            An integer was not passed for ``days``.

        Returns
        ---------
        Optional[:class:`int`]
            The number of members pruned. If ``compute_prune_count`` is ``False``
            then this returns ``None``.
        """

        if not isinstance(days, int):
            raise InvalidArgument('Expected int for ``days``, received {0.__class__.__name__} instead.'.format(days))

        if roles:
            roles = [str(role.id) for role in roles]  # type: ignore

        data = await self._state.http.prune_members(
            self.id,
            days,
            compute_prune_count=compute_prune_count,
            roles=roles,
            reason=reason
        )
        return data['pruned']

    async def templates(self) -> List[Template]:
        """|coro|

        Gets the list of templates from this guild.

        Requires :attr:`~.Permissions.manage_guild` permissions.

        .. versionadded:: 1.7

        Raises
        -------
        Forbidden
            You don't have permissions to get the templates.

        Returns
        --------
        List[:class:`Template`]
            The templates for this guild.
        """
        from .template import Template
        data = await self._state.http.guild_templates(self.id)
        return [Template(data=d, state=self._state) for d in data]

    async def webhooks(self) -> List[Webhook]:
        """|coro|

        Gets the list of webhooks from this guild.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        Raises
        -------
        Forbidden
            You don't have permissions to get the webhooks.

        Returns
        --------
        List[:class:`Webhook`]
            The webhooks for this guild.
        """

        from .webhook import Webhook
        data = await self._state.http.guild_webhooks(self.id)
        return [Webhook.from_state(d, state=self._state) for d in data]

    async def estimate_pruned_members(self, *, days: int, roles: Optional[List[Snowflake]] = None) -> int:
        """|coro|

        Similar to :meth:`prune_members` except instead of actually
        pruning members, it returns how many members it would prune
        from the guild had it been called.

        Parameters
        -----------
        days: :class:`int`
            The number of days before counting as inactive.
        roles: Optional[List[:class:`abc.Snowflake`]]
            A list of :class:`abc.Snowflake` that represent roles to include in the estimate. If a member
            has a role that is not specified, they'll be excluded.

            .. versionadded:: 1.7

        Raises
        -------
        Forbidden
            You do not have permissions to prune members.
        HTTPException
            An error occurred while fetching the prune members estimate.
        InvalidArgument
            An integer was not passed for ``days``.

        Returns
        ---------
        :class:`int`
            The number of members estimated to be pruned.
        """

        if not isinstance(days, int):
            raise InvalidArgument('Expected int for ``days``, received {0.__class__.__name__} instead.'.format(days))

        if roles:
            roles = [str(role.id) for role in roles]  # type: ignore

        data = await self._state.http.estimate_pruned_members(self.id, days, roles)
        return data['pruned']

    async def invites(self) -> List[Invite]:
        """|coro|

        Returns a list of all active instant invites from the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to get
        this information.

        Raises
        -------
        Forbidden
            You do not have proper permissions to get the information.
        HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        List[:class:`Invite`]
            The list of invites that are currently active.
        """

        data = await self._state.http.invites_from(self.id)
        result = []
        for invite in data:
            channel = self.get_channel(int(invite['channel']['id']))
            invite['channel'] = channel
            invite['guild'] = self
            result.append(Invite(state=self._state, data=invite))

        return result

    async def create_template(self, *, name: str, description: Optional[str] = None) -> Template:
        """|coro|

        Creates a template for the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.7

        Parameters
        -----------
        name: :class:`str`
            The name of the template.
        description: Optional[:class:`str`]
            The description of the template.
        """
        from .template import Template

        payload = {
            'name': name
        }

        if description:
            payload['description'] = description

        data = await self._state.http.create_template(self.id, payload)

        return Template(state=self._state, data=data)

    async def create_integration(self, *, type: IntegrationType, id: int):
        """|coro|

        Attaches an integration to the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.4

        Parameters
        -----------
        type: :class:`str`
            The integration type (e.g. Twitch).
        id: :class:`int`
            The integration ID.

        Raises
        -------
        Forbidden
            You do not have permission to create the integration.
        HTTPException
            The account could not be found.
        """
        await self._state.http.create_integration(self.id, type, id)

    async def integrations(self) -> List[Integration]:
        """|coro|
        
        Returns a list of all integrations attached to the guild.
        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.
        .. versionadded:: 1.4
        Raises
        -------
        Forbidden
            You do not have permission to create the integration.
        HTTPException
            Fetching the integrations failed.
        Returns
        --------
        List[:class:`Integration`]
            The list of integrations that are attached to the guild.
        """
        data = await self._state.http.get_all_integrations(self.id)

        def convert(d):
            factory, itype = _integration_factory(d['type'])
            if factory is None:
                raise InvalidData('Unknown integration type {type!r} for integration ID {id}'.format_map(d))
            return factory(guild=self, data=d)

        return [convert(d) for d in data]

    async def fetch_emojis(self) -> List[Emoji]:
        r"""|coro|

        Retrieves all custom :class:`Emoji`\s from the guild.

        .. note::

            This method is an API call. For general usage, consider :attr:`emojis` instead.

        Raises
        ---------
        HTTPException
            An error occurred fetching the emojis.

        Returns
        --------
        List[:class:`Emoji`]
            The retrieved emojis.
        """
        data = await self._state.http.get_all_custom_emojis(self.id)
        return [Emoji(guild=self, state=self._state, data=d) for d in data]

    async def fetch_emoji(self, emoji_id: int) -> Emoji:
        """|coro|

        Retrieves a custom :class:`Emoji` from the guild.

        .. note::

            This method is an API call.
            For general usage, consider iterating over :attr:`emojis` instead.

        Parameters
        -------------
        emoji_id: :class:`int`
            The emoji's ID.

        Raises
        ---------
        NotFound
            The emoji requested could not be found.
        HTTPException
            An error occurred fetching the emoji.

        Returns
        --------
        :class:`Emoji`
            The retrieved emoji.
        """
        data = await self._state.http.get_custom_emoji(self.id, emoji_id)
        return Emoji(guild=self, state=self._state, data=data)

    async def create_custom_emoji(
            self,
            *,
            name: str,
            image: bytes,
            roles: Optional[List[Snowflake]] = None,
            reason: Optional[str] = None
    ) -> Emoji:
        r"""|coro|

        Creates a custom :class:`Emoji` for the guild.

        There is currently a limit of 50 static and animated emojis respectively per guild,
        unless the guild has the ``MORE_EMOJI`` feature which extends the limit to 200.

        You must have the :attr:`~Permissions.manage_emojis` permission to
        do this.

        Parameters
        -----------
        name: :class:`str`
            The emoji name. Must be at least 2 characters.
        image: :class:`bytes`
            The :term:`py:bytes-like object` representing the image data to use.
            Only JPG, PNG and GIF images are supported.
        roles: Optional[List[:class:`Role`]]
            A :class:`list` of :class:`Role`\s that can use this emoji. Leave empty to make it available to everyone.
        reason: Optional[:class:`str`]
            The reason for creating this emoji. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to create emojis.
        HTTPException
            An error occurred creating an emoji.

        Returns
        --------
        :class:`Emoji`
            The created emoji.
        """

        img = utils._bytes_to_base64_data(image)
        if roles:
            roles = [role.id for role in roles]  # type: ignore
        data = await self._state.http.create_custom_emoji(self.id, name, img, roles=roles, reason=reason)
        return self._state.store_emoji(self, data)

    async def fetch_roles(self) -> List[Role]:
        """|coro|

        Retrieves all :class:`Role` that the guild has.

        .. note::

            This method is an API call. For general usage, consider :attr:`roles` instead.

        .. versionadded:: 1.3

        Raises
        -------
        HTTPException
            Retrieving the roles failed.

        Returns
        -------
        List[:class:`Role`]
            All roles in the guild.
        """
        data = await self._state.http.get_roles(self.id)
        return [Role(guild=self, state=self._state, data=d) for d in data]

    @overload
    async def create_role(
            self,
            *,
            name: str = MISSING,
            permissions: Permissions = MISSING,
            color: Union[Colour, int] = MISSING,
            colour: Union[Colour, int] = MISSING,
            hoist: bool = False,
            mentionable: bool = False,
            reason: Optional[str] = None
    ) -> Role:
        ...
    
    @overload
    async def create_role(
            self,
            *,
            icon: bytes,
            name: str = MISSING,
            permissions: Permissions = MISSING,
            color: Union[Colour, int] = MISSING,
            colour: Union[Colour, int] = MISSING,
            hoist: bool = False,
            mentionable: bool = False,
            reason: Optional[str] = None
    ) -> Role:
        ...
    
    @overload
    async def create_role(
            self,
            *,
            unicode_emoji: str,
            name: str = MISSING,
            permissions: Permissions = MISSING,
            color: Union[Colour, int] = MISSING,
            colour: Union[Colour, int] = MISSING,
            hoist: bool = False,
            mentionable: bool = False,
            reason: Optional[str] = None
    ) -> Role:
        ...
    
    async def create_role(
            self,
            *,
            name: str = MISSING,
            permissions: Permissions = MISSING,
            color: Union[Colour, int] = MISSING,
            colour: Union[Colour, int] = MISSING,
            hoist: bool = False,
            mentionable: bool = False,
            icon: Optional[bytes] = None,
            unicode_emoji: Optional[str] = None,
            reason: Optional[str] = None
    ) -> Role:
        """|coro|

        Creates a :class:`Role` for the guild.

        All fields are optional.

        You must have the :attr:`~Permissions.manage_roles` permission to
        do this.

        .. versionchanged:: 1.6
            Can now pass ``int`` to ``colour`` keyword-only parameter.
        
        .. versionadded:: 2.0
            Added the ``icon`` and ``unicode_emoji`` keyword-only parameters.
        
        .. note::
            The ``icon`` and ``unicode_emoji`` can't be used together.
            Both of them can only be used when ``ROLE_ICONS`` is in the guild :meth:`~Guild.features`.
            
        Parameters
        -----------
        name: :class:`str`
            The role name. Defaults to 'new role'.
        permissions: :class:`Permissions`
            The permissions to have. Defaults to no permissions.
        color: Union[:class:`Colour`, :class:`int`]
            The colour for the role. Defaults to :meth:`Colour.default`.
        colour: Union[:class:`Colour`, :class:`int`]
            The colour for the role. Defaults to :meth:`Colour.default`.
            This is aliased to ``color`` as well.
        hoist: :class:`bool`
            Indicates if the role should be shown separately in the member list.
            Defaults to ``False``.
        mentionable: :class:`bool`
            Indicates if the role should be mentionable by others.
            Defaults to ``False``.
        icon: Optional[:class:`bytes`]
            The :term:`py:bytes-like object` representing the image data to use as the role :attr:`~Role.icon`.
        unicode_emoji: Optional[:class:`str`]
            The unicode emoji to use as the role :attr:`~Role.unicode_emoji`.
        reason: Optional[:class:`str`]
            The reason for creating this role. Shows up on the audit log.
        
        Raises
        -------
        Forbidden
            You do not have permissions to create the role.
        HTTPException
            Creating the role failed.
        InvalidArgument
            Both ``icon`` and ``unicode_emoji`` were passed.
        
        Returns
        --------
        :class:`Role`
            The newly created role.
        """

        fields = {}
        
        if name is not MISSING:
            fields['name'] = name
        
        if permissions is not MISSING:
            fields['permissions'] = permissions.value
        
        color = color if color is not MISSING else colour
        
        if color is not MISSING:
            if isinstance(color, Colour):
                color = color.value
            fields['color'] = color
        
        if hoist is not MISSING:
            fields['hoist'] = hoist
        
        if mentionable is not MISSING:
            fields['mentionable'] = mentionable
        
        if icon is not None:
            if unicode_emoji is not None:
                raise InvalidArgument('icon and unicode_emoji cannot be used together.')
            fields['icon'] = utils._bytes_to_base64_data(icon)
        
        elif unicode_emoji is not None:
            fields['unicode_emoji'] = str(unicode_emoji)

        data = await self._state.http.create_role(self.id, reason=reason, fields=fields)
        role = Role(guild=self, data=data, state=self._state)
        self._add_role(role)
        # TODO: add to cache
        return role

    async def edit_role_positions(self, positions: Dict[Role, int], *, reason: Optional[str] = None) -> List[Role]:
        """|coro|

        Bulk edits a list of :class:`Role` in the guild.

        You must have the :attr:`~Permissions.manage_roles` permission to
        do this.

        .. versionadded:: 1.4

        Example:

        .. code-block:: python3

            positions = {
                bots_role: 1, # penultimate role
                tester_role: 2,
                admin_role: 6
            }

            await guild.edit_role_positions(positions=positions)

        Parameters
        -----------
        positions
            A :class:`dict` of :class:`Role` to :class:`int` to change the positions
            of each given role.
        reason: Optional[:class:`str`]
            The reason for editing the role positions. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to move the roles.
        HTTPException
            Moving the roles failed.
        InvalidArgument
            An invalid keyword argument was given.

        Returns
        --------
        List[:class:`Role`]
            A list of all the roles in the guild.
        """
        if not isinstance(positions, dict):
            raise InvalidArgument('positions parameter expects a dict.')

        role_positions = []
        for role, position in positions.items():

            payload = {
                'id': role.id,
                'position': position
            }

            role_positions.append(payload)

        data = await self._state.http.move_role_position(self.id, role_positions, reason=reason)
        roles = []
        for d in data:
            role = Role(guild=self, data=d, state=self._state)
            roles.append(role)
            self._roles[role.id] = role

        return roles

    async def kick(self, user: Snowflake, *, reason: Optional[str] = None):
        """|coro|

        Kicks a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.kick_members` permission to
        do this.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to kick from their guild.
        reason: Optional[:class:`str`]
            The reason the user got kicked.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to kick.
        HTTPException
            Kicking failed.
        """
        await self._state.http.kick(user.id, self.id, reason=reason)  # type: ignore

    async def ban(
            self,
            user: Snowflake,
            *,
            reason: Optional[str] = None,
            delete_message_days: Optional[int] = None,
            delete_message_seconds: Optional[int] = 0
    ) -> None:
        """|coro|

        Bans a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.ban_members` permission to
        do this.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to ban from their guild.
        delete_message_days: :class:`int`
            The number of days worth of messages to delete from the user
            in the guild. The minimum is 0 and the maximum is 7.

            .. deprecated:: 2.0
        delete_message_seconds: :class:`int`
            The number of days worth of messages to delete from the user
            in the guild. The minimum is 0 and the maximum is 604800 (7 days).
        reason: Optional[:class:`str`]
            The reason the user got banned.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to ban.
        HTTPException
            Banning failed.
        """
        if delete_message_days is not None:
            import warnings
            warnings.warn(
                'delete_message_days is deprecated, use delete_message_seconds instead.',
                DeprecationWarning,
                stacklevel=2
            )
            delete_message_seconds = delete_message_days * 86400
        await self._state.http.ban(user.id, self.id, delete_message_seconds, reason=reason)  # type: ignore

    async def unban(self, user: Snowflake, *, reason: Optional[str] = None):
        """|coro|

        Unbans a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.ban_members` permission to
        do this.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to unban.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to unban.
        HTTPException
            Unbanning failed.
        """
        await self._state.http.unban(user.id, self.id, reason=reason)  # type: ignore

    async def vanity_invite(self) -> Invite:
        """|coro|

        Returns the guild's special vanity invite.

        The guild must have ``VANITY_URL`` in :attr:`~Guild.features`.

        You must have the :attr:`~Permissions.manage_guild` permission to use
        this as well.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to get this.
        HTTPException
            Retrieving the vanity invite failed.

        Returns
        --------
        :class:`Invite`
            The special vanity invite.
        """

        # we start with { code: abc }
        payload = await self._state.http.get_vanity_code(self.id)

        # get the vanity URL channel since default channels aren't
        # reliable or a thing anymore
        data = await self._state.http.get_invite(payload['code'])

        payload['guild'] = self
        payload['channel'] = self.get_channel(int(data['channel']['id']))
        payload['revoked'] = False
        payload['temporary'] = False
        payload['max_uses'] = 0
        payload['max_age'] = 0
        return Invite(state=self._state, data=payload)

    def audit_logs(
            self,
            *,
            limit: int = 100,
            before: Optional[Union[Snowflake, datetime]] = None,
            after: Optional[Union[Snowflake, datetime]] = None,
            oldest_first: Optional[bool] = None,
            user: Optional[Snowflake] = None,
            action: Optional[AuditLogAction] = None
    ):
        """Returns an :class:`AsyncIterator` that enables receiving the guild's audit logs.

        You must have the :attr:`~Permissions.view_audit_log` permission to use this.

        Examples
        ----------

        Getting the first 100 entries: ::

            async for entry in guild.audit_logs(limit=100):
                print('{0.user} did {0.action} to {0.target}'.format(entry))

        Getting entries for a specific action: ::

            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban):
                print('{0.user} banned {0.target}'.format(entry))

        Getting entries made by a specific user: ::

            entries = await guild.audit_logs(limit=None, user=guild.me).flatten()
            await channel.send('I made {} moderation actions.'.format(len(entries)))

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of entries to retrieve. If ``None`` retrieve all entries.
        before: Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]
            Retrieve entries before this date or entry.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after: Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]
            Retrieve entries after this date or entry.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        oldest_first: :class:`bool`
            If set to ``True``, return entries in oldest->newest order. Defaults to ``True`` if
            ``after`` is specified, otherwise ``False``.
        user: :class:`abc.Snowflake`
            The moderator to filter entries from.
        action: :class:`AuditLogAction`
            The action to filter with.

        Raises
        -------
        Forbidden
            You are not allowed to fetch audit logs
        HTTPException
            An error occurred while fetching the audit logs.

        Yields
        --------
        :class:`AuditLogEntry`
            The audit log entry.
        """
        if user:
            user = user.id  # type: ignore

        if action:
            action = action.value

        return AuditLogIterator(
            self,
            before=before,
            after=after,
            limit=limit,
            oldest_first=oldest_first,
            user_id=user,
            action_type=action
        )

    async def widget(self) -> Widget:
        """|coro|

        Returns the widget of the guild.

        .. note::

            The guild must have the widget enabled to get this information.

        Raises
        -------
        Forbidden
            The widget for this guild is disabled.
        HTTPException
            Retrieving the widget failed.

        Returns
        --------
        :class:`Widget`
            The guild's widget.
        """
        data = await self._state.http.get_widget(self.id)

        return Widget(state=self._state, data=data)

    async def chunk(self, *, cache: bool = True):
        """|coro|

        Requests all members that belong to this guild. In order to use this,
        :meth:`Intents.members` must be enabled.

        This is a websocket operation and can be slow.

        .. versionadded:: 1.5

        Parameters
        -----------
        cache: :class:`bool`
            Whether to cache the members as well.

        Raises
        -------
        ClientException
            The members intent is not enabled.
        """

        if not self._state._intents.members:
            raise ClientException('Intents.members must be enabled to use this.')

        if not self._state.is_guild_evicted(self):
            return await self._state.chunk_guild(self, cache=cache)

    async def query_members(
            self,
            query: Optional[str] = None,
            *,
            limit: int = 5,
            user_ids: Optional[List[int]] = None,
            presences: bool = False,
            cache: bool = True
    ) -> List[Member]:
        """|coro|

        Request members that belong to this guild whose username starts with
        the query given.

        This is a websocket operation and can be slow.

        .. versionadded:: 1.3

        Parameters
        -----------
        query: Optional[:class:`str`]
            The string that the username's start with.
        limit: :class:`int`
            The maximum number of members to send back. This must be
            a number between 5 and 100.
        presences: :class:`bool`
            Whether to request for presences to be provided. This defaults
            to ``False``.

            .. versionadded:: 1.6

        cache: :class:`bool`
            Whether to cache the members internally. This makes operations
            such as :meth:`get_member` work for those that matched.
        user_ids: Optional[List[:class:`int`]]
            List of user IDs to search for. If the user ID is not in the guild then it won't be returned.

            .. versionadded:: 1.4


        Raises
        -------
        asyncio.TimeoutError
            The query timed out waiting for the members.
        ValueError
            Invalid parameters were passed to the function
        ClientException
            The presences intent is not enabled.

        Returns
        --------
        List[:class:`Member`]
            The list of members that have matched the query.
        """

        if presences and not self._state._intents.presences:
            raise ClientException('Intents.presences must be enabled to use this.')

        if query is None:
            if query == '':
                raise ValueError('Cannot pass empty query string.')

            if user_ids is None:
                raise ValueError('Must pass either query or user_ids')

        if user_ids is not None and query is not None:
            raise ValueError('Cannot pass both query and user_ids')

        if user_ids is not None and not user_ids:
            raise ValueError('user_ids must contain at least 1 value')

        limit = min(100, limit or 5)
        return await self._state.query_members(
            self,
            query=query,
            limit=limit,
            user_ids=user_ids,
            presences=presences,
            cache=cache
        )

    async def change_voice_state(
            self,
            *,
            channel: Optional[Union[VoiceChannel, StageChannel]],
            self_mute: bool = False,
            self_deaf: bool = False
    ):
        """|coro|

        Changes client's voice state in the guild.

        .. versionadded:: 1.4

        Parameters
        -----------
        channel: Optional[:class:`VoiceChannel`]
            Channel the client wants to join. Use ``None`` to disconnect.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.
        """
        ws = self._state._get_websocket(self.id)
        channel_id = channel.id if channel else None
        await ws.voice_state(self.id, channel_id, self_mute, self_deaf)

    async def create_sticker(
            self,
            name: str,
            file: Union[UploadFile, PathLike[str], PathLike[bytes]],
            tags: Union[str, List[str]],
            description: Optional[str] = None,
            *,
            reason: Optional[str] = None
    ) -> GuildSticker:
        """|coro|

        Create a new sticker for the guild.

        Requires the ``MANAGE_EMOJIS_AND_STICKERS`` permission.


        Parameters
        ----------
        name: :class:`str`
            The name of the sticker (2-30 characters).
        tags: Union[:class:`str`, List[:class:`str`]]
            Autocomplete/suggestion tags for the sticker separated by ``,`` or in a list. (max 200 characters).
        description: Optional[:class:`str`]
            The description of the sticker (None or 2-100 characters).
        file: Union[:class:`UploadFile`, :class:`str`]
            The sticker file to upload or the path to it, must be a PNG, APNG, GIF or Lottie JSON file, max 500 KB
        reason: Optional[:class:`str`]
            The reason for creating the sticker., shows up in the audit-log.

        Raises
        ------
        discord.Forbidden:
            You don't have the permissions to upload stickers in this guild.
        discord.HTTPException:
            Creating the sticker failed.
        ValueError
            Any of name, description or tags is too short/long.

        Return
        ------
        :class:`GuildSticker`
            The new GuildSticker created on success.
        """
        if 2 > len(name) > 30:
            raise ValueError(f'The name must be between 2 and 30 characters in length; got {len(name)}.')
        if not isinstance(file, UploadFile):
            file = UploadFile(file)
        if description is not None and 2 > len(description) > 100:
            raise ValueError(f'The description must be between 2 and 100 characters in length; got {len(description)}.')
        if isinstance(tags, list):
            tags = ','.join(tags)
        if len(tags) > 200:
            raise ValueError(f'The tags could be max. 200 characters in length; {len(tags)}.')
        try:
            data = await self._state.http.create_guild_sticker(
                guild_id=self.id,
                name=name,
                description=description,
                tags=tags,
                file=file,
                reason=reason
            )
        finally:
            file.close()
        return self._state.store_sticker(data)

    async def fetch_events(
            self,
            with_user_count: bool = True
    ) -> Optional[List[GuildScheduledEvent]]:
        """|coro|

        Retrieves a :class:`list` of scheduled events the guild has.

        .. note::

            This method is an API call.
            For general usage, consider iterating over :attr:`events` instead.

        Parameters
        ----------
        with_user_count: :class:`bool`
            Whether to include the number of interested users the event has, default ``True``.

        Returns
        -------
        Optional[List[:class:`GuildScheduledEvent`]]
            A list of scheduled events the guild has.
        """
        data = self._state.http.get_guild_events(guild_id=self.id, with_user_count=with_user_count)
        [self._add_event(GuildScheduledEvent(state=self._state, guild=self, data=d)) for d in data]
        return self.events

    async def fetch_event(
            self,
            id: int,
            with_user_count: bool = True
    ) -> Optional[GuildScheduledEvent]:
        """|coro|

        Fetches the :class:`GuildScheduledEvent` with the given id.

        Parameters
        ----------
        id: :class:`int`
            The id of the event to fetch.
        with_user_count: :class:`bool`
            Whether to include the number of interested users the event has, default ``True``.

        Returns
        -------
        Optional[:class:`GuildScheduledEvent`]
            The event on success.
        """
        data = await self._state.http.get_guild_event(guild_id=self.id, event_id=id, with_user_count=with_user_count)
        if data:
            event = GuildScheduledEvent(state=self._state, guild=self, data=data)
            self._add_event(event)
            return event

    async def create_scheduled_event(
            self,
            name: str,
            entity_type: EventEntityType,
            start_time: datetime,
            end_time: Optional[datetime] = None,
            channel: Optional[Union[StageChannel, VoiceChannel]] = None,
            description: Optional[str] = None,
            location: Optional[str] = None,
            cover_image: Optional[bytes] = None,
            *,
            reason: Optional[str] = None
    ) -> GuildScheduledEvent:
        """|coro|

        Schedules a new Event in this guild. Requires ``MANAGE_EVENTS`` at least in the :attr:`channel`
        or in the entire guild if :attr:`~GuildScheduledEvent.type` is :attr:`~EventType.external`.

        Parameters
        ----------
        name: :class:`str`
            The name of the scheduled event. 1-100 characters long.
        entity_type: :class:`EventEntityType`
            The entity_type of the scheduled event.

            .. important::
                :attr:`end_time` and :attr:`location` must be provided if entity_type is :class:`~EventEntityType.external`, otherwise :attr:`channel`

        start_time: :class:`datetime.datetime`
            The time when the event will start. Must be a valid date in the future.
        end_time: Optional[:class:`datetime.datetime`]
            The time when the event will end. Must be a valid date in the future.

            .. important::
                If :attr:`entity_type` is :class:`~EventEntityType.external` this must be provided.
        channel: Optional[Union[:class:`StageChannel`, :class:`VoiceChannel`]]
            The channel in which the event takes place.
            Must be provided if :attr:`entity_type` is :class:`~EventEntityType.stage` or :class:`~EventEntityType.voice`.
        description: Optional[:class:`str`]
            The description of the scheduled event. 1-1000 characters long.
        location: Optional[:class:`str`]
            The location where the event will take place. 1-100 characters long.

            .. important::
                This must be provided if :attr:`~GuildScheduledEvent.entity_type` is :attr:`~EventEntityType.external`

        cover_image: Optional[:class:`bytes`]
            The cover image of the scheduled event.
        reason: Optional[:class:`str`]
            The reason for scheduling the event, shows up in the audit-log.

        Returns
        -------
        :class:`~discord.GuildScheduledEvent`
            The scheduled event on success.

        Raises
        ------
        TypeError:
            Any parameter is of wrong type.
        errors.InvalidArgument:
            entity_type is :attr:`~EventEntityType.stage` or :attr:`~EventEntityType.voice` but ``channel`` is not provided
            or :attr:`~EventEntityType.external` but no ``location`` and/or ``end_time`` provided.
        ValueError:
            The value of any parameter is invalid. (e.g. to long/short)
        errors.Forbidden:
            You don't have permissions to schedule the event.
        discord.HTTPException:
            Scheduling the event failed.
        """

        fields: Dict[str, Any] = {}

        if not isinstance(entity_type, EventEntityType):
            entity_type = try_enum(EventEntityType, entity_type)
        if not isinstance(entity_type, EventEntityType):
            raise ValueError('entity_type must be a valid EventEntityType.')

        if 1 > len(name) > 100:
            raise ValueError(f'The length of the name must be between 1 and 100 characters long; got {len(name)}.')
        fields['name'] = name

        if int(entity_type) == 3 and not location:
            raise InvalidArgument('location must be provided if type is EventEntityType.external')
        elif int(entity_type) != 3 and not channel:
            raise InvalidArgument('channel must be provided if type is EventEntityType.stage or EventEntityType.voice.')

        fields['entity_type'] = int(entity_type)

        if channel is not None and not entity_type.external:
            if not isinstance(channel, (VoiceChannel, StageChannel)):
                raise TypeError(
                    f'The channel must be a StageChannel or VoiceChannel object, not {channel.__class__.__name__}.'
                    )
            if int(entity_type) not in (1, 2):
                entity_type = {StageChannel: EventEntityType.stage, VoiceChannel: EventEntityType.voice}.get(type(channel))
                fields['entity_type'] = entity_type.value
            fields['channel_id'] = str(channel.id)
            fields['entity_metadata'] = None

        if description is not None:
            if 1 > len(description) > 1000:
                raise ValueError(
                    f'The length of the description must be between 1 and 1000 characters long; got {len(description)}.'
                )
            fields['description'] = description

        if location is not None:
            if 1 > len(location) > 100:
                raise ValueError(
                    f'The length of the location must be between 1 and 100 characters long; got {len(location)}.'
                )
            if not entity_type.external:
                entity_type = EventEntityType.external
                fields['entity_type'] = entity_type.value
            fields['channel_id'] = None
            fields['entity_metadata'] = {'location': location}

        if entity_type.external and not end_time:
            raise ValueError('end_time is required for external events.')

        if not isinstance(start_time, datetime):
            raise TypeError(f'The start_time must be a datetime.datetime object, not {start_time.__class__.__name__}.')
        elif start_time < datetime.utcnow():
            raise ValueError('The start_time could not be in the past.')

        fields['scheduled_start_time'] = start_time.isoformat()

        if end_time:
            if not isinstance(end_time, datetime):
                raise TypeError(f'The end_time must be a datetime.datetime object, not {end_time.__class__.__name__}.')
            elif end_time < datetime.utcnow():
                raise ValueError('The end_time could not be in the past.')

            fields['scheduled_end_time'] = end_time.isoformat()

        fields['privacy_level'] = 2

        if cover_image:
            if not isinstance(cover_image, bytes):
                raise ValueError(f'cover_image must be of type bytes, not {cover_image.__class__.__name__}')
            as_base64 = utils._bytes_to_base64_data(cover_image)
            fields['image'] = as_base64

        data = await self._state.http.create_guild_event(guild_id=self.id, fields=fields, reason=reason)
        event = GuildScheduledEvent(state=self._state, guild=self, data=data)
        self._add_event(event)
        return event

    async def _register_application_command(self, command):
        client = self._state._get_client()
        try:
            client._guild_specific_application_commands[self.id]
        except KeyError:
            client._guild_specific_application_commands[self.id] = {
                'chat_input': {},
                'message': {},
                'user': {}
            }
        client._guild_specific_application_commands[self.id][command.type.name][command.name] = command
        data = command.to_dict()
        command_data = await self._state.http.create_application_command(self._state._get_client().app.id, data=data,
                                                                         guild_id=self.id
                                                                         )
        command._fill_data(command_data)
        client._application_commands[command.id] = self._application_commands[command.id] = command
        return command

    async def add_slash_command(
            self,
            name: str,
            name_localizations: Optional[Localizations] = Localizations(),
            description: str = 'No description',
            description_localizations: Optional[Localizations] = Localizations(),
            default_required_permissions: Optional['Permissions'] = None,
            options: Optional[List[Union['SubCommandGroup', 'SubCommand', 'SlashCommandOption']]] = [],
            connector: Optional[Dict[str, str]] = {},
            func: Awaitable = default_callback,
            cog: Optional[Cog] = None
    ) -> SlashCommand:
        command = SlashCommand(
            name=name,
            name_localizations=name_localizations,
            description=description,
            description_localizations=description_localizations,
            default_member_permissions=default_required_permissions,
            options=options,
            connector=connector,
            func=func,
            guild_id=self.id,
            state=self._state,
            cog=cog
        )
        return await self._register_application_command(command)

    async def add_message_command(
            self,
            name: str,
            name_localizations: Optional[Localizations] = Localizations(),
            description: str = 'No description',
            description_localizations: Optional[Localizations] = Localizations(),
            default_required_permissions: Optional[Permissions] = None,
            func: Awaitable = default_callback,
            cog: Optional[Cog] = None
            ) -> MessageCommand:
        command = MessageCommand(
            name=name,
            name_localizations=name_localizations,
            description=description,
            description_localizations=description_localizations,
            default_member_permissions=default_required_permissions,
            func=func,
            guild_id=self.id,
            state=self._state,
            cog=cog
        )
        return await self._register_application_command(command)

    async def add_user_command(
            self,
            name: str,
            name_localizations: Optional[Localizations] = Localizations(),
            description: str = 'No description',
            description_localizations: Optional[Localizations] = Localizations(),
            default_required_permissions: Optional[Permissions] = None,
            func: Awaitable = default_callback,
            cog: Optional[Cog] = None
            ) -> UserCommand:
        command = UserCommand(
            name=name,
            name_localizations=name_localizations,
            description=description,
            description_localizations=description_localizations,
            default_member_permissions=default_required_permissions,
            func=func,
            guild_id=self.id,
            state=self._state,
            cog=cog
        )
        return await self._register_application_command(command)

    async def automod_rules(self) -> List[AutoModRule]:
        """|coro|

        Fetches the Auto Moderation rules for this guild

        .. warning::
            This is an API-call, use it carefully.

        Returns
        --------
        List[:class:`~discord.AutoModRule`]
            A list of AutoMod rules the guild has
        """
        data = await self._state.http.get_automod_rules(guild_id=self.id)
        for rule in data:
            self._add_automod_rule(AutoModRule(state=self._state, guild=self, **rule))
        return self.cached_automod_rules

    async def create_automod_rule(
            self,
            name: str,
            event_type: AutoModEventType,
            trigger_type: AutoModTriggerType,
            trigger_metadata: AutoModTriggerMetadata,
            actions: List[AutoModAction],
            enabled: bool = True,
            exempt_roles: List[Snowflake] = [],
            exempt_channels: List[Snowflake] = [],
            *,
            reason: Optional[str] = None
    ) -> AutoModRule:
        """|coro|

        Creates a new AutoMod rule for this guild

        Parameters
        -----------
        name: :class:`str`
            The name, the rule should have. Only valid if it's not a preset rule.
        event_type: :class:`~discord.AutoModEventType`
            Indicates in what event context a rule should be checked.
        trigger_type: :class:`~discord.AutoModTriggerType`
            Characterizes the type of content which can trigger the rule.
        trigger_metadata: :class:`~discord.AutoModTriggerMetadata`
            Additional data used to determine whether a rule should be triggered.
            Different fields are relevant based on the value of :attr:`~AutoModRule.trigger_type`.
        actions: List[:class:`~discord.AutoModAction`]
            The actions which will execute when the rule is triggered.
        enabled: :class:`bool`
            Whether the rule is enabled, default :obj:`True`.
        exempt_roles: List[:class:`.Snowflake`]
            Up to 20 :class:`~discord.Role`'s, that should not be affected by the rule.
        exempt_channels: List[:class:`.Snowflake`]
            Up to 50 :class:`~discord.TextChannel`/:class:`~discord.VoiceChannel`'s, that should not be affected by the rule.
        reason: Optional[:class:`str`]
            The reason for creating the rule. Shows up in the audit log.

        Raises
        ------
        :exc:`discord.Forbidden`
            The bot is missing permissions to create AutoMod rules
        :exc:`~discord.HTTPException`
            Creating the rule failed

        Returns
        --------
        :class:`~discord.AutoModRule`
            The AutoMod rule created
        """
        data = {
            'name': name,
            'event_type': int(event_type),
            'trigger_type': int(trigger_type),
            'trigger_metadata': trigger_metadata.to_dict(),
            'actions': [a.to_dict() for a in actions],
            'enabled': enabled,
            'exempt_roles': [str(r.id) for r in exempt_roles]  # type: ignore
        }
        exempt_channels = [str(c.id) for c in exempt_channels]  # type: ignore
        for action in actions:  # Add the channels where messages should be logged to, to the exempted channels
            if action.type.send_alert_message and str(action.channel_id) not in exempt_channels:
                exempt_channels.append(str(action.channel_id))
        data['exempt_channels'] = exempt_channels
        rule_data = await self._state.http.create_automod_rule(guild_id=self.id, data=data, reason=reason)
        rule = AutoModRule(state=self._state, guild=self, data=rule_data)
        self._add_automod_rule(rule)
        return rule
