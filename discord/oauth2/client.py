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

import asyncio
from aiosignal import Signal
from copy import copy
import logging
from functools import wraps

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    overload,
    TYPE_CHECKING,
    TypeVar,
    Union
)

from typing_extensions import (
    Literal,
    Self
)

from .errors import *
from .http import OAuth2HTTPClient
from .models import *
from ..errors import HTTPException, Unauthorized
from ..application_commands import (
    AppCommandPermission,
    GuildAppCommandPermissions
)
from ..utils import (
    MISSING,
    setup_logging as _setup_logging,
    SupportsStr
)

if TYPE_CHECKING:
    from . import types
    from ..types import (
        app_command,
        guild,
        user
    )
    from ..types.snowflake import SnowflakeID
    
    from typing_extensions import (
        ParamSpec
    )
    
    T = TypeVar('T')
    P = ParamSpec('P')
    

__all__ = (
    'AccessTokenStore',
    'OAuth2Client',
)


_log = logging.getLogger(__name__)


def handle_auto_refresh(func: Callable[P, T]) -> T:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except AccessTokenExpired as exc:
            self: OAuth2Client
            access_token: AccessToken
            if exc.refreshable:
                self, access_token = args[:2]
                if self.auto_refresh:
                    _log.debug('Access token expired or invalid, auto-refreshing...')
                    access_token = await self.refresh_access_token(access_token)
                    return await func(self, access_token, *args[2:], **kwargs)
                raise
            raise
    
    return wrapper


class AccessTokenStore:
    """
    Base class for an access token store.
    
    Attributes
    ----------
    oauth2_client: :class:`OAuth2Client`
        The client that this store is associated with.
    """
    oauth2_client: OAuth2Client
    
    async def on_startup(self) -> None:
        """|coro|
        
        This is called by the :class:`OAuth2Client` when it is starting up.
        
        This can be used to initialise a database connection or similar.
        
        By default, this calls :meth:`load_access_tokens`.
        """
        await self.load_access_tokens()
    
    async def on_close(self) -> None:
        """|coro|
        
        This is called by the :class:`OAuth2Client` when it is closing.
        
        This can be used to close a database connection or similar.
        
        By default, this calls :meth:`store_access_tokens`.
        """
        await self.store_access_tokens()
    
    async def store_access_token(self, access_token: AccessToken) -> None:
        """|coro|
        
        This is called by the :class:`OAuth2Client` when a new access token is created using :meth:`OAuth2Client.authorize`.
        
        It can be used to store the access token to a database or similar.
        
        Parameters
        ----------
        access_token: :class:`AccessToken`
            The access token that was created.
        """
        pass
    
    async def store_refreshed_access_token(self, old_access_token: AccessToken, new_access_token: AccessToken) -> None:
        """|coro|
        
        This is called by the :class:`OAuth2Client` when an access token is refreshed using :meth:`OAuth2Client.refresh_access_token`.
        
        It can be used to update the database entry for the access token with the new data.
        
        Parameters
        ----------
        old_access_token: :class:`AccessToken`
            The old access token that was refreshed.
        new_access_token: :class:`AccessToken`
            The new access token that was refreshed.
        """
        pass
    
    async def store_access_tokens(self) -> None:
        """|coro|
        
        This can be used to store access tokens to a database or similar.
        
        .. note::
            By default this is called by :meth:`on_close`.
        """
        pass
    
    async def load_access_token(self, *args, **kwargs) -> AccessToken:
        """|coro|
        
        This can be used to load an access token from a database or similar.
        """
        raise NotImplementedError('load_access_token must be implemented by a subclass of discord.oauth2.AccessTokenStore')
    
    async def load_access_tokens(self) -> Any:
        """|coro|
        
        This can be used to load access tokens from a database or similar.
        
        .. note::
            By default this is called by :meth:`on_startup`.
        """
        pass
    
    async def remove_revoked_access_token(self, access_token: AccessToken) -> None:
        """|coro|
        
        This is called by the :class:`OAuth2Client` when an access token is revoked using :meth:`OAuth2Client.revoke_access_token`.
        
        It can be used to remove the access token from the database or similar.
        
        Parameters
        ----------
        access_token: :class:`AccessToken`
            The access token that was revoked.
        """
        pass


