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
    overload,
    Set,
    Union,
    List,
    Type,
    TYPE_CHECKING,
    TypeVar
)
from typing_extensions import (
    Self,
    Literal
)

from datetime import (
    datetime,
    timedelta,
    timezone
)

from ..mixins import Hashable
from ..asset import Asset
from ..enums import Locale, DefaultAvatar, PremiumType, IntegrationType, try_enum
from ..flags import ApplicationFlags, PublicUserFlags, GuildMemberFlags
from ..utils import (
    cached_property,
    utcnow,
    snowflake_time,
    SnowflakeList,
    SupportsStr,
    MISSING
)
from ..user import BaseUser, _BaseUser
from ..member import flatten_user
from ..permissions import Permissions
from ..webhook import Webhook

from .enums import OAuth2Scope, ConnectionService
from .errors import (
    AccessTokenNotRefreshable
)

if TYPE_CHECKING:
    from ..types import (
        user,
        guild,
        appinfo
    )
    from ..types.snowflake import SnowflakeID
    from .client import OAuth2Client
    from . import types


T = TypeVar('T')
DatetimeLike = Union[int, str, datetime]


__all__ = (
    'AccessToken',
    'AccessTokenInfo',
    'PartialAppInfo',
    'User',
    'PartialGuild',
    'PartialGuildIntegration',
    'PartialUser',
    'GuildMember',
    'Connection',
    'RoleConnection'
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
    
    Attributes
    -----------
    additional_data: :class:`dict`
        Additional data that was stored in the access token.
    
    
    .. container:: operations
        
        .. describe:: x == y
            
            Checks if two access tokens are equal.
        
        .. describe:: x != y
            
            Checks if two access tokens are not equal.
        
        .. describe:: str(x)
            
            Returns the :attr:`~AccessToken.access_token` **Be careful where you use this!**
        
        .. describe:: x[key]
            
            Returns the additional data stored in the access token.
        
        .. describe:: x[key] = value
            
            Sets the additional data stored in the access token.
        
        .. describe:: del x[key]
            
            Deletes the additional data stored in the access token.
        
        .. describe:: key in x
            
            Checks if the given key is stored in the additional data.
        
        .. describe:: iter(x)
            
            Returns an iterator over the additional data.
        
        .. describe:: len(x)
            
            Returns the amount of additional data stored in the access token.
    """
    def __init__(
            self,
            client: OAuth2Client,
            /,
            access_token: str,
            expires_at: DatetimeLike,
            refresh_token: Optional[str] = None,
            scopes: Iterable[str] = None,
            **additional_data: Any,
    ):
        """
        A representation of a
        `access token response <https://discord.com/developers/docs/topics/oauth2#authorization-code-grant-access-token-response>`_
        from discord.
        
        This can be also used to store additional data that can be accessed through get item.
        
        Parameters
        -----------
        client: :class:`OAuth2Client`
            The client that created this access token
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
        self._client: OAuth2Client = client
        self._access_token: str = access_token
        self._expires_at: datetime = convert_to_datetime(expires_at)
        self._refresh_token: Optional[str] = refresh_token
        self._scopes: Set[str] = set(scopes)
        self.additional_data: Dict[str, Any] = additional_data
    
    def __str__(self) -> str:
        return self._access_token
    
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} expires_at={self.expires_at.isoformat()} scopes={", ".join(str(s) for s in self.scopes)}>'
    
    def __getitem__(self, item: str) -> Any:
        return self.additional_data.get(item)
    
    def __setitem__(self, key: str, value: Any):
        self.additional_data[key] = value
    
    @property
    def client(self) -> Optional[OAuth2Client]:
        """
        The :class:`~discord.oauth2.OAuth2Client` that manages this access token.
        """
        return self._client
    
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

    @cached_property
    def scopes(self) -> Set[OAuth2Scope]:
        """
        A set of :class:`~discord.oauth2.OAuth2Scope` that the access token is authorized to.
        """
        return {try_enum(OAuth2Scope, scope) for scope in self._scopes}
    
    @cached_property
    def webhook(self) -> Optional[Webhook]:
        """:class:`~discord.Webhook`: The webhook that was created with the webhook when the access token was authorized
        with the :attr:`~OAuth2Scope.CREATE_WEBHOOK` scope. Only available on the original access token instance"""
        return getattr(self, '_webhook', None)
    
    @property
    def refreshable(self) -> bool:
        """:class:`bool`: Whether the access token is refreshable. This checks if the :attr:`.refresh_token` is set"""
        return self.refresh_token is not None
    
    def is_expired(self) -> bool:
        """:class:`bool`: Whether the access token is expired. This just checks if the :attr:`~AccessToken.expires_at` is in the past"""
        return utcnow() > self.expires_at
    
    @classmethod
    def from_raw_data(cls, client: OAuth2Client, data: types.AccessToken) -> AccessToken:
        """
        Creates an :class:`~discord.oauth2.AccessToken` from raw data returned by discord.
        
        Parameters
        -----------
        client: :class:`~discord.oauth2.OAuth2Client`
            The client that created this access token
        data: :class:`AccessToken`
            The raw data returned by discord
        
        Returns
        --------
        :class:`AccessToken`
            The access token object
        """
        expires_at = convert_to_datetime(data.pop('expires_in'), from_delta=True)  # type: ignore
        scopes = data.pop('scope', '').split(' ')  # type: ignore
        base = cls(client, expires_at=expires_at, scopes=scopes, **data)
        
        try:
            webhook = data.pop('webhook')
        except KeyError:
            pass
        else:
            base._webhook = Webhook.from_oauth2(webhook, client)
        
        return base
    
    def _update(self, data: types.AccessToken) -> Self:
        self._access_token = data['access_token']
        self._expires_at = convert_to_datetime(data['expires_in'], from_delta=True)
        self._refresh_token = data['refresh_token']
        return self
    
    def to_dict(self) -> Union[types.AccessTokenWithAbsoluteTime, types.ClientCredentialsAccessTokenWithAbsoluteTime]:
        """
        Converts the access token data to a dictionary.
        
        Structure of the dictionary:
        
        .. code-block:: python3
        
            {
                'access_token': str,
                'token_type': 'Bearer',
                'expires_at': str,
                'scopes': List[str],
                'refresh_token': NotRequired[str]
                'webhook_url': NotRequired[str]
            }
            
        Example
        -------
        
        .. code-block:: python3
        
            {
                "access_token": "6qrZcUqja7812RVdnEKjpzOL4CvHBFG",
                "token_type": "Bearer",
                "expires_at": "2018-06-10T21:20:00+00:00",
                "scopes": ["identify", "guilds"],
                "refresh_token": "D43f5y0ahjqew82jZ4NViEr2YafMKhue"  # only available when refresh_token is set
                "webhook_url": "https://discord.com/api/v10/webhooks/12345678910/T0kEn0fw3Bh00K"  # only available when webhook is set
            }
        
        Returns
        --------
        Dict[:class:`str`, Any]
            The access token data as a dictionary
        """
        base = {
            'access_token': self.access_token,
            'token_type': 'Bearer',
            'expires_at': self.expires_at.isoformat(),
            'scopes': list(self._scopes)
        }
        refresh_token = self.refresh_token
        webhook = self.webhook
        if refresh_token:
            base['refresh_token'] = refresh_token
        if webhook:
            base['webhook_url'] = webhook.url
        
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
        AttributeError
            The client attribute is not set
        :exc:`AccessTokenNotRefreshable`:
            The access token is not refreshable
        :exc:`InvalidRefreshToken`
            The refresh token is invalid or has expired
        
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

        return await self._client.refresh_access_token(self)
    
    async def revoke(self) -> None:
        """|coro|
        
        Revokes the access token.
        
        For more details, see :meth:`.OAuth2Client.revoke_access_token`.
        """
        
        client = self.client
        if not client:
            raise AttributeError('client attribute is not set so you can\'t call this from the access token directly')
        
        await self._client.revoke_access_token(self)

    @overload
    async def fetch_info(self) -> AccessTokenInfo: ...

    @overload
    async def fetch_info(self, *, raw: Literal[False]) -> AccessTokenInfo: ...

    @overload
    async def fetch_info(self, *, raw: Literal[True]) -> types.CurrentAuthorizationInfo: ...

    async def fetch_info(
            self,
            *,
            raw: Literal[True, False] = False
    ) -> Union[AccessTokenInfo, types.CurrentAuthorizationInfo]:
        """|coro|
        
        Fetches the authorization information for the access token.
        
        Fpr details, see :meth:`.OAuth2Client.fetch_access_token_info`.
        """
        return await self._client.fetch_access_token_info(self)
    
    @overload
    async def fetch_user(self) -> User: ...
    
    @overload
    async def fetch_user(self, *, raw: Literal[False]) -> User: ...

    @overload
    async def fetch_user(self, *, raw: Literal[True]) -> types.User: ...
    
    async def fetch_user(self, *, raw: Literal[True, False] = False) -> Union[User, types.User]:
        """|coro|
        
        Fetches the user associated with the access token.
        
        For details, see :meth:`.OAuth2Client.fetch_user`.
        """
        return await self._client.fetch_user(self, raw=raw)
    
    @overload
    async def fetch_guilds(self) -> List[PartialGuild]: ...
    
    @overload
    async def fetch_guilds(self, *, raw: Literal[False]) -> List[PartialGuild]: ...
    
    @overload
    async def fetch_guilds(self, *, raw: Literal[True]) -> List[guild.PartialGuild]: ...
    
    async def fetch_guilds(self, *, raw: Literal[True, False] = False) -> Union[List[PartialGuild], List[guild.PartialGuild]]:
        """|coro|
        
        Fetches the guilds associated with the access token.
        
        For details, see :meth:`.OAuth2Client.fetch_guilds`.
        """
        return await self._client.fetch_guilds(self, raw=raw)
    
    @overload
    async def fetch_guild_member(self, guild_id: SnowflakeID, /) -> GuildMember: ...
    
    @overload
    async def fetch_guild_member(self, guild_id: SnowflakeID, /, *, raw: Literal[False]) -> GuildMember: ...
    
    @overload
    async def fetch_guild_member(self, guild_id: SnowflakeID, /, *, raw: Literal[True]) -> user.Member: ...
    
    async def fetch_guild_member(self, guild_id: SnowflakeID, /, *, raw: Literal[True, False] = False) -> Union[GuildMember, user.Member]:
        """|coro|
        
        Fetches the guild member of the current user in the guild. Requires the :attr:`OAuth2Scope.READ_GUILD_MEMBERS` scope.
        
        For details, see :meth:`.OAuth2Client.fetch_guild_member`.
        """
        return await self._client.fetch_guild_member(self, guild_id, raw=raw)
    
    @overload
    async def add_guild_member(
        self,
        /, *,
        bot_token: SupportsStr,
        guild_id: SupportsStr,
        user_id: SupportsStr,
        nick: str = MISSING,
        roles: List[SupportsStr] = MISSING,
        mute: bool = MISSING,
        deaf: bool = MISSING
    ) -> GuildMember: ...
    
    @overload
    async def add_guild_member(
        self,
        /, *,
        bot_token: SupportsStr,
        guild_id: SupportsStr,
        user_id: SupportsStr,
        nick: str = MISSING,
        roles: List[SupportsStr] = MISSING,
        mute: bool = MISSING,
        deaf: bool = MISSING,
        raw: Literal[False]
    ) -> GuildMember: ...
    
    @overload
    async def add_guild_member(
        self,
        /, *,
        bot_token: SupportsStr,
        guild_id: SupportsStr,
        user_id: SupportsStr,
        nick: str = MISSING,
        roles: List[SupportsStr] = MISSING,
        mute: bool = MISSING,
        deaf: bool = MISSING,
        raw: Literal[True]
    ) -> user.Member: ...
    
    async def add_guild_member(
        self,
        /, *,
        bot_token: SupportsStr,
        guild_id: SupportsStr,
        user_id: SupportsStr,
        nick: str = MISSING,
        roles: List[SupportsStr] = MISSING,
        mute: bool = MISSING,
        deaf: bool = MISSING,
        raw: Literal[True, False] = False
    ):
        """|coro|
        
        Adds a user to a guild using their access token.
        
        For details, see :meth:`.OAuth2Client.add_guild_member`.
        """
        return await self._client.add_guild_member(
            self,
            bot_token=bot_token,
            guild_id=guild_id,
            user_id=user_id,
            nick=nick,
            roles=roles,
            mute=mute,
            deaf=deaf,
            raw=raw
        )
    
    @overload
    async def fetch_connections(self, /) -> List[Connection]: ...
    
    @overload
    async def fetch_connections(self, /, *, raw: Literal[False]) -> List[Connection]: ...
    
    @overload
    async def fetch_connections(self, /, *, raw: Literal[True]) -> List[types.Connection]: ...
    
    async def fetch_connections(self, /, *, raw: Literal[True, False] = False) -> Union[List[Connection], List[types.Connection]]:
        """|coro|
        
        Fetches the connections associated with the access token.
        
        For details, see :meth:`.OAuth2Client.fetch_connections`.
        """
        return await self._client.fetch_connections(self, raw=raw)
    
    @overload
    async def fetch_user_app_role_connection(self, /) -> RoleConnection: ...
    
    @overload
    async def fetch_user_app_role_connection(self, /, *, raw: Literal[False]) -> RoleConnection: ...
    
    @overload
    async def fetch_user_app_role_connection(self, /, *, raw: Literal[True]) -> types.RoleConnection: ...
    
    async def fetch_user_app_role_connection(self, /, *, raw: Literal[True, False] = False) -> Union[RoleConnection, types.RoleConnection]:
        """|coro|
        
        Fetches the application role connection associated with the access token.
        
        For details, see :meth:`.OAuth2Client.fetch_user_app_role_connection`.
        """
        return await self._client.fetch_user_app_role_connection(self, raw=raw)

    @overload
    async def update_user_app_role_connection(
            self,
            /, *,
            platform_name: str = MISSING,
            platform_username: str = MISSING,
            metadata: Dict[str, str] = MISSING,
            application_id: int = None
    ) -> RoleConnection: ...
    
    @overload
    async def update_user_app_role_connection(
            self,
            /, *,
            platform_name: str = MISSING,
            platform_username: str = MISSING,
            metadata: Dict[str, str] = MISSING,
            application_id: int = None,
            raw: Literal[False]
    ) -> RoleConnection: ...
    
    @overload
    async def update_user_app_role_connection(
            self,
            /, *,
            platform_name: str = MISSING,
            platform_username: str = MISSING,
            metadata: Dict[str, str] = MISSING,
            application_id: int = None,
            raw: Literal[True]
    ) -> types.RoleConnection: ...
    
    async def update_user_app_role_connection(
            self,
            /, *,
            platform_name: str = MISSING,
            platform_username: str = MISSING,
            metadata: Dict[str, str] = MISSING,
            application_id: int = None,
            raw: Literal[True, False] = False
    ) -> Union[RoleConnection, types.RoleConnection]:
        """|coro|
        
        Updates the application role connection associated with the access token.
        
        For details, see :meth:`.OAuth2Client.update_user_app_role_connection`.
        """
        return await self._client.update_user_app_role_connection(
            self,
            platform_name=platform_name,
            platform_username=platform_username,
            metadata=metadata,
            application_id=application_id,
            raw=raw
        )


