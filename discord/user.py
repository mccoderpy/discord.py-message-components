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

from typing import (
    Any,
    Dict,
    List,
    Optional,
    TYPE_CHECKING
)

from typing_extensions import Literal

import discord.abc
from .flags import PublicUserFlags
from .utils import snowflake_time, _bytes_to_base64_data
from .enums import DefaultAvatar, try_enum
from .colour import Colour
from .asset import Asset

if TYPE_CHECKING:
    import datetime
    from .abc import GuildChannel
    from .channel import DMChannel
    from .guild import Guild
    from .message import Message
    from .permissions import Permissions
    from .state import ConnectionState


_BaseUser = discord.abc.User


class BaseUser(_BaseUser):
    __slots__ = (
        'name', 'id', 'discriminator', 'avatar', 'banner', 'banner_color',
        'hex_banner_color', 'bot', 'system', '_public_flags', '_state'
    )

    def __init__(self, *, state: ConnectionState, data: Dict[str, Any]):
        self._state: ConnectionState = state
        self._update(data)

    def __str__(self):
        return '{0.name}#{0.discriminator}'.format(self)

    def __eq__(self, other: object):
        return isinstance(other, _BaseUser) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.id >> 22

    def _update(self, data: Dict[str, Any]) -> None:
        self.name = data['username']
        self.id = int(data['id'])
        self.discriminator = data['discriminator']
        self.avatar = data['avatar']
        self.banner = data.get('banner', None)
        banner_color = data.get('accent_color', None)
        if banner_color:
            self.banner_color = Colour(banner_color)
        else:
            self.banner_color = None
        self.hex_banner_color: str = data.get('banner_color', None)
        self._public_flags = data.get('public_flags', 0)
        self.bot = data.get('bot', False)
        self.system = data.get('system', False)

    @classmethod
    def _copy(cls, user) -> User:
        self = cls.__new__(cls)  # bypass __init__

        self.name = user.name
        self.id = user.id
        self.discriminator = user.discriminator
        self.avatar = user.avatar
        self.banner = user.banner
        self.banner_color = user.banner_color
        self.bot = user.bot
        self._state = user._state
        self._public_flags = user._public_flags

        return self

    def _to_minimal_user_json(self) -> Dict[str, Any]:
        return {
            'username': self.name,
            'id': self.id,
            'avatar': self.avatar,
            'banner': self.banner,
            'accent_color': self.banner_color,
            'discriminator': self.discriminator,
            'bot': self.bot,
        }

    @property
    def public_flags(self) -> PublicUserFlags:
        """:class:`PublicUserFlags`: The publicly available flags the user has."""
        return PublicUserFlags._from_value(self._public_flags)

    @property
    def avatar_url(self) -> Asset:
        """:class:`Asset`: Returns an :class:`Asset` for the avatar the user has.

        If the user does not have a traditional avatar, an asset for
        the default avatar is returned instead.

        This is equivalent to calling :meth:`avatar_url_as` with
        the default parameters (i.e. webp/gif detection and a size of 1024).
        """
        return self.avatar_url_as(format=None, size=1024)

    def is_avatar_animated(self) -> bool:
        """:class:`bool`: Indicates if the user has an animated avatar."""
        return bool(self.avatar and self.avatar.startswith('a_'))

    def avatar_url_as(self, *, format: Optional[str] = None, static_format='webp', size=1024) -> Asset:
        """Returns an :class:`Asset` for the avatar the user has.

        If the user does not have a traditional avatar, an asset for
        the default avatar is returned instead.

        The format must be one of 'webp', 'jpeg', 'jpg', 'png' or 'gif', and
        'gif' is only valid for animated avatars. The size must be a power of 2
        between 16 and 4096.

        Parameters
        -----------
        format: Optional[:class:`str`]
            The format to attempt to convert the avatar to.
            If the format is ``None``, then it is automatically
            detected into either 'gif' or static_format depending on the
            avatar being animated or not.
        static_format: Optional[:class:`str`]
            Format to attempt to convert only non-animated avatars to.
            Defaults to 'webp'
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or ``static_format``, or
            invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_avatar(self._state, self, format=format, static_format=static_format, size=size)

    @property
    def default_avatar(self) -> DefaultAvatar:
        """:class:`DefaultAvatar`: Returns the default avatar for a given user. This is calculated by the user's discriminator."""
        return try_enum(DefaultAvatar, int(self.discriminator) % len(DefaultAvatar))

    @property
    def default_avatar_url(self) -> Asset:
        """:class:`Asset`: Returns a URL for a user's default avatar."""
        return Asset(self._state, '/embed/avatars/{}.png'.format(self.default_avatar.value))

    @property
    def banner_url(self) -> Optional[Asset]:
        """
        Optional[:class:`Asset`]: Returns an asset for the banner the user has, if any.
        This is equal to calling :meth:`banner_url_as` with the default arguments.

        Returns
        --------
        Optional[:class:`Asset`]
            The resulting CDN asset if any.
        """
        return self.banner_url_as()

    def is_banner_animated(self) -> bool:
        """:class:`bool`: Indicates if the user has an animated banner."""
        return bool(self.banner and self.banner.startswith('a_'))

    def banner_url_as(
            self,
            *,
            format: Optional[str] = None,
            static_format: Literal['png', 'jpeg', 'webp', 'gif'] = 'webp',
            size: int = 1024
    ) -> Optional[Asset]:
        """Returns an :class:`Asset` for the banner the user has. Could be ``None``.

        The format must be one of 'webp', 'jpeg', 'jpg', 'png' or 'gif', and
        'gif' is only valid for animated banners. The size must be a power of 2
        between 16 and 4096.

        Parameters
        -----------
        format: Optional[:class:`str`]
            The format to attempt to convert the banner to.
            If the format is ``None``, then it is automatically
            detected into either 'gif' or static_format depending on the
            banner being animated or not.
        static_format: Optional[:class:`str`]
            Format to attempt to convert only non-animated banner to.
            Defaults to 'webp'
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or ``static_format``, or
            invalid ``size``.

        Returns
        --------
        Optional[:class:`Asset`]
            The resulting CDN asset if any.
        """
        return Asset._from_banner(self._state, self, format=format, static_format=static_format, size=size)

    @property
    def colour(self) -> Colour:
        """:class:`Colour`: A property that returns a colour denoting the rendered colour
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :attr:`color`.
        """
        return Colour.default()

    @property
    def color(self) -> Colour:
        """:class:`Colour`: A property that returns a color denoting the rendered color
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :attr:`colour`.
        """
        return self.colour

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user."""
        return '<@{0.id}>'.format(self)

    def permissions_in(self, channel: GuildChannel) -> Permissions:
        """An alias for :meth:`abc.GuildChannel.permissions_for`.

        Basically equivalent to:

        .. code-block:: python3

            channel.permissions_for(self)

        Parameters
        -----------
        channel: :class:`abc.GuildChannel`
            The channel to check your permissions for.
        """
        return channel.permissions_for(self)

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the user's creation time in UTC.

        This is when the user's Discord account was created."""
        return snowflake_time(self.id)

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name.

        For regular users this is just their username, but
        if they have a guild specific nickname then that
        is returned instead.
        """
        return self.name

    def mentioned_in(self, message: Message):
        """Checks if the user is mentioned in the specified message.

        Parameters
        -----------
        message: :class:`Message`
            The message to check if you're mentioned in.

        Returns
        -------
        :class:`bool`
            Indicates if the user is mentioned in the message.
        """

        if message.mention_everyone:
            return True

        return any(user.id == self.id for user in message.mentions)


class ClientUser(BaseUser):
    """Represents your Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator.

    Attributes
    -----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator. This is given when the username has conflicts.
    avatar: Optional[:class:`str`]
        The avatar hash the user has. Could be ``None``.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).
    locale: Optional[:class:`str`]
        The IETF language tag used to identify the language the user is using.
    mfa_enabled: :class:`bool`
        Specifies if the user has MFA turned on and working.
    """
    __slots__ = BaseUser.__slots__ + \
                ('locale', '_flags', 'verified', 'mfa_enabled', '__weakref__')

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)

    def __repr__(self):
        return '<ClientUser id={0.id} name={0.name!r} discriminator={0.discriminator!r}' \
               ' bot={0.bot} mfa_enabled={0.mfa_enabled}>'.format(self)

    def _update(self, data: Dict[str, Any]) -> None:
        super()._update(data)
        self.locale = data.get('locale')
        self._flags = data.get('flags', 0)
        self.mfa_enabled = data.get('mfa_enabled', False)

    async def edit(self, **fields) -> None:
        """|coro|

        Edits the current profile of the client.

        .. note::

            To upload an avatar, a :term:`py:bytes-like object` must be passed in that
            represents the image being uploaded. If this is done through a file
            then the file must be opened via ``open('some_filename', 'rb')`` and
            the :term:`py:bytes-like object` is given through the use of ``fp.read()``.

            The only image formats supported for uploading is JPEG and PNG.

        Parameters
        -----------
        username: :class:`str`
            The new username you wish to change to.
        avatar: :class:`bytes`
            A :term:`py:bytes-like object` representing the image to upload.
            Could be ``None`` to denote no avatar.

        Raises
        ------
        HTTPException
            Editing your profile failed.
        InvalidArgument
            Wrong image format passed for ``avatar``.
        """

        try:
            avatar_bytes = fields['avatar']
        except KeyError:
            avatar = self.avatar
        else:
            if avatar_bytes is not None:
                avatar = _bytes_to_base64_data(avatar_bytes)
            else:
                avatar = None

        args = {
            'username': fields.get('username', self.name),
            'avatar': avatar
        }

        http = self._state.http

        data = await http.edit_profile(**args)
        self._update(data)


class User(BaseUser, discord.abc.Messageable):
    """Represents a Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator.

    Attributes
    -----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator. This is given when the username has conflicts.
    avatar: Optional[:class:`str`]
        The avatar hash the user has. Could be None.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).
    """

    __slots__ = BaseUser.__slots__ + ('__weakref__',)

    def __repr__(self):
        return '<User id={0.id} name={0.name!r} discriminator={0.discriminator!r} bot={0.bot}>'.format(self)

    async def _get_channel(self):
        ch = await self.create_dm()
        return ch

    @property
    def dm_channel(self) -> Optional[DMChannel]:
        """Optional[:class:`DMChannel`]: Returns the channel associated with this user if it exists.

        If this returns ``None``, you can create a DM channel by calling the
        :meth:`create_dm` coroutine function.
        """
        return self._state._get_private_channel_by_user(self.id)

    @property
    def mutual_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: The guilds that the user shares with the client.

        .. note::

            This will only return mutual guilds within the client's internal cache.

        .. versionadded:: 1.7
        """
        return [guild for guild in self._state._guilds.values() if guild.get_member(self.id)]

    async def create_dm(self) -> DMChannel:
        """|coro|

        Creates a :class:`DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.

        Returns
        -------
        :class:`.DMChannel`
            The channel that was created.
        """
        found = self.dm_channel
        if found is not None:
            return found

        state = self._state
        data = await state.http.start_private_message(self.id)
        return state.add_dm_channel(data)
