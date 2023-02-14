# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2023-present mccoderpy

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
    Iterable,
    Optional,
    Set,
    Union,
    List,
    TYPE_CHECKING,
    TypeVar
)
from typing_extensions import (
    Self,
    Literal
)

from ..abc import User as _BaseUser
from ..mixins import Hashable
from ..asset import Asset
from ..colour import Colour
from ..enums import Locale, DefaultAvatar, PremiumType, try_enum
from ..flags import PublicUserFlags, GuildMemberFlags
from ..utils import (
    utcnow,
    snowflake_time,
    SnowflakeList,
    MISSING
)
from ..user import BaseUser
from ..permissions import Permissions


from .enums import OAuth2Scope
from .errors import (
    AccessTokenNotRefreshable
)

from datetime import (
    datetime,
    timedelta,
    timezone
)

if TYPE_CHECKING:
    from .client import OAuth2Client
    from ..types.user import UserPayload, GuildMember as GuildMemberPayload
    from ..types.snowflake import SnowflakeID
    from ..types.guild import PartialGuild as PartialGuildPayload
    from ..types.oauth2.models import *
    from ..types.oauth2.http import AccessTokenResponse
    
T = TypeVar('T')

__all__ = (
    'AccessToken',
    'User',
    'PartialGuild',
    'GuildMember',
)


def convert_to_datetime(value: DatetimeLike, /, from_delta: bool = False) -> datetime:
    """
    Converts the given value to an utc-aware :class:`~datetime.datetime` object:
    
    - If the value already is a :class:`~datetime.datetime` object it is returned instant
    
    - If the value is a :class:`int` / :class:`float` it is usually interpreted as an utc-aware POSIX timestamp -
     if :attr:`from_delta` is :obj:`True` it will return :func:`~discord.utils.utcnow()` + :func:`~datetime.timedelta(seconds=value)`
    
    - If is a :class:`str` it will be interpreted as a ISO 8601 compatible timestamp
    """
    if isinstance(value, datetime):
        return value
    elif isinstance(value, (float, int)):
        if from_delta:
            return utcnow() + timedelta(seconds=value)
        else:
            return datetime.fromtimestamp(value, timezone.utc)
    elif isinstance(value, str):
        return datetime.fromisoformat(value)
    