class PartialAppInfo:
    """Represents the application info for the bot provided by Discord.


    Attributes
    -------------
    id: :class:`int`
        The application ID.
    name: :class:`str`
        The application name.
    icon: Optional[:class:`str`]
        The icon hash, if it exists.
    description: Optional[:class:`str`]
        The application description.
    bot_public: :class:`bool`
        Whether the bot can be invited by anyone or if it is locked
        to the application owner.
    bot_require_code_grant: :class:`bool`
        Whether the bot requires the completion of the full oauth2 code
        grant flow to join.
    verify_key: :class:`str`
        The hex encoded key for verification in interactions and the
        GameSDK's `GetTicket <https://discord.com/developers/docs/game-sdk/applications#getticket>`_.
    """
    
    __slots__ = ('_client', 'description', 'id', 'name', 'bot_public', 'bot_require_code_grant', 'icon',
                 'verify_key', 'custom_install_url', 'tags', '_flags', 'interactions_endpoint_url')
    
    def __init__(self, *, client: OAuth2Client, data: appinfo.PartialAppInfo) -> None:
        self._client: OAuth2Client = client
        self.id = int(data['id'])
        self.name = data['name']
        self.description = data['description']
        self.icon = data['icon']
        self.bot_public: bool = data['bot_public']
        self.bot_require_code_grant: bool = data['bot_require_code_grant']
        self.tags: List[str] = data.get('tags', [])
        self._flags = data.get('flags', 0)
        self.verify_key = data['verify_key']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r} description={self.description!r} ' \
               f'public={self.bot_public}>'
    
    @property
    def icon_url(self) -> Asset:
        """:class:`~discord.Asset`: Retrieves the application's icon asset.

        This is equivalent to calling :meth:`icon_url_as` with
        the default parameters ('webp' format and a size of 1024).
        """
        return self.icon_url_as()
    
    def icon_url_as(
            self,
            *,
            format: Literal['png', 'jpeg', 'jpg', 'webp'] = 'webp',
            size=1024
    ) -> Asset:
        """Returns an :class:`~discord.Asset` for the icon the application has.

        The format must be one of 'webp', 'jpeg', 'jpg' or 'png'.
        The size must be a power of 2 between 16 and 4096.

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the icon to. Defaults to 'webp'.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`~discord.Asset`
            The resulting CDN asset.
        """
        return Asset._from_icon(self._client, self, 'app', format=format, size=size)
    
    @property
    def flags(self):
        return ApplicationFlags._from_value(self._flags)