class OAuth2Client:
    def __init__(
        self,
        client_id: int,
        client_secret: str,
        access_token_store: Optional[AccessTokenStore] = AccessTokenStore(),
        *,
        auto_refresh: bool = True,
        log_level: Optional[int] = logging.INFO,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        """
        A class for interacting with the Discord OAuth2 API.
        
        Parameters
        ----------
        client_id: :class:`int`
            The client ID of your application.
        client_secret: :class:`str`
            The client secret of your application.
        access_token_store: :class:`AccessTokenStore`
            The access token store to use to store and update and load the access_tokens.
            Must be a subclass of :class:`AccessTokenStore`
        auto_refresh: :class:`bool`
            Whether to automatically refresh access tokens when :exc:`AccessTokenExpired` is raised.
        log_level: Optional[:class:`int`]
            The log level to use for the internal logger.
        loop: Optional[:class:`asyncio.AbstractEventLoop`]
            The event loop to use for the internal HTTP client.
            Only required if you are using a custom event loop.
        
        Attributes
        ----------
        client_id: :class:`int`
            The client ID of your application.
        access_token_store: :class:`AccessTokenStore`
            The access token store to use to store and update and load the access_tokens.
            Must be a subclass of :class:`AccessTokenStore`
        auto_refresh: :class:`bool`
            Whether to automatically refresh access tokens when :exc:`AccessTokenExpired` is raised.
        loop: :class:`asyncio.AbstractEventLoop`
            The event loop that the client is running on.
        """
        self.loop: asyncio.AbstractEventLoop = loop
        self.client_id: int = client_id
        if not issubclass(access_token_store.__class__, AccessTokenStore):
            raise TypeError(f'access_token_store must be a subclass of discord.oauth2.AccessTokenStore')
        self.access_token_store: AccessTokenStore = access_token_store
        access_token_store.oauth2_client = self
        self._closed: bool = False
        self._on_startup = Signal(self)
        self._on_close = Signal(self)
        self.on_startup.append(access_token_store.on_startup)
        self.on_close.append(access_token_store.on_close)
        self.__client_secret: str = client_secret
        self.auto_refresh: bool = auto_refresh
        self.http: OAuth2HTTPClient = OAuth2HTTPClient(client_id=client_id, client_secret=client_secret, loop=loop)
        self.__log_level: Optional[int] = log_level
        self.__logging_setup_done: bool = False
    
    def __aenter__(self):
        return self.start()
    
    def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.close()
    
    def is_closed(self) -> bool:
        return self._closed
    
    @property
    def on_startup(self):
        return self._on_startup
    
    @property
    def on_close(self):
        return self._on_close
    
    def setup_logging(
            self,
            *,
            log_handler: Optional[logging.Handler] = MISSING,
            log_formatter: logging.Formatter = MISSING,
            log_level: int = MISSING,
            root_logger: bool = False
    ) -> Optional[logging.Logger]:
        """
        Sets up the `:mod:`logging` library to make it easier for beginners to know what is going on with the library.
        For more advanced users, this can be disabled by passing :obj:`None` to the ``log_handler`` parameter.
        
        .. note::
        
            This will only return the logger when called the first time on this instance.
            Subsequent calls will return :obj:`None`.
            
            So if you want to get the logger, you should call this method yourself before starting the client.
            
            
        Parameters
        ----------
        log_handler: Optional[:class:`logging.Handler`]
            The log handler to use for the library's logger. If this is :obj:`None`
            then the library will not set up anything logging related. Logging
            will still work if :obj:`None` is passed, though it is your responsibility
            to set it up.
            The default log handler if not provided is :class:`logging.StreamHandler`.
        log_formatter: :class:`logging.Formatter`
            The formatter to use with the given log handler. If not provided then it
            defaults to a colour based logging formatter (if available).
        log_level: :class:`int`
            The default log level for the library's logger. This is only applied if the
            ``log_handler`` parameter is not :obj:`None`.
            Defaults to the value of ``log_level`` in the init or :attr:`logging.INFO`.
        root_logger: :class:`bool`
            Whether to set up the root logger rather than the library logger.
            By default, only the library logger (``'discord'``) is set up. If this
            is set to :obj:`True` then the root logger is set up as well.
            Defaults to :obj:`False`.
        
        Returns
        -------
        Optional[:class:`logging.Logger`]
            The logger that was set up. This is the library logger if ``root_logger``
        """
        if not self.__logging_setup_done:
            self.__logging_setup_done = True
            if log_handler is not None:
                if log_level is MISSING:
                    log_level = self.__log_level
                if log_level is not None:
                    return _setup_logging(
                        handler=log_handler,
                        formatter=log_formatter,
                        level=log_level,
                        root=root_logger
                    )
    
    async def start(self) -> Self:
        """|coro|
        
        Starts the client. This will start the internal HTTP client and call the :attr:`on_startup` event.
        
        .. important::
            This must be called before any other requests are made.
        """
        self.setup_logging()
        
        if not self.loop:
            self.loop = self.http.loop = asyncio.get_running_loop()
        
        self.on_startup.freeze()
        self.on_close.freeze()
        
        self.http.start()
        self._closed = False
        await self.on_startup.send()
        return self
    
    async def close(self) -> None:
        await self.http.close()
        await self.on_close.send()
        self._closed = True
    
    async def authorize(self, code: str, redirect_uri: str) -> AccessToken:
        """|coro|
        
        Retrieves a users access token by doing a post-request with the authorization code to ``https://discord.com/api/oauth2/token``
        
        Parameters
        ----------
        code: :class:`str`
            The access code from ``https://discord.com/oauth2/authorize``
        redirect_uri: :class:`str`
            The redirect_uri associated with this authorization, usually from your authorization URL
        
        Raises
        ------
        :exc:`InvalidAuthorizationCode`
            The authorization code is invalid or has expired
        :exc:`HTTPException`
            Requesting the access token failed
        
        Returns
        -------
        :class:`AccessToken`
            The access token for the user
        """
        try:
            data = await self.http.exchange_authorization_token(code, redirect_uri)
        except HTTPException as e:
            if e.status == 400:
                raise InvalidAuthorizationCode()
            raise
        
        access_token = AccessToken.from_raw_data(self, data)
        await self.access_token_store.store_access_token(access_token)
        return access_token
    
    async def refresh_access_token(self, access_token: AccessToken, /) -> AccessToken:
        """|coro|
        
        Refreshes an access token using its :attr:`~.AccessToken.refresh_token` and returns the updated instance.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access_token to refresh
        
        Raises
        ------
        :exc:`InvalidRefreshToken`
            The refresh token is invalid or has expired
        
        Returns
        -------
        :class:`.AccessToken`
            The refreshed token
        """
        try:
            data = await self.http.exchange_refresh_token(access_token.refresh_token)
        except HTTPException as e:
            if e.status == 400:
                raise InvalidRefreshToken() from e
            raise
        
        old_access_token = copy(access_token)
        access_token._update(data)

        await self.access_token_store.store_refreshed_access_token(old_access_token, access_token)

        return access_token
    
    async def revoke_access_token(self, access_token: AccessToken, /) -> None:
        """|coro|
        
        Revokes an access token. It will no longer be usable.
        
        Parameters
        ----------
        access_token: :class:`AccessToken`
            The access token to revoke
        
        Raises
        ------
        :exc:`HTTPException`
            Revoking the access token failed
        """
        await self.http.revoke_access_token(access_token.access_token)
        await self.access_token_store.remove_revoked_access_token(access_token)
    
    @overload
    async def fetch_access_token_info(self, access_token: AccessToken, /) -> AccessTokenInfo: ...
    
    @overload
    async def fetch_access_token_info(self, access_token: AccessToken, /, *, raw: Literal[True]) -> types.CurrentAuthorizationInfo: ...
    
    @handle_auto_refresh
    async def fetch_access_token_info(
            self,
            access_token: AccessToken,
            /, *,
            raw: bool = False
    ) -> Union[AccessTokenInfo, types.CurrentAuthorizationInfo]:
        """|coro|
        
        Fetches info about the current authorization.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch info for
        raw: :class:`bool`
            Whether to return the raw data or not
        
        Raises
        ------
        :exc:`AccessTokenExpired`
            The access token is expired (this might be handled automatically when :attr:`auto_refresh` is ``True``)
        
        Returns
        -------
        :class:`~discord.oauth2.AccessTokenInfo`
            The info about the current authorization
        :class:`dict`
            The raw data if ``raw`` is ``True``
        """
        try:
            data = await self.http.get_current_auth_info(access_token.access_token)
        except Unauthorized:
            raise AccessTokenExpired(access_token.refreshable)
        
        if raw:
            return data
        
        return AccessTokenInfo(data=data, client=self)
    
    @overload
    async def fetch_user(self, access_token: AccessToken, /) -> User: ...
    
    @overload
    async def fetch_user(self, access_token: AccessToken, /, *, raw: Literal[False]) -> User: ...

    @overload
    async def fetch_user(self, access_token: AccessToken, /, *, raw: Literal[True]) -> types.User: ...

    @handle_auto_refresh
    async def fetch_user(self, access_token: AccessToken, /, *, raw: bool = False) -> Union[User, types.User]:
        """|coro|
        
        Fetches the user associated with the access token. Requires the :attr:`~OAuth2Scope.IDENTIFY` scope.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch the user for
        raw: :class:`bool`
            Whether to return the raw data, defaults to ``False``
        
        Returns
        -------
        :class:`~discord.oauth2.User`
            The user associated with the access token
        :class:`dict`
            The raw data if ``raw`` is ``True``
        """
        try:
            data = await self.http.get_user(access_token.access_token)
        except Unauthorized:
            raise AccessTokenExpired(access_token.refreshable)
        
        if raw:
            return data
        
        return User(client=self, data=data)
    
    @overload
    async def fetch_guilds(self, access_token: AccessToken, /) -> List[PartialGuild]: ...
    @overload
    async def fetch_guilds(self, access_token: AccessToken, /, *, raw: Literal[True]) -> List[guild.PartialGuild]: ...
    
    @handle_auto_refresh
    async def fetch_guilds(self, access_token: AccessToken, /, *, raw: bool = False) -> Union[List[PartialGuild], List[guild.PartialGuild]]:
        """|coro|
        
        Fetches the guilds the current user is a member of. Requires the :attr:`~OAuth2Scope.GUILDS` scope.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch the guilds for
        raw: :class:`bool`
            Whether to return the raw data, defaults to ``False``
        
        Returns
        -------
        List[:class:`PartialGuild`]
            The guilds the current user is a member of
        List[:class:`dict`]
            The raw data if ``raw`` is ``True``
        """
        try:
            data = await self.http.get_user_guilds(access_token.access_token)
        except Unauthorized:
            raise AccessTokenExpired(access_token.refreshable)
        
        if raw:
            return data
        
        return [PartialGuild(client=self, data=d) for d in data]
    
    @overload
    async def fetch_guild_member(self, access_token: AccessToken, guild_id: SupportsStr, /) -> GuildMember: ...
    
    @overload
    async def fetch_guild_member(self, access_token: AccessToken, guild_id: SupportsStr, /, *, raw: Literal[True]) -> user.Member: ...
    
    @handle_auto_refresh
    async def fetch_guild_member(self, access_token, guild_id: SupportsStr, *, raw: bool = False) -> Union[GuildMember, user.Member]:
        """|coro|
        
        Fetches the guild member of the current user in the guild. Requires the :attr:`~OAuth2Scope.READ_GUILD_MEMBERS` scope.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch the guild member for
        guild_id: :class:`SupportsStr`
            The ID of the guild to fetch the guild member for
        raw: :class:`bool`
            Whether to return the raw data, defaults to ``False``
        
        Raises
        ------
        :exc:`AccessTokenExpired`
            The access token is expired (this might be handled automatically when :attr:`auto_refresh` is ``True``)
        
        Returns
        -------
        :class:`GuildMember`
            The guild member of the current user in the guild
        :class:`dict`
            The raw data if ``raw`` is ``True``
        """
        try:
            data = await self.http.get_user_guild_member(access_token.access_token, guild_id)
        except Unauthorized:
            raise AccessTokenExpired(access_token.refreshable)
        
        if raw:
            return data
        
        return GuildMember(client=self, data=data)
    
    @overload
    async def add_guild_member(
            self,
            access_token: AccessToken,
            /, *,
            bot_token: SupportsStr,
            guild_id: SupportsStr,
            user_id: SupportsStr,
            nick: str = MISSING,
            roles: List[SupportsStr] = MISSING,
            mute: bool = MISSING,
            deaf: bool = MISSING,
    ) -> GuildMember: ...
    
    @overload
    async def add_guild_member(
            self,
            access_token: AccessToken,
            /, *,
            bot_token: SupportsStr,
            guild_id: SupportsStr,
            user_id: SupportsStr,
            nick: str = MISSING,
            roles: List[SupportsStr] = MISSING,
            mute: bool = MISSING,
            deaf: bool = MISSING,
            raw: Literal[True],
    ) -> user.Member: ...
    
    @handle_auto_refresh
    async def add_guild_member(
            self,
            access_token: AccessToken,
            /, *,
            bot_token: SupportsStr,
            guild_id: SupportsStr,
            user_id: SupportsStr,
            nick: str = MISSING,
            roles: List[SupportsStr] = MISSING,
            mute: bool = MISSING,
            deaf: bool = MISSING,
            raw: bool = False,
    ) -> Union[user.Member, GuildMember]:
        """
        Adds a user to a guild using their access token.
        
        .. note::
            This requires the ``access_token`` to be authorized with the :attr:`~OAuth2Scope.JOIN_GUILDS` scope.
            Furthermore, the bot must be a member of the guild with the :attr:`~Permissions.create_instant_invite` permissions.
        
        .. warning::
            You should always ask for the user's consent before adding them to a guild.
        
        The ``nick``, ``roles``, ``mute`` and ``deaf`` parameters are optional and requires different permission for the bot.
        
        +-----------------+-------------------------------------------------------+
        | Parameter       | Required Permissions                                  |
        +=================+=======================================================+
        | ``nick``        | :attr:`~discord.Permissions.manage_nicknames`         |
        +-----------------+-------------------------------------------------------+
        | ``roles``       | :attr:`~discord.Permissions.manage_roles`             |
        +-----------------+-------------------------------------------------------+
        | ``mute``        | :attr:`~discord.Permissions.mute_members`             |
        +-----------------+-------------------------------------------------------+
        | ``deaf``        | :attr:`~discord.Permissions.deafen_members`           |
        +-----------------+-------------------------------------------------------+
        
        Parameters
        ----------
        access_token: :class:`AccessToken`
            The access token for the user to add to the guild.
        bot_token: :class:`SupportsStr`
            The bot token for the bot. This is required for authorization.
        guild_id: :class:`SupportsStr`
            The ID of the guild to add the user to.
        user_id: :class:`SupportsStr`
            The ID of the user to add to the guild. If you don\'t store the user ID already you can get it using :meth:`fetch_user`.
        nick: :class:`str`
            The nickname to give the user. Defaults to ``None``.
        roles: List[:class:`SupportsStr`]
            A list of role IDs for roles to give the member on join. Defaults to ``None``.
            
            .. important::
            
                For guilds with `membership screening <https://support.discord.com/hc/en-us/articles/1500000466882-Membership-Screening-FAQ>`_ enabled,
                assigning a role using the roles parameter will add the user to the guild as a full member
                (:attr:`~discord.oauth2.GuildMember.pending` will be ``False``).
                
                **A member with a role will bypass membership screening, onboarding and the guild's verification level, and get immediate access to chat.**
                Therefore, instead of assigning a role when the member joins, it is recommended to grant roles only after the user completes screening.
            
        mute: :class:`bool`
            Whether to mute the user on join. Defaults to ``False``.
        deaf: :class:`bool`
            Whether to deafen the user on join. Defaults to ``False``.
        raw: :class:`bool`
            Whether to return the raw data. Defaults to ``False``.
        
        Raises
        ------
        :exc:`AccessTokenExpired`
            The access token is expired (this might be handled automatically when :attr:`auto_refresh` is ``True``)
        :exc:`Forbidden`
            The bot does not have the :attr:`~Permissions.create_instant_invite` permission.
        :exc:`UserIsAtGuildLimit`
            The user cannot be added to the guild because they reached the guild limit of 100 (200 with nitro).
        :exc:`HTTPException`
            Adding the user to the guild failed.
        
        Returns
        -------
        :class:`~discord.oauth2.GuildMember`
            The guild member of the current user in the guild.
        :class:`dict`
            The raw data if ``raw`` is ``True``.
        """
        try:
            data = await self.http.add_guild_member(
                access_token.access_token,
                bot_token,
                guild_id=guild_id,
                user_id=user_id,
                nick=nick,
                roles=roles,
                mute=mute,
                deaf=deaf,
            )
        except Unauthorized:
            raise AccessTokenExpired(access_token.refreshable)
        except HTTPException as exc:
            if exc.status == 400 and exc.code == 30001:
                raise UserIsAtGuildLimit()
            raise
        
        if raw:
            return data
        
        return GuildMember(client=self, data=data) if data else None
    
    @overload
    async def fetch_connections(self, access_token: AccessToken, /) -> List[Connection]: ...
    
    @overload
    async def fetch_connections(self, access_token: AccessToken, /, *, raw: Literal[True]) -> List[types.Connection]: ...
    
    @handle_auto_refresh
    async def fetch_connections(self, access_token: AccessToken, /, *, raw: bool = False) -> Union[List[Connection], List[types.Connection]]:
        """|coro|
        
        Fetches the connections of the current user. Requires the :attr:`~OAuth2Scope.CONNECTIONS` scope.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch the connections for
        raw: :class:`bool`
            Whether to return the raw data, defaults to ``False``
        
        Raises
        ------
        :exc:`AccessTokenExpired`
            The access token is expired (this might be handled automatically when :attr:`auto_refresh` is ``True``)
        
        Returns
        -------
        List[:class:`.Connection`]
            The connections of the current user
        :class:`dict`
            The raw data if ``raw`` is ``True``
        """
        try:
            data = await self.http.get_user_connections(access_token.access_token)
        except Unauthorized:
            raise AccessTokenExpired(access_token.refreshable)
        
        if raw:
            return data
        
        return [Connection(client=self, data=d) for d in data]
    
    @overload
    async def fetch_user_app_role_connection(self, access_token: AccessToken, /) -> RoleConnection: ...
    
    @overload
    async def fetch_user_app_role_connection(self, access_token: AccessToken, /, *, raw: Literal[True]) -> types.RoleConnection: ...
    
    @handle_auto_refresh
    async def fetch_user_app_role_connection(
            self,
            access_token: AccessToken,
            /, *,
            raw: bool = False
    ) -> Union[RoleConnection, types.RoleConnection]:
        """|coro|
        
        Fetches the role connection of the current user if any. Requires the :attr:`~OAuth2Scope.WRITE_ROLE_CONNECTIONS` scope.
        
        Parameters
        ----------
        access_token: :class:`AccessToken`
            The access token to fetch the role connection for
        raw: :class:`bool`
            Whether to return the raw data, defaults to ``False``
        
        Raises
        ------
        :exc:`AccessTokenExpired`
            The access token is expired (this might be handled automatically when :attr:`auto_refresh` is ``True``)
        
        Returns
        -------
        :class:`.RoleConnection`
            The role connection of the current user
        :class:`dict`
            The raw data if ``raw`` is ``True``
        """
        try:
            data = await self.http.get_user_application_role_connection(access_token.access_token)
        except Unauthorized:
            raise AccessTokenExpired(access_token.refreshable)
        
        if raw:
            return data
        
        return RoleConnection(data=data)
    
    @overload
    async def update_user_app_role_connection(
            self,
            access_token: AccessToken,
            /, *,
            platform_name: str = MISSING,
            platform_username: str = MISSING,
            metadata: Dict[str, str] = MISSING,
            application_id: int = None
    ) -> RoleConnection: ...
    
    @overload
    async def update_user_app_role_connection(
            self,
            access_token: AccessToken,
            /, *,
            platform_name: str = MISSING,
            platform_username: str = MISSING,
            metadata: Dict[str, str] = MISSING,
            application_id: int = None,
            raw: Literal[True]
    ) -> types.RoleConnection: ...
    
    @handle_auto_refresh
    async def update_user_app_role_connection(
            self,
            access_token: AccessToken,
            /, *,
            platform_name: str = MISSING,
            platform_username: str = MISSING,
            metadata: Dict[str, str] = MISSING,
            application_id: int = None,
            raw: bool = False
    ) -> Union[RoleConnection, types.RoleConnection]:
        """|coro|
        
        Updates the role connection of the current user. Requires the :attr:`~OAuth2Scope.WRITE_ROLE_CONNECTIONS` scope.
        
        All parameters are optional and will only be updated if provided.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to update the role connection for
        platform_name: :class:`str`
            The vanity name of the platform a bot has connected (max 50 characters)
        platform_username: :class:`str`
            The username on the platform a bot has connected (max 100 characters)
        metadata: Dict[:class:`str`, :class:`str`]
            The metadata of the role connection.
            
            Mapping of :attr:`AppRoleConnectionMetadata.key` s to their string-ified value (max 100 characters)
        application_id: :class:`int`
            The ID of the application to update the role connection for.
            
            Only required if the application id is not the same as the client id (e.g. for some older applications)

        raw: :class:`bool`
            Whether to return the raw data, defaults to ``False``
        
        Returns
        -------
        :class:`.RoleConnection`
            The updated role connection of the current user
        :class:`dict`
            The raw data if ``raw`` is ``True``
        """
        payload = {}
        if platform_name is not MISSING:
            payload['platform_name'] = platform_name
        if platform_username is not MISSING:
            payload['platform_username'] = platform_username
        if metadata is not MISSING:
            payload['metadata'] = metadata
        
        data = await self.http.update_user_application_role_connection(access_token.access_token, data=payload, application_id=application_id)
        
        if raw:
            return data
        
        return RoleConnection(data=data)
    
    @overload
    async def fetch_all_application_command_permissions(
            self,
            access_token: AccessToken, /, *,
            guild_id: SnowflakeID,
            application_id: Optional[SnowflakeID] = None
    ) -> List[GuildAppCommandPermissions]: ...
    
    @overload
    async def fetch_all_application_command_permissions(
            self,
            access_token: AccessToken, /, *,
            guild_id: SnowflakeID,
            application_id: Optional[SnowflakeID] = None,
            raw: Literal[True]
    ) -> List[app_command.GuildApplicationCommandPermissions]: ...
    
    @handle_auto_refresh
    async def fetch_all_application_command_permissions(
            self,
            access_token: AccessToken, /, *,
            guild_id: SnowflakeID,
            application_id: Optional[SnowflakeID] = None,
            raw: bool = False
    ) -> Union[List[GuildAppCommandPermissions], List[app_command.GuildApplicationCommandPermissions]]:
        """|coro|
        
        Fetches all application command permissions for the given guild.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            An access token of a user that is a member of the guild to fetch the application-command permissions for.
        guild_id: Union[:class:`int`, :class:`str`]
            The ID of the guild to fetch the application-command permissions for.
        application_id: Optional[Union[:class:`int`, :class:`str`]]
            The ID of the application to fetch the permissions for.
            If not provided, defaults to the client's application ID.
            
            .. note::
                
                This is only required if the application ID is not the same as the client ID (e.g. for some older applications).
        raw: :class:`bool`
            Whether to return the raw data, defaults to ``False``
        
        Raises
        ------
        :exc:`AccessTokenExpired`
            The access token is expired (this might be handled automatically when :attr:`auto_refresh` is ``True``)
        :exc:`HTTPException`
            Fetching the application-command permissions failed.
        
        Returns
        -------
        List[:class:`.GuildApplicationCommandPermissions`]
            A list of all application command permissions for the given guild.
        List[:class:`dict`]
            The raw data if ``raw`` is ``True``.
        """
        data = await self.http.get_all_application_command_permissions(
            access_token.access_token, guild_id=guild_id, application_id=application_id
        )
        
        if raw:
            return data
        
        return [GuildAppCommandPermissions(data=entry) for entry in data]
    
    @overload
    async def fetch_application_command_permissions(
            self,
            access_token: AccessToken, /, *,
            guild_id: SnowflakeID,
            command_id: SnowflakeID,
            application_id: Optional[SnowflakeID] = None
    ) -> GuildAppCommandPermissions: ...
    
    @overload
    async def fetch_application_command_permissions(
            self,
            access_token: AccessToken, /, *,
            guild_id: SnowflakeID,
            command_id: SnowflakeID,
            application_id: Optional[SnowflakeID] = None,
            raw: Literal[True]
    ) -> app_command.GuildApplicationCommandPermissions: ...
    
    @handle_auto_refresh
    async def fetch_application_command_permissions(
            self,
            access_token: AccessToken, /, *,
            guild_id: SnowflakeID,
            command_id: SnowflakeID,
            application_id: Optional[SnowflakeID] = None,
            raw: bool = False
    ) -> Union[GuildAppCommandPermissions, app_command.GuildApplicationCommandPermissions]:
        """|coro|
        
        Fetches the permission overwrites for an application-command in a guild.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            An access token of a user that is a member of the guild to fetch the application-commands permissions for.
        guild_id: Union[:class:`int`, :class:`str`]
            The ID of the guild to fetch the application-command permissions for.
        command_id: Union[:class:`int`, :class:`str`]
            The ID of the application-command to fetch the permissions for.
        application_id: Optional[Union[:class:`int`, :class:`str`]]
            The ID of the application to fetch the permissions for.
            If not provided, defaults to the client's application ID.
            
            .. note::
                
                This is only required if the application ID is not the same as the client ID (e.g. for some older applications).
        raw: :class:`bool`
            Whether to return the raw data, defaults to ``False``
        
        Raises
        ------
        :exc:`AccessTokenExpired`
            The access token is expired (this might be handled automatically when :attr:`auto_refresh` is ``True``)
        :exc:`Forbidden`
            The application does not have the permission to fetch the permissions.
        :exc:`NotFound`
            The application-command or the guild was not found.
        
        Returns
        -------
        :class:`.GuildApplicationCommandPermissions`
            The permission overwrites for the application-command in the guild.
        :class:`dict`
            The raw data if ``raw`` is ``True
        """
        data = await self.http.get_application_command_permissions(
            access_token.access_token, guild_id=guild_id, command_id=command_id, application_id=application_id
        )
        
        if raw:
            return data
        
        return GuildAppCommandPermissions(data=data)
    
    @overload
    async def edit_application_command_permissions(
            self,
            access_token: AccessToken, /, *,
            guild_id: SnowflakeID,
            command_id: SnowflakeID,
            permissions: List[AppCommandPermission],
            application_id: Optional[SnowflakeID] = None
    ) -> GuildAppCommandPermissions: ...
    
    @overload
    async def edit_application_command_permissions(
            self,
            access_token: AccessToken, /, *,
            guild_id: SnowflakeID,
            command_id: SnowflakeID,
            permissions: List[AppCommandPermission],
            application_id: Optional[SnowflakeID] = None,
            raw: Literal[True]
    ) -> app_command.GuildApplicationCommandPermissions: ...
    
    @handle_auto_refresh
    async def edit_application_command_permissions(
            self,
            access_token: AccessToken, /, *,
            guild_id: SnowflakeID,
            command_id: SnowflakeID,
            permissions: List[AppCommandPermission],
            application_id: Optional[SnowflakeID] = None,
            raw: bool = False
    ) -> Union[GuildAppCommandPermissions, app_command.GuildApplicationCommandPermissions]:
        """|coro|
        
        Edits the permission overwrites for an application-command in a guild.
        Requires the :attr:`~OAuth2Scope.UPDATE_APPLICATIONS_COMMANDS_PERMISSIONS` scope.
        
        .. warning::
            
            This method will overwrite all existing permissions for the application-command.
            So if you want to keep the existing permissions, you need to include the existing ones in ``permissions``.
        
        .. note::
            
            The ``access_token`` must be of a user that is a member of the guild and the following permissions are required:
            
            - :attr:`.Permissions.manage_guild`
            - :attr:`.Permissions.manage_roles`
            - Has the ability to run the application-command
            - Has the permissions to manage the resources that will be affected (roles, users, and/or channels depending on the :attr:`.ApplicationCommandPermissions.type`)
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            An access token of a user that is a member of the guild to edit the application-command permissions for.
        guild_id: Union[:class:`int`, :class:`str`]
            The ID of the guild to edit the application-command permissions for.
        command_id: Union[:class:`int`, :class:`str`]
            The ID of the application-command to edit the permissions for.
        permissions: List[:class:`.ApplicationCommandPermissions`]
            The new permissions for the application-command.
        application_id: Optional[Union[:class:`int`, :class:`str`]]
            The ID of the application to edit the permissions for.
            If not provided, defaults to the client's application ID.
            
            .. note::
                
                This is only required if the application ID is not the same as the client ID (e.g. for some older applications).
        raw: :class:`bool`
            Whether to return the raw data, defaults to ``False``
        
        Raises
        ------
        :exc:`AccessTokenExpired`
            The access token is expired (this might be handled automatically when :attr:`auto_refresh` is ``True``)
        :exc:`.Forbidden`
            The application does not have the permission to edit the permissions.
        :exc:`NotFound`
            The application-command or the guild was not found.
        
        Returns
        -------
        :class:`.GuildApplicationCommandPermissions`
            The permission overwrites for the application-command in the guild.
        :class:`dict`
            The raw data if ``raw`` is ``True
        
        Examples
        --------
        Editing the permissions for an application-command in a guild:
        
            There is a command called "test" and now you want to ensure the following for the guild with the ID 852871920411475968:
            
            - ``@everyone`` should not be able to use the command
            - Every member with the role "Member" (ID: 852937257903456256) can use the command
            - The command should only be usable in the channel "commands" (ID: 853000092156035083)
            
        .. code-block:: python3
            
            import discord.oauth2 as oauth2
            
            from discord import (
                AppCommandPermission
                AppCommandPermissionType
            )
            
            # Assuming you have a OAuth2Client instance and a command called "test" with the ID 919316347165495356
            
            GUILD_ID = 852871920411475968
            MEMBER_ROLE_ID = 852937257903456256
            COMMAND_CHANNEL_ID = 853000092156035083
            COMMAND_ID = 919316347165495356
            
            permissions = [
                AppCommandPermission(
                    type=AppCommandPermissionType.ROLE,
                    id=GUILD_ID,  # Special constant for all members in the guild
                    permission=False
                ),  # Deny permission for @everyone
                AppCommandPermission(
                    type=AppCommandPermissionType.ROLE,
                    id=MEMBER_ROLE_ID,
                    permission=True
                ), # Allow permission for members with the "Member" role
                AppCommandPermission(
                    type=AppCommandPermissionType.CHANNEL,
                    id=GUILD_ID - 1,  # Special constant for "all channels"
                    permission=False
                )  # Deny permission for all channels
                AppCommandPermission(
                    type=AppCommandPermissionType.CHANNEL,
                    id=COMMAND_CHANNEL_ID,
                    permission=True
                )  # Allow permission for the "commands" channel
            ]
            
            await client.edit_application_command_permissions(
                access_token,
                guild_id=guild_id,
                command_id=COMMAND_ID,
                permissions=permissions
            )
            
        """
        data = await self.http.update_application_command_permissions(
            access_token.access_token,
            guild_id=guild_id,
            command_id=command_id,
            application_id=application_id,
            permissions=[permission.to_dict() for permission in permissions]
        )
        
        if raw:
            return data
        
        return GuildAppCommandPermissions(data=data)