class AccessToken:
    """
    A representation of a
    `access token response <https://discord.com/developers/docs/topics/oauth2#authorization-code-grant-access-token-response>`_
    from discord.
    
    This can be also used to store additional data that can be accessed through getitem.
    """
    def __init__(
            self,
            access_token: str,
            expires_at: DatetimeLike,
            refresh_token: Optional[str] = None,
            scopes: Iterable[str] = None,
            **additional_data: Any
    ):
        """
        A representation of a
        `access token response <https://discord.com/developers/docs/topics/oauth2#authorization-code-grant-access-token-response>`_
        from discord.
        
        This can be also used to store additional data that can be accessed through get item.
        
        Parameters
        -----------
        access_token: :class:`str`
            The actual access token - this will also be returned when calling ``str(some_access_token)``
        expires_at: Union[:class:`int`, :class:`str`, :class:`~datetime.datetime`]
            When the access token will expire and needs to be refreshed.
            In order to make it compatible with most of the database drivers it allows the following types
                - integers/floats (POSIX timestamp)
                - strings (timestamps in any ISO 8601 format)
                - :class:`~datetime.datetime` objects for the drivers that already convert it to a datetime object
        refresh_token: Optional[:class:`str`]
            The token that is required to request a new access token when the previous one expires.
            This might be :obj:`None` depending on the grant type used
        scopes: Iterable[:class:`str`]
            A list of scopes the access token is authorized to
        **additional_data
            Additional data that should be stored as key=value pairs
        """
        self._access_token: str = access_token
        self._expires_at: datetime = convert_to_datetime(expires_at)
        self._refresh_token: Optional[str] = refresh_token
        self._scopes: Set[OAuth2Scope] = {OAuth2Scope(scope) for scope in scopes}
        self.additional_data: Dict[str, Any] = additional_data
    
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} expires_at={self.expires_at.isoformat()} scopes={", ".join(str(s) for s in self.scopes)}>'
    
    def __getitem__(self, item: str) -> Any:
        return self.additional_data.get(item)
    
    def __setitem__(self, key: str, value: Any):
        self.additional_data[key] = value
    
    @property
    def client(self) -> OAuth2Client:
        """
        The :class:`~discord.oauth2.OAuth2Client` that manages this access token when set, else :obj:`None`
        """
        return getattr(self, '_client', None)
    
    @client.setter
    def client(self, value: OAuth2Client):
        from .client import OAuth2Client  # avoid circular import
        if not isinstance(value, OAuth2Client):
            raise ValueError('Attribute client must be an instance of discord.oauth2.OAuth2Client')
        self._client = value
    
    @property
    def access_token(self) -> str:
        """
        The actual bearer access token.
        
        .. note::
            Note that this might be expired, and you need to refresh the token first.
            Use :meth:`is_expired` to check if it is expired.
        """
        return self._access_token
    
    @property
    def expires_at(self) -> datetime:
        """:class:`~datetime.datetime`: Wen the access token will expire"""
        return self._expires_at
    
    @property
    def refresh_token(self) -> Optional[str]:
        """:class:`str`: The refresh token that is required to refresh the access token when it is expired"""
        return self._refresh_token
    
    @property
    def scopes(self) -> Set[OAuth2Scope]:
        """:class:`list`[:class:`~discord.oauth2.OAuth2Scope`]: A list of scopes the access token is authorized to"""
        return self._scopes
    
    def is_expired(self) -> bool:
        """:class:`bool`: Whether the access token is expired. This just checks if the :attr:`.expires_at` is in the past"""
        return utcnow() > self.expires_at
    
    @classmethod
    def with_client(cls, client: OAuth2Client, /, **data) -> AccessToken:
        self = cls(**data)
        self._client = client
        return self
    
    @classmethod
    def from_raw_data(cls, client: OAuth2Client, data: AccessTokenData) -> AccessToken:
        expires_at = convert_to_datetime(data.pop('expires_in'), from_delta=True)
        scopes = data.pop('scope', '').split(' ')
        return cls.with_client(client, expires_at=expires_at, scopes=scopes, **data)
    
    def _update(self, data: AccessTokenResponse) -> Self:
        self._access_token = data['access_token']
        self._expires_at = convert_to_datetime(data['expires_in'], from_delta=True)
        self._refresh_token = data['refresh_token']
        return self
    
    def to_dict(self) -> AccessTokenData:
        base = {
            'access_token': self.access_token,
            'expires_at': self.expires_at.isoformat(),
            'scopes': [s.value for s in self.scopes],
            'refresh_token': self.refresh_token
        }
        refresh_token = self.refresh_token
        if refresh_token:
            base['refresh_token'] = refresh_token
        return base
        
    async def refresh(self, *, force: bool = False) -> Self:
        """|coro|
        
        Refreshes the access token when possible and returns the new one.
        If the token is still valid it will instantly return it unless ``force`` is set.
        This also updates the :attr:`expires_at` and :attr:`refresh_token`.
        
        .. note::
            This is only available when :attr:`.client` and :attr:`refresh_token` is set
        
        Parameters
        ----------
        force: :class:`bool`
            Whether to force-refresh the access token, even when :meth:`.is_expired` returns :obj:`False`
        
        Raises
        ------
        TokenNotRefreshable:
            The access token is not refreshable
        AttributeError:
            The client attribute is not set
        
        Returns
        -------
        :class:`str`:
            The new access token
        """
        if not self.is_expired() and not force:
            return self.access_token
        
        if not self.refresh_token:
            raise AccessTokenNotRefreshable()
        
        client = self.client
        if not client:
            raise AttributeError('client attribute is not set so you can\'t call this from the access token directly')
        await self._client.refresh_access_token(self)
        return self
    
    async def revoke(self) -> None:
        """|coro|
        
        Revokes the access token.
        
        .. note::
            This is only available when :attr:`.client` is set
        
        Raises
        ------
        AttributeError:
            The client attribute is not set
        """
        
        client = self.client
        if not client:
            raise AttributeError('client attribute is not set so you can\'t call this from the access token directly')
        
        await self._client.revoke_access_token(self)
        
    async def fetch_info(self):
        """|coro|
        
        Fetches the authorization information for the access token.
        
        .. note::
            This is only available when :attr:`.client` is set
        
        Raises
        ------
        AttributeError:
            The client attribute is not set
        
        Returns
        -------
        :class:`~discord.oauth2.OAuth2AuthInfo`:
            The authorization information
        """
        client = self.client
        if not client:
            raise AttributeError('client attribute is not set so you can\'t call this from the access token directly')
        
        data = await self._client.fetch_access_token_info(self)
        return data
    
    async def fetch_user(self) -> User:
        """|coro|
        
        Fetches the user associated with the access token.
        
        .. note::
            This is only available when :attr:`.client` is set
        
        Raises
        ------
        AttributeError:
            The client attribute is not set
        
        Returns
        -------
        :class:`~discord.User`:
            The user associated with the access token
        """
        client = self.client
        if not client:
            raise AttributeError('client attribute is not set so you can\'t call this from the access token directly')
        
        return await self._client.fetch_user(self)