class AccessTokenInfo:
    """Represents the authorization information for an access token."""
    __slots__ = ('_client', '_application', '_scopes', '_expires_at', '_user')
    
    def __init__(self, *, client: OAuth2Client, data: types.CurrentAuthorizationInfo):
        self._client: OAuth2Client = client
        self._application = data['application']
        self._scopes = data['scopes']
        self._expires_at = data['expires']
        self._user = data['user']
    
    def __repr__(self) -> str:
        return '<AccessTokenInfo app={0.application!r} scopes={0.scopes!r} expires_at={0.expires_at!r} user={0.user!r}>'.format(self)
    
    @property
    def application(self) -> PartialAppInfo:
        """:class:`~discord.oauth2.PartialAppInfo`: The application the access token is authorized for."""
        return PartialAppInfo(client=self._client, data=self._application)
    
    @property
    def scopes(self) -> Set[OAuth2Scope]:
        """Set[:class:`~discord.oauth2.OAuth2Scope`]: A list of scopes the access token is authorized to."""
        return {try_enum(OAuth2Scope, scope) for scope in self._scopes}
    
    @property
    def expires_at(self) -> datetime:
        """:class:`~datetime.datetime`: The time when the access token expires."""
        return datetime.fromisoformat(self._expires_at)
    
    @property
    def user(self) -> PartialUser:
        """:class:`PartialUser`: The user associated with the access token."""
        return PartialUser(client=self._client, data=self._user)
    
    def to_dict(self) -> types.CurrentAuthorizationInfo:
        return {
            'application': self._application,
            'scopes': self._scopes,
            'expires': self._expires_at,
            'user': self._user,
        }


