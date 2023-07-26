# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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
    List,
    Tuple,
    TYPE_CHECKING
)
from typing_extensions import Literal

from .asset import Asset
from .welcome_screen import WelcomeScreen
from .sticker import GuildSticker
from .utils import parse_time, snowflake_time, _get_as_snowflake
from .object import Object
from .mixins import Hashable
from .enums import ChannelType, VerificationLevel, try_enum

if TYPE_CHECKING:
    from datetime import datetime

    from .state import ConnectionState
    from .scheduled_event import GuildScheduledEvent


class PartialInviteChannel:
    """Represents a "partial" invite channel.

    This model will be given when the user is not part of the
    guild the :class:`Invite` resolves to.

    .. container:: operations

        .. describe:: x == y

            Checks if two partial channels are the same.

        .. describe:: x != y

            Checks if two partial channels are not the same.

        .. describe:: hash(x)

            Return the partial channel's hash.

        .. describe:: str(x)

            Returns the partial channel's name.

    Attributes
    -----------
    name: :class:`str`
        The partial channel's name.
    id: :class:`int`
        The partial channel's ID.
    type: :class:`ChannelType`
        The partial channel's type.
    """

    __slots__ = ('id', 'name', 'type')

    def __init__(self, **kwargs):
        self.id = kwargs.pop('id')
        self.name = kwargs.pop('name')
        self.type = kwargs.pop('type')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<PartialInviteChannel id={0.id} name={0.name} type={0.type!r}>'.format(self)

    @property
    def mention(self):
        """:class:`str`: The string that allows you to mention the channel."""
        return f'<#{self.id}>'

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return snowflake_time(self.id)