class User(Hashable):
    """Represents a Discord user retrieved via an access_token.
    
    .. container:: operations
    
        .. describe:: x == y
        
            Checks if two users are equal.
        
        .. describe:: x != y
        
            Checks if two users are not equal.
        
        .. describe:: hash(x)
        
            Returns the user's hash.
        
        .. describe:: str(x)
        
            Returns the user's name with discriminator.
    
    .. note::
        :attr:`~discord.oauth2.User.email` and :attr:`discord.oauth2.User.verified` are only present
        if authorized with the :attr:`~OAuth2Scope.email`. Otherwise they are :obj:`MISSING`
    
    Attributes
    -----------
    id: :class:`int`
        The user's ID.
    name: :class:`str`
        The user's username.
    discriminator: :class:`str`
        The user's discriminator (4-digit discord-tag).
    avatar: Optional[:class:`str`]
        The user's avatar hash.
    bot: :class:`bool`
        Indicates if the user is a bot account. Should always be :obj:`False` as bots can't use OAuth2.
    system: :class:`bool`
        Indicates if the user is a system account.
    mfa_enabled: :class:`bool`
        Indicates if the user has MFA enabled on their account.
    banner: Optional[:class:`str`]
        The user's banner hash.
    banner_color: Optional[:class:`~discord.Colour`]
        The user's banner color.
    locale: Optional[:class:`~discord.Locale`]
        The user's chosen language option.
    verified: Optional[:class:`bool`]
        Indicates if the email on this account has been verified.
    email: Optional[:class:`str`]
        The user's email.
    premium_type: :class:`PremiumType`
        The user's premium subscription type.
    """
    __slots__ = (
        '_client', 'id', 'name', 'discriminator', 'avatar', 'bot', 'system', 'banner_color', 'mfa_enabled',
        'banner', 'locale', 'verified', 'email', '_public_flags', '_flags', 'premium_type',)
    
    def __init__(self, *, client: OAuth2Client, data: UserPayload):
        self._client = client
        self.id: int = int(data['id'])
        self.name: str = data['username']
        self.discriminator: str = data['discriminator']
        self.avatar: str = data.get('avatar')
        self.bot: bool = data.get('bot', False)
        self.system: bool = data.get('system', False)
        accent_color = data.get('accent_color', None)
        if accent_color:
            accent_color = Colour(accent_color)
        self.banner_color: Optional[Colour] = accent_color
        self.banner: Optional[str] = data.get('banner', None)
        self.mfa_enabled: bool = data.get('mfa_enabled', False)
        self.locale: Locale = try_enum(Locale, data.get('locale', None))
        email = data.get('email', MISSING)
        self.email: str = email
        self.verified: bool = data.get('verified', MISSING if email is MISSING else False)
        self.premium_type: Optional[PremiumType] = try_enum(PremiumType, data.get('premium_type', None))
        self._flags: int = data.get('flags', 0)
        self._public_flags: int = data.get('public_flags', 0)
    
    def __str__(self) -> str:
        return '{0.name}#{0.discriminator}'.format(self)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.id == self.id

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self):
        return self.id >> 22
    
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
    def flags(self) -> PublicUserFlags:
        """:class:`PublicUserFlags`: The available flags the user has."""
        return PublicUserFlags._from_value(self._flags)

    @property
    def public_flags(self) -> PublicUserFlags:
        """:class:`PublicUserFlags`: The available public flags the user has."""
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

    def avatar_url_as(
            self,
            *,
            format: Optional[Literal['jpeg', 'jpg', 'webp', 'png', 'gif']] = None,
            static_format: Literal['jpeg', 'jpg', 'webp', 'png', 'gif'] = 'webp',
            size=1024
    ) -> Asset:
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
        return Asset._from_avatar(self._client, self, format=format, static_format=static_format, size=size)

    @property
    def default_avatar(self) -> DefaultAvatar:
        """:class:`DefaultAvatar`: Returns the default avatar for a given user. This is calculated by the user's discriminator."""
        return try_enum(DefaultAvatar, int(self.discriminator) % len(DefaultAvatar))

    @property
    def default_avatar_url(self) -> Asset:
        """:class:`Asset`: Returns a URL for a user's default avatar."""
        return Asset(self._client, '/embed/avatars/{}.png'.format(self.default_avatar.value))

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
            format: Optional[Literal['jpeg', 'jpg', 'webp', 'png', 'gif']] = None,
            static_format: Literal['png', 'jpeg', 'webp'] = 'webp',
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
        return Asset._from_banner(self._client, self, format=format, static_format=static_format, size=size)

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user in discord."""
        return '<@{0.id}>'.format(self)

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the user's creation time in UTC.

        This is when the user's Discord account was created."""
        return snowflake_time(self.id)
        
    