class PartialUser(_BaseUser):
    """Represents a partial Discord User retrieved via an OAuth2 :class:`AccessToken`.

    This

    .. container:: operations
        
        .. describe:: x == y
            Checks if two partial users are equal.
        
        .. describe:: x != y
            Checks if two partial users are not equal.
        
        .. describe:: hash(x)
            Returns the partial user's hash.
        
        .. describe:: str(x)
            Returns the :attr:`username` if :attr:`is_migrated` is true, else the user's name with discriminator.

            .. note::

                When the migration is complete, this will always return the :attr:`username` .

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The user's ID.
    username: :class:`str`
        The user's username.
    global_name: Optional[:class:`str`]
        The users global name if set.
        In the client UI this referred to as "Display Name".
    discriminator: :class:`str`
        The user's discriminator.

        .. deprecated:: 2.0

        .. important::
            This will be removed in the future.
            Read more about it :dis-gd:`here <usernames>`.
    avatar: Optional[:class:`str`]
        The user's avatar hash.
    avatar_decoration: Optional[:class:`str`]
        The user's avatar decoration hash.
    """
    def __init__(self, *, client: OAuth2Client, data: types.User):
        self._client = client
        self.id: int = int(data['id'])
        self.username: str = data['username']
        self.global_name: Optional[str] = data.get('global_name')
        self.discriminator: str = data.get('discriminator')
        self.avatar: str = data.get('avatar')
        self.avatar_decoration: str = data.get('avatar_decoration')
        self._public_flags: int = data.get('public_flags', 0)

    def __str__(self) -> str:
        return f'{self.username}' if self.is_migrated else f'{self.name}#{self.discriminator}'
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, _BaseUser) and other.id == self.id

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return self.id >> 22

    @property
    def name(self) -> str:
        """:class:`str`: This is an alias of :attr:`username` which replaces the previous `name` attribute.

        .. note::
            It is recommended to use :attr:`username` instead as this might be removed in the future.
        """
        return self.username

    @property
    def is_migrated(self) -> bool:
        """:class:`bool`: Indicates if the user has migrated to the :dis-gd:`new username system <usernames>`."""
        return self.discriminator == '0'

    @property
    def public_flags(self) -> PublicUserFlags:
        """:class:`PublicUserFlags`: The available public flags the user has."""
        return PublicUserFlags._from_value(self._public_flags)

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user in discord."""
        return f'<@{self.id}>'

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name.

        For regular users this is just their :attr:`global_name` if set else their :attr:`username`, but
        if they have a guild specific nickname then that
        is returned instead.
        """
        return self.global_name or self.username

    @property
    def created_at(self) -> datetime:
        """:class:`~datetime.datetime`: Returns the user's creation time in UTC.

        This is when the user's Discord account was created."""
        return snowflake_time(self.id)
    
    @property
    def avatar_url(self) -> Asset:
        """:class:`~discord.Asset`: Returns an :class:`~discord.Asset` for the avatar the user has.

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
            static_format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp',
            size=1024
    ) -> Asset:
        """Returns an :class:`~discord.Asset` for the avatar the user has.

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
        :class:`~discord.Asset`
            The resulting CDN asset.
        """
        return Asset._from_avatar(self._client, self, format=format, static_format=static_format, size=size)

    @property
    def default_avatar(self) -> DefaultAvatar:
        """:class:`DefaultAvatar`: Returns the default avatar for a given user.
        For non-migrated users this is calculated by the user's discriminator.
        For :dis-gd:`migrated <usernames>` users this is calculated by the user's ID.
        """
        if self.is_migrated:
            value = (self.id >> 22) % len(DefaultAvatar)
        else:
            value = int(self.discriminator) % len(DefaultAvatar)
        return try_enum(DefaultAvatar, value)

    @property
    def default_avatar_url(self) -> Asset:
        """:class:`~discord.Asset`: Returns a URL for a user's default avatar."""
        return Asset(self._client, f'/embed/avatars/{self.default_avatar.value}.png')