class PartialInviteGuild:
    """Represents a "partial" invite guild.

    This model will be given when the user is not part of the
    guild the :class:`Invite` resolves to.

    .. container:: operations

        .. describe:: x == y

            Checks if two partial guilds are the same.

        .. describe:: x != y

            Checks if two partial guilds are not the same.

        .. describe:: hash(x)

            Return the partial guild's hash.

        .. describe:: str(x)

            Returns the partial guild's name.

    Attributes
    -----------
    name: :class:`str`
        The partial guild's name.
    id: :class:`int`
        The partial guild's ID.
    verification_level: :class:`VerificationLevel`
        The partial guild's verification level.
    features: List[:class:`str`]
        A list of features the guild has. See :attr:`Guild.features` for more information.
    icon: Optional[:class:`str`]
        The partial guild's icon.
    banner: Optional[:class:`str`]
        The partial guild's banner.
    splash: Optional[:class:`str`]
        The partial guild's invite splash.
    description: Optional[:class:`str`]
        The partial guild's description.
    premium_subscription_count: :class:`int`
        The partial guild's "boost" count.
    """

    __slots__ = ('_state', 'features', 'icon', 'banner', 'id', 'name', 'splash',
                 'verification_level', 'description', 'premium_subscription_count',
                 'stickers')

    def __init__(self, state: ConnectionState, data, id):
        self._state: ConnectionState = state
        self.id: int = id
        self.name: str = data['name']
        self.features: List[str] = data.get('features', [])
        self.icon: Optional[str] = data.get('icon')
        self.banner: Optional[str] = data.get('banner')
        self.splash: Optional[str] = data.get('splash')
        self.verification_level: VerificationLevel = try_enum(VerificationLevel, data.get('verification_level'))
        self.description: Optional[str] = data.get('description')
        self.premium_subscription_count: int = data.get('premium_subscription_count', 0)
        self.stickers: Tuple[GuildSticker] = tuple(GuildSticker(state=state, data=d) for d in data.get('stickers', []))

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return '<{0.__class__.__name__} id={0.id} name={0.name!r} features={0.features} ' \
               'description={0.description!r}>'.format(self)

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the guild's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def icon_url(self) -> Asset:
        """:class:`Asset`: Returns the guild's icon asset."""
        return self.icon_url_as()

    def is_icon_animated(self) -> bool:
        """:class:`bool`: Returns ``True`` if the guild has an animated icon.

        .. versionadded:: 1.4
        """
        return bool(self.icon and self.icon.startswith('a_'))

    def icon_url_as(
            self,
            *,
            format: Literal['webp', 'jpeg', 'jpg', 'png', 'gif'] = None,
            static_format: Literal['webp', 'jpeg', 'jpg', 'png'] = 'webp',
            size: int =1024
    ) -> Asset:
        """The same operation as :meth:`Guild.icon_url_as`.

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
        """The same operation as :meth:`Guild.banner_url_as`.

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
        """The same operation as :meth:`Guild.splash_url_as`.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_guild_image(self._state, self.id, self.splash, 'splashes', format=format, size=size)


class Invite(Hashable):
    r"""Represents a Discord :class:`Guild` or :class:`abc.GuildChannel` invite.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two invites are equal.

        .. describe:: x != y

            Checks if two invites are not equal.

        .. describe:: hash(x)

            Returns the invite hash.

        .. describe:: str(x)

            Returns the invite URL.

    The following table illustrates what methods will obtain the attributes:

    +------------------------------------+----------------------------------------------------------+
    |             Attribute              |                          Method                          |
    +====================================+==========================================================+
    | :attr:`max_age`                    | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites` |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`max_uses`                   | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites` |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`created_at`                 | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites` |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`temporary`                  | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites` |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`uses`                       | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites` |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`approximate_member_count`   | :meth:`Client.fetch_invite`                              |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`approximate_presence_count` | :meth:`Client.fetch_invite`                              |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`scheduled_event`            | :meth:`Client.fetch_invite`                              |
    +------------------------------------+----------------------------------------------------------+

    If it's not in the table above then it is available by all methods.

    Attributes
    -----------
    max_age: :class:`int`
        How long the before the invite expires in seconds.
        A value of ``0`` indicates that it doesn't expire.
    code: :class:`str`
        The URL fragment used for the invite.
    guild: Optional[Union[:class:`Guild`, :class:`Object`, :class:`PartialInviteGuild`]]
        The guild the invite is for. Can be ``None`` if it's from a group direct message.
    revoked: :class:`bool`
        Indicates if the invite has been revoked.
    created_at: :class:`datetime.datetime`
        A datetime object denoting the time the invite was created.
    temporary: :class:`bool`
        Indicates that the invite grants temporary membership.
        If ``True``, members who joined via this invite will be kicked upon disconnect.
    uses: :class:`int`
        How many times the invite has been used.
    max_uses: :class:`int`
        How many times the invite can be used.
        A value of ``0`` indicates that it has unlimited uses.
    inviter: :class:`User`
        The user who created the invite.
    approximate_member_count: Optional[:class:`int`]
        The approximate number of members in the guild.
    approximate_presence_count: Optional[:class:`int`]
        The approximate number of members currently active in the guild.
        This includes idle, dnd, online, and invisible members. Offline members are excluded.
    scheduled_event: Optional[:class:`GuildScheduledEvent`]
        The scheduled event attached to this invite link, if any.
    channel: Union[:class:`abc.GuildChannel`, :class:`Object`, :class:`PartialInviteChannel`]
        The channel the invite is for.
    """

    __slots__ = ('max_age', 'code', 'guild', 'revoked', 'created_at', 'uses',
                 'temporary', 'max_uses', 'inviter', 'channel', '_state',
                 'approximate_member_count', 'approximate_presence_count',
                 'scheduled_event')

    BASE = 'https://discord.gg'

    def __init__(self, *, state: ConnectionState, data) -> None:
        self._state = state
        self.max_age = data.get('max_age')
        self.code = data.get('code')
        self.guild = data.get('guild')
        self.revoked: Optional[bool] = data.get('revoked')
        self.created_at: datetime = parse_time(data.get('created_at'))
        self.temporary: Optional[bool] = data.get('temporary')
        self.uses: Optional[int] = data.get('uses')
        self.max_uses: Optional[int] = data.get('max_uses')
        self.approximate_presence_count: Optional[int] = data.get('approximate_presence_count')
        self.approximate_member_count: Optional[int] = data.get('approximate_member_count')

        inviter_data = data.get('inviter')
        self.inviter = None if inviter_data is None else self._state.store_user(inviter_data)
        self.channel = data.get('channel')
        self.scheduled_event: Optional[GuildScheduledEvent]
        guild_scheduled_event = data.get('guild_scheduled_event', None)
        if guild_scheduled_event is not None:
            self.scheduled_event = state.store_event(guild=self.guild, data=guild_scheduled_event)
        else:
            self.scheduled_event = None

    @classmethod
    def from_incomplete(cls, *, state: ConnectionState, data) -> Invite:
        try:
            guild_id = int(data['guild']['id'])
        except KeyError:
            # If we're here, then this is a group DM
            guild = None
        else:
            guild = state._get_guild(guild_id)
            if guild is None:
                # If it's not cached, then it has to be a partial guild
                guild_data = data['guild']
                guild = PartialInviteGuild(state, guild_data, guild_id)

        # As far as I know, invites always need a channel
        # So this should never raise.
        channel_data = data['channel']
        channel_id = int(channel_data['id'])
        channel_type = try_enum(ChannelType, channel_data['type'])
        channel = PartialInviteChannel(id=channel_id, name=channel_data['name'], type=channel_type)
        if guild is not None and not isinstance(guild, PartialInviteGuild):
            # Upgrade the partial data if applicable
            channel = guild.get_channel(channel_id) or channel

        data['guild'] = guild
        data['channel'] = channel
        return cls(state=state, data=data)

    @classmethod
    def from_gateway(cls, *, state: ConnectionState, data) -> Invite:
        guild_id = _get_as_snowflake(data, 'guild_id')
        guild = state._get_guild(guild_id)
        channel_id = _get_as_snowflake(data, 'channel_id')
        if guild is not None:
            channel = guild.get_channel(channel_id) or Object(id=channel_id)
        else:
            guild = Object(id=guild_id)
            channel = Object(id=channel_id)

        data['guild'] = guild
        data['channel'] = channel
        return cls(state=state, data=data)

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return f'<Invite code={self.code!r} guild={self.guild!r} ' \
               f'online={self.approximate_presence_count} ' \
               f'members={self.approximate_member_count} ' \
               f'scheduled_event={self.scheduled_event}>'

    def __hash__(self) -> int:
        return hash(self.code)

    @property
    def id(self) -> str:
        """:class:`str`: Returns the proper code portion of the invite."""
        return self.code

    @property
    def url(self):
        """:class:`str`: A property that retrieves the invite URL."""
        return f"{self.BASE}/{self.code}{f'?event={self.scheduled_event.id}' if self.scheduled_event else ''}"

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Revokes the instant invite.

        You must have the :attr:`~Permissions.manage_channels` permission to do this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this invite. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to revoke invites.
        NotFound
            The invite is invalid or expired.
        HTTPException
            Revoking the invite failed.
        """

        await self._state.http.delete_invite(self.code, reason=reason)

    def set_scheduled_event(self, event: GuildScheduledEvent) -> None:
        """Links the given scheduled event to this invite.

        .. note::

            Scheduled events aren't actually associated with invites on the API.
            Any guild channel invite can have an event attached to it. Using
            :meth:`abc.GuildChannel.create_invite`, :meth:`Client.fetch_invite`,
            or this method, you can link scheduled events.

        .. versionadded:: 2.0

        Parameters
        ----------
        event: :class:`ScheduledEvent`
            The scheduled event object to link.
        """
        self.scheduled_event = event
