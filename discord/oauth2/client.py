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
from copy import copy
from typing import (
    Dict,
    List,
    Optional
)

from typing_extensions import Self

from .errors import InvalidAuthorizationCode
from .http import OAuth2HTTPClient
from .models import *
from ..errors import HTTPException
from ..utils import (MISSING, SupportsStr)


class OAuth2Client:
    def __init__(
            self,
            client_id: int,
            client_secret: str,
            *,
            loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.loop: asyncio.AbstractEventLoop = loop
        self.client_id: int = client_id
        self.__client_secret: str = client_secret
        self.access_tokens: List[AccessToken] = []
        self.http: OAuth2HTTPClient = OAuth2HTTPClient(client_id=client_id, client_secret=client_secret, loop=loop)
    
    def __aenter__(self):
        return self.start()
    
    def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.close()
    
    async def store_access_token(self, access_token: AccessToken) -> None:
        self.access_tokens.append(access_token)

    async def store_refreshed_access_token(self, old_access_token: AccessToken, new_access_token: AccessToken) -> None:
        pass
    
    async def store_access_tokens(self) -> None:
        pass

    async def load_access_token(self, *args, **kwargs) -> AccessToken:
        pass

    async def load_access_tokens(self) -> Dict[int, AccessToken]:
        return {}
    
    async def remove_revoked_access_token(self, access_token: AccessToken) -> None:
        pass
    
    def run(self):
        loop = self.loop
        
        if not loop:
            try:
                self.loop = loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        
        if loop.is_running():
            loop.create_task(self.start(), name=f'{self.__class__.__name__}.start')
        else:
            return loop.run_until_complete(self.start())
    
    async def start(self) -> Self:
        if not self.loop:
            self.loop = self.http.loop = asyncio.get_running_loop()
        
        self.access_tokens = await self.load_access_tokens()
        self.http.start()
        return self
    
    async def close(self) -> None:
        await self.http.close()
        await self.store_access_tokens()
    
    async def authorize(self, code: str, redirect_uri: str, /) -> AccessToken:
        """|coro|
        
        Retrieves a users access token by doing a post-request with the authorization code to ``https://discord.com/api/oauth2/token``
        
        Attributes
        ----------
        code: :class:`str`
            The access code from ``https://discord.com/oauth2/authorize``
        redirect_uri: :class:`str`
            The redirect_uri associated with this authorization, usually from your authorization URL
        
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
        self.loop.create_task(self.store_access_token(access_token))
        return access_token
    
    async def refresh_access_token(self, access_token: AccessToken, /) -> AccessToken:
        """|coro|
        
        Refreshes an access token using its :attr:`~.AccessToken.refresh_token` and returns the updated instance.
        
        Attributes
        ----------
        access_token: :class:`.AccessToken`
            The access_token to refresh
        
        Returns
        -------
        :class:`.AccessToken`
            The refreshed token
        """
        data = await self.http.exchange_refresh_token(access_token.refresh_token)
        old_access_token = copy(access_token)
        access_token._update(data)
        self.loop.create_task(self.store_refreshed_access_token(old_access_token, access_token))
        return access_token
    
    async def revoke_access_token(self, access_token: AccessToken) -> None:
        """|coro|
        
        Revokes an access token. It will no longer be usable.
        
        """
        await self.http.revoke_access_token(access_token.access_token)
        self.loop.create_task(self.remove_revoked_access_token(access_token))
        self.loop.create_task(self.store_access_tokens())
    
    async def fetch_access_token_info(self, access_token: AccessToken, /):
        """|coro|
        
        Fetches info about the current authorization.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch info for
        """
        data = await self.http.get_current_auth_info(access_token.access_token)
        return data
    
    async def fetch_user(self, access_token: AccessToken, /) -> User:
        """|coro|
        
        Fetches the user associated with the access token. Requires the :attr:`OAuth2Scope.IDENTIFY` scope.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch the user for
        
        Returns
        -------
        :class:`discord.User`
            The user associated with the access token
        """
        data = await self.http.get_user(access_token.access_token)
        return data
    
    async def fetch_guilds(self, access_token: AccessToken) -> List[PartialGuild]:
        """|coro|
        
        Fetches the guilds the current user is a member of. Requires the :attr:`OAuth2Scope.GUILDS` scope.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch the guilds for
        """
        data = await self.http.get_user_guilds(access_token.access_token)
        return data
    
    async def fetch_guild_member(self, access_token, guild_id: SupportsStr) -> GuildMember:
        """|coro|
        
        Fetches the guild member of the current user in the guild. Requires the :attr:`OAuth2Scope.READ_GUILD_MEMBERS` scope.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch the guild member for
        guild_id: :class:`SupportsStr`
            The ID of the guild to fetch the guild member for
        
        Returns
        -------
        :class:`discord.GuildMember`
            The guild member of the current user in the guild
        """
        data = await self.http.get_user_guild_member(access_token.access_token, guild_id)
        return data
    
    async def fetch_connections(self, access_token: AccessToken) -> List[Connection]:
        """|coro|
        
        Fetches the connections of the current user. Requires the :attr:`OAuth2Scope.CONNECTIONS` scope.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch the connections for
        
        Returns
        -------
        List[:class:`.Connection`]
            The connections of the current user
        """
        data = await self.http.get_user_connections(access_token.access_token)
        return data
    
    async def fetch_user_app_role_connection(self, access_token: AccessToken) -> RoleConnection:
        """|coro|
        
        Fetches the role connection of the current user if any. Requires the :attr:`OAuth2Scope.WRITE_ROLE_CONNECTIONS` scope.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to fetch the role connection for
        
        Returns
        -------
        :class:`.RoleConnection`
            The role connection of the current user
        """
        data = await self.http.get_user_application_role_connection(access_token.access_token)
        return data
    
    async def update_user_app_role_connection(
            self,
            access_token: AccessToken,
            *,
            platform_name: str = MISSING,
            platform_username: str = MISSING,
            metadata: RoleConnectionMetadata = MISSING,
            application_id: int = None
    ):
        """|coro|
        
        Updates the role connection of the current user. Requires the :attr:`OAuth2Scope.WRITE_ROLE_CONNECTIONS` scope.
        
        Parameters
        ----------
        access_token: :class:`.AccessToken`
            The access token to update the role connection for
        platform_name: :class:`str`
            The vanity name of the platform a bot has connected (max 50 characters)
        platform_username: :class:`str`
            The username on the platform a bot has connected (max 100 characters)
        metadata: :class:`.RoleConnectionMetadata`
            The metadata of the role connection
        
        Returns
        -------
        :class:`.RoleConnection`
            The updated role connection of the current user
        """
        payload = {}
        if platform_name is not MISSING:
            payload['platform_name'] = platform_name
        if platform_username is not MISSING:
            payload['platform_username'] = platform_username
        if metadata is not MISSING:
            payload['metadata'] = metadata.to_dict()
        
        data = await self.http.update_user_application_role_connection(access_token.access_token, payload)
        return data