class User(BaseUser):
    """Represents a full Discord user retrieved via an OAuth2 :class:`AccessToken`.
    
    .. note::
        :attr:`~discord.oauth2.User.email` and :attr:`discord.oauth2.User.verified` are only present
        if authorized with the :attr:`~OAuth2Scope.email`. Otherwise they are :obj:`MISSING`
    
    Attributes
    -----------
    id: :class:`int`
        The user's ID.
    username: :class:`str`
        The user's username.
    global_name: Optional[:class:`str`]
        The users global name if set.
        In the client UI this referred to as "Display Name".
    discriminator: :class:`str`
        The user's discriminator.

        .. deprecated:: 2.0

        .. important::
            This will be removed in the future.
            Read more about it :dis-gd:`here <usernames>`.
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
    locale: Optional[:class:`~discord.Locale`]
        The user's chosen language option.
    verified: Optional[:class:`bool`]
        Indicates if the email on this account has been verified.
    email: Optional[:class:`str`]
        The user's email.
    premium_type: :class:`PremiumType`
        The user's premium subscription type.
    """
    __slots__ = BaseUser.__slots__ + (
        '_client', 'mfa_enabled', 'locale', 'verified', 'email', '_flags', 'premium_type',
    )
    
    def __init__(self, *, client: OAuth2Client, data: types.User):
        super().__init__(state=client, data=data)
        self._client: OAuth2Client = client
        self.mfa_enabled: bool = data.get('mfa_enabled', False)
        self.locale: Locale = try_enum(Locale, data.get('locale', None))
        email = data.get('email', MISSING)
        self.email: str = email
        self.verified: bool = data.get('verified', MISSING if email is MISSING else False)
        self.premium_type: Optional[PremiumType] = try_enum(PremiumType, data.get('premium_type', None))
        self._flags: int = data.get('flags', 0)


    @property
    def flags(self) -> PublicUserFlags:
        """:class:`PublicUserFlags`: The available flags the user has. This might be the same as :attr:`public_flags`."""
        return PublicUserFlags._from_value(self._flags)

    @classmethod
    def _copy(cls: Type[User], user: User) -> User:
        return super()._copy(user)