class PartialGuild(Hashable):
    """Represents a partial guild returned by the OAuth2 API."""
    def __init__(self, *, client: OAuth2Client, data: PartialGuildPayload):
        self._client: OAuth2Client = client
        self.id: SnowflakeID = int(data['id'])
        self.name: str = data['name']
        self.features: List[str] = data.get('features', [])
        self.icon: Optional[str] = data.get('icon', None)
        self.owner: Optional[bool] = data.get('owner', False)
        self.permissions: Optional[Permissions] = Permissions(int(data.get('permissions', 0)))
    
    @property
    def icon_url(self):
        """:class:`Asset`: Returns the guild's icon asset."""
        return self.icon_url_as()

    def is_icon_animated(self):
        """:class:`bool`: Returns True if the guild has an animated icon."""
        return bool(self.icon and self.icon.startswith('a_'))

    def icon_url_as(
            self,
            *,
            format: Literal['webp', 'jpeg', 'jpg', 'png', 'gif'] = None,
            static_format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp',
            size=1024
    ):
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
        return Asset._from_guild_icon(self._client, self, format=format, static_format=static_format, size=size)


class GuildMember(Hashable, _BaseUser):
    """Represents a member of a guild.

    .. container:: operations

        .. describe:: x == y

            Checks if two members are equal.

        .. describe:: x != y

            Checks if two members are not equal.

        .. describe:: hash(x)

            Returns the member's hash.

        .. describe:: str(x)

            Returns the member's name with discriminator.

    Attributes
    -----------
    joined_at: :class:`datetime.datetime`
        When the member joined the guild.
    deaf: :class:`bool`
        Indicates if the member is deafened.
    mute: :class:`bool`
        Indicates if the member is muted.
    pending: :class:`bool`
        Indicates if the member is pending verification.
    nick: Optional[:class:`str`]
        The member's nickname. Could be ``None``.
    guild_avatar: Optional[:class:`str`]
        The member's guild-specific avatar hash. Could be ``None``.
    premium_since: Optional[:class:`datetime.datetime`]
        When the member started boosting the guild.
    role_ids: :class:`~discord.utils.SnowflakeList`
        A list of role ids for roles the member has.
    """
    __slots__ = (
        '_client', 'id', 'guild', 'joined_at', 'deaf', 'mute', 'pending', 'nick', 'guild_avatar', 'premium_since',
        '_user', 'role_ids', '_flags', '_communication_disabled_until'
    )

    def __init__(self, *, client: OAuth2Client, data: GuildMemberPayload):
        self._client: OAuth2Client = client
        self.id: SnowflakeID = int(data['user']['id'])
        self.joined_at: datetime = datetime.fromisoformat(data['joined_at'])
        self.deaf: bool = data['deaf']
        self.mute: bool = data['mute']
        self.pending: bool = data.get('pending', False)
        self.nick: Optional[str] = data.get('nick', None)
        self.guild_avatar: Optional[str] = data.get('avatar', None)
        self.premium_since: Optional[datetime] = datetime.fromisoformat(data['premium_since']) if data.get('premium_since') else None
        self._user: BaseUser = BaseUser(state=client, data=data['user'])
        self.role_ids: SnowflakeList = SnowflakeList(map(int, data.get('roles', [])))
        self._flags = data.get('flags', 0)
        self._communication_disabled_until: Optional[str] = data.get('communication_disabled_until', None)

    def __str__(self):
        return str(self._user)
    
    def __repr__(self):
        return '<GuildMember id={1.id} name={1.name!r} discriminator={1.discriminator!r}' \
               ' nick={0.nick!r}>'.format(self, self._user)

    def __eq__(self, other):
        return isinstance(other, _BaseUser) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._user)

    @property
    def flags(self) -> GuildMemberFlags:
        """:class:`GuildMemberFlags`: Guild specific flags for the member."""
        return GuildMemberFlags._from_value(self._flags)
    
    @property
    def mention(self):
        """:class:`str`: Returns a string that allows you to mention the member in discord."""
        return '<@%s>' % self.id
    
    @property
    def display_name(self):
        """:class:`str`: Returns the user's display name.

        For regular users this is just their username, but
        if they have a guild specific nickname then that
        is returned instead.
        """
        return self.nick or self._user.name
    
    @property
    def communication_disabled_until(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: The time until the member is timeouted, if any"""
        return datetime.fromisoformat(self._communication_disabled_until) if self._communication_disabled_until else None

    @property
    def guild_avatar_url(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild-specific banner asset for the member if any."""
        return self.guild_avatar_url_as()

    def guild_avatar_url_as(
        self,
        *,
        format: Optional[Literal['jpeg', 'jpg', 'webp', 'png', 'gif']] = None,
        static_format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp',
        size: int = 1024
    ) -> Optional[Asset]:
        """Returns an :class:`Asset` for the guild-specific avatar of the member if any, else :obj:`None`.
    
        The format must be one of 'webp', 'jpeg', or 'png'. The
        size must be a power of 2 between 16 and 4096.
    
        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the avatar to.
        static_format: Optional[:class:`str`]
            Format to attempt to convert only non-animated avatars to.
        size: :class:`int`
            The size of the image to display.
    
        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.
    
        Returns
        --------
        Optional[:class:`Asset`]
            The resulting CDN asset if any.
        """
        if self.guild_avatar:
            return Asset._from_guild_avatar(self._client, self, static_format=static_format, format=format, size=size)

    def is_guild_avatar_animated(self):
        """:class:`bool`: Indicates if the member has an animated guild-avatar."""
        return bool(self.guild_avatar and self.guild_avatar.startswith('a_'))

    @property
    def display_avatar_url(self) -> Asset:
        """:class:`Asset`: Returns the guild-specific avatar asset for the member if he has one, else the default avatar asset"""
        return self.guild_avatar_url or self._user.avatar_url

    def display_avatar_url_as(
        self,
        format: Optional[Literal['jpeg', 'jpg', 'webp', 'png', 'gif']] = None,
        static_format: Literal['jpeg', 'jpg', 'webp', 'png', 'gif'] = 'webp',
        size: int = 1024
    ) -> Optional[Asset]:
        """
        Same behaviour as :meth:`~discord.oauth2.User.avatar_url_as` and :meth:`~discord.oauth2.GuildMember.guild_avatar_url_as`
        but it prefers the guild-specific avatar
        
        Returns
        --------
        :class:`Asset`:
            The resulting CDN asset for the avatar
        """
        if self.guild_avatar:
            return self.guild_avatar_url_as(format=format, static_format=static_format, size=size)
        return self._user.avatar_url_as(format=format, static_format=static_format, size=size)


from ..integrations import Integration


class Connection:
    """Represents a connection of a user to a service.

    .. container:: operations

        .. describe:: str(x)

            Returns the connection's name.

    Attributes
    -----------
    id: :class:`str`
        The connection id.
    name: :class:`str`
        The connection's name.
    type: :class:`str`
        The connection's type.
    revoked: :class:`bool`
        Indicates if the connection is revoked.
    integrations: List[:class:`Integration`]
        A list of integrations for the connection.
    verified: :class:`bool`
        Indicates if the connection is verified.
    friend_sync: :class:`bool`
        Indicates if the connection is syncing friends.
    show_activity: :class:`bool`
        Indicates if the connection is showing activity.
    visibility: :class:`int`
        The visibility of the connection.
    """

    __slots__ = (
        '_client', 'id', 'name', 'type', 'revoked', 'integrations', 'verified', 'friend_sync', 'show_activity', 'visibility'
    )

    def __init__(self, *, client: OAuth2Client, data: ConnectionData):
        self._client: OAuth2Client = client
        self.id: str = data['id']
        self.name: str = data['name']
        self.type: str = data['type']
        self.revoked: bool = data['revoked']
        self.integrations: List[Integration] = [Integration(data=i) for i in data.get('integrations', [])]
        self.verified: bool = data['verified']
        self.friend_sync: bool = data['friend_sync']
        self.show_activity: bool = data['show_activity']
        self.visibility: int = data['visibility']

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Connection id={0.id} name={0.name!r} type={0.type!r}>'.format(self)
        
    