class PartialGuild(Hashable):
    """
    Represents a partial guild returned by the OAuth2 API.
    
    .. container:: operations
        
        .. describe:: x == y
            
            Checks if two partial guilds are equal.
        
        .. describe:: x != y
            
            Checks if two partial guilds are not equal.
            
        .. describe:: hash(x)
            
            Returns the partial guild's hash.
        
        .. describe:: str(x)
            Returns the partial guild's name.
            
    Attributes
    -----------
    id: :class:`int`
        The guild's ID.
    name: :class:`str`
        The guild's name.
    features: List[:class:`str`]
        The guild's features.
    icon: Optional[:class:`str`]
        The guild's icon hash.
    owner: Optional[:class:`bool`]
        Indicates if the user is the owner of the guild.
    permissions: Optional[:class:`Permissions`]
        The permissions the user has in the guild.
    """
    def __init__(self, *, client: OAuth2Client, data: guild.PartialGuild):
        self._client: OAuth2Client = client
        self.id: SnowflakeID = int(data['id'])
        self.name: str = data['name']
        self.features: List[str] = data.get('features', [])
        self.icon: Optional[str] = data.get('icon', None)
        self.owner: Optional[bool] = data.get('owner', False)
        self.permissions: Optional[Permissions] = Permissions(int(data.get('permissions', 0)))
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return '<PartialGuild id={0.id} name={0.name!r} features={0.features!r}>'.format(self)
    
    @property
    def icon_url(self):
        """:class:`~discord.Asset`: Returns the guild's icon asset."""
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
        """Returns an :class:`~discord.Asset` for the guild's icon.

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
        :class:`~discord.Asset`
            The resulting CDN asset.
        """
        return Asset._from_guild_icon(self._client, self, format=format, static_format=static_format, size=size)

@flatten_user(PartialUser)
class GuildMember(_BaseUser):
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
    id: :class:`int`
        The member's ID.
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

    if TYPE_CHECKING:
        name: str
        username: str
        global_name: str
        id: int
        discriminator: str
        bot: bool
        system: bool
        created_at: datetime
        default_avatar: str
        avatar: Optional[str]
        public_flags: PublicUserFlags
        banner: Optional[str]

    def __init__(self, *, client: OAuth2Client, data: user.Member):
        self._client: OAuth2Client = client
        self.id: SnowflakeID = int(data['user']['id'])
        self.joined_at: datetime = datetime.fromisoformat(data['joined_at'])
        self.deaf: bool = data['deaf']
        self.mute: bool = data['mute']
        self.pending: bool = data.get('pending', False)
        self.nick: Optional[str] = data.get('nick', None)
        self.guild_avatar: Optional[str] = data.get('avatar', None)
        self.premium_since: Optional[datetime] = datetime.fromisoformat(data['premium_since']) if data.get('premium_since') else None
        self._user: PartialUser = PartialUser(client=client, data=data['user'])
        self.role_ids: SnowflakeList = SnowflakeList(map(int, data.get('roles', [])))
        self._flags = data.get('flags', 0)
        self._communication_disabled_until: Optional[str] = data.get('communication_disabled_until', None)

    def __str__(self):
        return str(self._user)
    
    def __repr__(self) -> str:
        user = self._user
        if not user.is_migrated:
            return f'<GuildMember id={user.id} username={user.username!r} global_name={user.global_name} ' \
                   f'discriminator={user.discriminator!r} nick={self.nick!r} guild={self.guild!r}>'
        return f'<GuildMember id={user.id} username={user.username!r} global_name={user.global_name} ' \
               f'nick={self.nick!r} guild={self.guild!r}>'

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, _BaseUser) and other.id == self.id

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self._user)

    @property
    def flags(self) -> GuildMemberFlags:
        """:class:`GuildMemberFlags`: Guild specific flags for the member."""
        return GuildMemberFlags._from_value(self._flags)
    
    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the member in discord."""
        return f'<@{self.id}>'
    
    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name.

        For regular users this is just their username, but
        if they have a guild specific nickname then that
        is returned instead.
        """
        return self.nick or self._user.display_name
    
    @property
    def communication_disabled_until(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: The time until the member is timeouted, if any"""
        return datetime.fromisoformat(self._communication_disabled_until) if self._communication_disabled_until else None

    @property
    def guild_avatar_url(self) -> Optional[Asset]:
        """Optional[:class:`~discord.Asset`]: Returns the guild-specific banner asset for the member if any."""
        return self.guild_avatar_url_as()

    def guild_avatar_url_as(
        self,
        *,
        format: Optional[Literal['jpeg', 'jpg', 'webp', 'png', 'gif']] = None,
        static_format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp',
        size: int = 1024
    ) -> Optional[Asset]:
        """Returns an :class:`~discord.Asset` for the guild-specific avatar of the member if any, else :obj:`None`.
    
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
        Optional[:class:`~discord.Asset`]
            The resulting CDN asset if any.
        """
        if self.guild_avatar:
            return Asset._from_guild_avatar(self._client, self, static_format=static_format, format=format, size=size)

    def is_guild_avatar_animated(self):
        """:class:`bool`: Indicates if the member has an animated guild-avatar."""
        return bool(self.guild_avatar and self.guild_avatar.startswith('a_'))

    @property
    def display_avatar_url(self) -> Asset:
        """:class:`~discord.Asset`: Returns the guild-specific avatar asset for the member if he has one, else the default avatar asset"""
        return self.guild_avatar_url or self._user.avatar_url

    def display_avatar_url_as(
        self,
        format: Optional[Literal['jpeg', 'jpg', 'webp', 'png', 'gif']] = None,
        static_format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp',
        size: int = 1024
    ) -> Optional[Asset]:
        """
        Same behaviour as :meth:`~discord.oauth2.User.avatar_url_as` and :meth:`~discord.oauth2.GuildMember.guild_avatar_url_as`
        but it prefers the guild-specific avatar
        
        Returns
        --------
        :class:`~discord.Asset`:
            The resulting CDN asset for the avatar
        """
        if self.guild_avatar:
            return self.guild_avatar_url_as(format=format, static_format=static_format, size=size)
        return self._user.avatar_url_as(format=format, static_format=static_format, size=size)


class PartialGuildIntegration:
    """Represents a partial integration in a guild."""
    def __init__(self, *, data):
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.type: IntegrationType = try_enum(IntegrationType, data['type'])
        self.enabled: bool = data['enabled']
        self.syncing: bool = data['syncing']
        self.role_id: Optional[int] = int(data['role_id']) if data['role_id'] else None
        self.expire_behavior = data['expire_behavior']
        self.expire_grace_period = data['expire_grace_period']
        self.account = data['account']
        self.synced_at: datetime = datetime.fromisoformat(data['synced_at'])


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
        '_client', 'id', 'name', 'type', 'revoked', '_integrations', 'verified', 'friend_sync', 'show_activity', 'visibility'
    )

    def __init__(self, *, client: OAuth2Client, data: types.Connection):
        self._client: OAuth2Client = client
        self.id: str = data['id']
        self.name: str = data['name']
        self.type: ConnectionService = try_enum(ConnectionService, data['type'])
        self.revoked: bool = data.get('revoked', False)
        self._integrations: List[types.PartialGuildIntegration] = data.get('integrations', [])
        self.verified: bool = data['verified']
        self.friend_sync: bool = data['friend_sync']
        self.show_activity: bool = data['show_activity']
        self.visibility: int = data['visibility']

    def __repr__(self):
        return '<Connection type={0.type!r} name={0.name!r} id={0.id}>'.format(self)
    
    @property
    def integrations(self) -> List[PartialGuildIntegration]:
        """List[:class:`Integration`]: A list of partial guild integrations for the connection."""
        return [PartialGuildIntegration(data=i) for i in self._integrations]
    
    def get_platform_user_url(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns the platform user url for the connection if available."""
        
        connection_type = str(self.type)
        
        if connection_type == 'twitch':
            return f'https://www.twitch.tv/{self.name}'
        elif connection_type == 'youtube':
            return f'https://www.youtube.com/channel/{self.id}'
        elif connection_type == 'github':
            return f'https://github.com/{self.name}'
        elif connection_type == 'instagram':
            return f'https://www.instagram.com/{self.name}/'
        elif connection_type == 'skype':
            return f'https://www.skype.com/{self.name}'
        elif connection_type == 'tiktok':
            return f'https://www.tiktok.com/{self.name}'
        elif connection_type == 'twitter':
            return f'https://twitter.com/{self.name}'
        elif connection_type == 'reddit':
            return f'https://www.reddit.com/user/{self.name}'
        elif connection_type == 'steam':
            return f'https://steamcommunity.com/profiles/{self.id}'
        elif connection_type == 'xbox':
            return f'https://account.xbox.com/en-US/Profile?Gamertag={self.name}'
        elif connection_type == 'spotify':
            return f'https://open.spotify.com/user/{self.id}'
        elif connection_type == 'ebay':
            return f'https://www.ebay.com/usr/{self.name}'
        return None


class RoleConnection:
    def __init__(self, *, data: types.RoleConnection):
        self.platform_name: Optional[str] = data['platform_name']
        self.platform_username: Optional[str] = data['platform_username']
        self.metadata: Dict[str, str] = data['metadata']
    
    def __repr__(self):
        return '<RoleConnection platform={0.platform_name!r} username={0.platform_username!r}>'.format(self)


