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

import asyncio
import logging
import sys
import weakref
from typing import (
    Any,
    Coroutine,
    List,
    Optional,
    TYPE_CHECKING,
    TypeVar,
    Union
)

import aiohttp
from typing_extensions import NoReturn

from .. import __version__
from ..errors import (
    DiscordServerError,
    Forbidden,
    Unauthorized,
    HTTPException,
    NotFound
)
from ..http import (
    json_or_text,
    MaybeUnlock,
    Route
)
from ..utils import (
    _parse_ratelimit_header,
    MISSING,
    to_json
)

if TYPE_CHECKING:
    from . import types
    from ..types import (
        app_command,
        guild,
        user
    )
    from ..enums import Locale
    from ..utils import SupportsStr
    
    T = TypeVar('T')
    Response = Coroutine[None, None, T]
    

__all__ = ('OAuth2HTTPClient',)

_log = logging.getLogger(__name__)


class OAuth2HTTPClient:
    """
    This class manages the async requests to the Discords OAuth2 API and manages ratelimiting automatically.
    
    """
    SUCCESS_LOG = '{method} {url} has received {text}'
    REQUEST_LOG = '{method} {url} with {json} has returned {status}'
    
    __session: aiohttp.ClientSession
    
    def __init__(
            self,
            client_id: int,
            client_secret: str,
            *,
            connector=None,
            proxy: Optional[str] = None,
            proxy_auth: Optional[aiohttp.BasicAuth] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None,
            unsync_clock: bool = True,
            api_version: int = 10,
            api_error_locale: Optional[Locale] = 'en-US'
    ):
        self.client_id: str = str(client_id)
        self.__client_secret: str = client_secret
        self.loop = loop
        self.connector = connector
        self._locks = weakref.WeakValueDictionary()
        self._global_over = asyncio.Event()
        self._global_over.set()
        self.proxy = proxy
        self.proxy_auth = proxy_auth
        self.use_clock = not unsync_clock
        self.api_version = api_version
        self.api_error_locale = str(api_error_locale)
        Route.BASE = f'https://discord.com/api/v{api_version}'
    
        user_agent = 'DiscordBot (https://github.com/mccoderpy/discord.py-message-components {0}) Python/{1[0]}.{1[1]} aiohttp/{2}'
        self.user_agent = user_agent.format(__version__, sys.version_info, aiohttp.__version__)
    
    def start(self):
        self.__session = aiohttp.ClientSession(connector=self.connector)
    
    def recreate(self):
        if self.__session.closed:
            self.__session = aiohttp.ClientSession(connector=self.connector)

    async def request(
            self,
            route: Route,
            *,
            content_type: Optional[str] = None,
            authorization: Optional[str] = None,
            **kwargs
    ) -> Any:
        bucket = route.bucket
        method = route.method
        url = route.url
    
        lock = self._locks.get(bucket)
        if lock is None:
            lock = asyncio.Lock()
            if bucket is not None:
                self._locks[bucket] = lock
    
        # header creation
        headers = {
            'User-Agent': self.user_agent,
            'X-Discord-Locale': self.api_error_locale
        }
        
        if content_type:
            headers['Content-Type'] = content_type
        if authorization:
            headers['Authorization'] = authorization
        
        # some checking if it's a JSON request
        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = to_json(kwargs.pop('json'))
    
        kwargs['headers'] = headers
    
        # Proxy support
        if self.proxy is not None:
            kwargs['proxy'] = self.proxy
        if self.proxy_auth is not None:
            kwargs['proxy_auth'] = self.proxy_auth
    
        if not self._global_over.is_set():
            # wait until the global lock is complete
            await self._global_over.wait()
    
        await lock.acquire()
        with MaybeUnlock(lock) as maybe_lock:
            for tries in range(5):
                try:
                    async with self.__session.request(method, url, **kwargs) as r:
                        _log.debug('%s %s with %s has returned %s', method, url, kwargs.get('data'), r.status)
                    
                        # even errors have text involved in them so this is safe to call
                        data = await json_or_text(r)
                    
                        # check if we have rate limit header information
                        remaining = r.headers.get('X-Ratelimit-Remaining')
                        if remaining == '0' and r.status != 429:
                            # we've depleted our current bucket
                            delta = _parse_ratelimit_header(r, use_clock=self.use_clock)
                            _log.debug('A rate limit bucket has been exhausted (bucket: %s, retry: %s).', bucket, delta)
                            maybe_lock.defer()
                            self.loop.call_later(delta, lock.release)
                    
                        # the request was successful so just return the text/json
                        if 300 > r.status >= 200:
                            _log.debug('%s %s has received %s', method, url, data)
                            return data
                    
                        # we are being rate limited
                        if r.status == 429:
                            if not r.headers.get('Via'):
                                # Banned by Cloudflare more than likely.
                                raise HTTPException(r, data)
                        
                            fmt = 'We are being rate limited. Retrying in %.2f seconds. Handled under the bucket "%s"'
                        
                            # sleep a bit
                            retry_after = data['retry_after']
                            _log.warning(fmt, retry_after, bucket)
                        
                            # check if it's a global rate limit
                            is_global = data.get('global', False)
                            if is_global:
                                _log.warning('Global rate limit has been hit. Retrying in %.2f seconds.', retry_after)
                                self._global_over.clear()
                        
                            await asyncio.sleep(retry_after)
                            _log.debug('Done sleeping for the rate limit. Retrying...')
                        
                            # release the global lock now that the
                            # global rate limit has passed
                            if is_global:
                                self._global_over.set()
                                _log.debug('Global rate limit is now over.')
                        
                            continue
                    
                        # we've received a 500 or 502, unconditional retry
                        if r.status in {500, 502}:
                            await asyncio.sleep(1 + tries * 2)
                            continue
                    
                        # the usual error cases
                        if r.status == 401:
                            raise Unauthorized(r, data)
                        elif r.status == 403:
                            raise Forbidden(r, data)
                        elif r.status == 404:
                            raise NotFound(r, data)
                        elif r.status == 503:
                            raise DiscordServerError(r, data)
                        else:
                            raise HTTPException(r, data)
            
                # This is handling exceptions from the request
                except OSError as e:
                    # Connection reset by peer
                    if tries < 4 and e.errno in (54, 10054):
                        continue
                    raise
        
            # We've run out of retries, raise.
            if r.status >= 500:
                raise DiscordServerError(r, data)
        
            raise HTTPException(r, data)

    # state management
    async def close(self):
        if self.__session:
            await self.__session.close()
            await asyncio.sleep(0.025)  # wait for the connection to be released
    
    async def get_from_cdn(self, url: str) -> bytes:
        async with self.__session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            elif resp.status == 404:
                raise NotFound(resp, 'asset not found')
            elif resp.status == 403:
                raise Forbidden(resp, 'cannot retrieve asset')
            else:
                raise HTTPException(resp, 'failed to get asset')
    
    def exchange_authorization_token(
            self,
            code: str,
            redirect_uri: str
    ) -> Response[types.AccessToken]:
        r = Route('POST', '/oauth2/token')
        data = {
            'client_id': self.client_id,
            'client_secret': self.__client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }
        return self.request(
            r,
            data=data,
            content_type='application/x-www-form-urlencoded'
        )
    
    def exchange_client_credentials(self, scopes: List[SupportsStr]) -> Response[types.ClientCredentialsAccessToken]:
        r = Route('POST', '/oauth2/token')
        data = {
            'grant_type': 'client_credentials',
            'scope': ' '.join(str(s) for s in scopes)
        }
        return self.request(
            r,
            data=data,
            content_type='application/x-www-form-urlencoded',
            auth=aiohttp.BasicAuth(self.client_id, self.__client_secret)
        )
    
    def exchange_refresh_token(self, refresh_token: str) -> Response[types.AccessToken]:
        r = Route('POST', '/oauth2/token')
        data = {
            'client_id': self.client_id,
            'client_secret': self.__client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        return self.request(
            r,
            data=data,
            content_type='application/x-www-form-urlencoded'
        )
    
    def revoke_access_token(self, access_token: SupportsStr) -> Response[NoReturn]:
        r = Route('POST', '/oauth2/token/revoke')
        params = {
            'token': str(access_token),
            'token_type_hint': 'access_token'
        }
        return self.request(
            r,
            params=params,
            authorization=f'Basic {self.__client_secret}',
            content_type='application/x-www-form-urlencoded'
        )
    
    def get_current_auth_info(self, access_token: SupportsStr) -> Coroutine[types.CurrentAuthorizationInfo]:
        r = Route('GET', '/oauth2/@me')
        return self.request(r, authorization=f'Bearer {access_token}')
    
    def get_user(self, access_token: SupportsStr) -> Response[types.User]:
        r = Route('GET', '/users/@me')
        return self.request(r, authorization=f'Bearer {access_token}')
        
    def get_user_guilds(
            self,
            access_token: SupportsStr,
            *,
            before: Optional[SupportsStr] = MISSING,
            after: Optional[SupportsStr] = MISSING,
            limit: Optional[int] = MISSING
    ) -> Response[List[guild.PartialGuild]]:
        r = Route('GET', '/users/@me/guilds')
        
        params = {}
        if before is not MISSING:
            params['before'] = str(before)
        if after is not MISSING:
            params['after'] = str(after)
        if limit is not MISSING:
            params['limit'] = limit
        
        return self.request(r, authorization=f'Bearer {access_token}', params=params)
    
    def get_user_guild_member(self, access_token: SupportsStr, guild_id: SupportsStr) -> Response[user.Member]:
        r = Route('GET', '/users/@me/guilds/{guild_id}/member', guild_id=guild_id)
        return self.request(r, authorization=f'Bearer {access_token}')
    
    def add_guild_member(
            self,
            access_token: SupportsStr,
            bot_token: SupportsStr,
            *,
            guild_id: SupportsStr,
            user_id: SupportsStr,
            nick: Optional[SupportsStr] = MISSING,
            roles: Optional[List[SupportsStr]] = MISSING,
            mute: Optional[bool] = MISSING,
            deaf: Optional[bool] = MISSING
    ) -> Response[Union[user.Member, NoReturn]]:
        r = Route('PUT', '/guilds/{guild_id}/members/{user_id}', guild_id=guild_id, user_id=user_id)
        data = {
            'access_token': str(access_token),
        }
        if nick is not MISSING:
            data['nick'] = str(nick)
        if roles is not MISSING:
            data['roles'] = [str(r) for r in roles]
        if mute is not MISSING:
            data['mute'] = mute
        if deaf is not MISSING:
            data['deaf'] = deaf
        
        return self.request(r, authorization=f'Bot {bot_token}', json=data)
    
    def get_user_connections(self, access_token: SupportsStr) -> Response[List[types.Connection]]:
        r = Route('GET', '/users/@me/connections')
        return self.request(r, authorization=f'Bearer {access_token}')
    
    def get_user_application_role_connection(
            self,
            access_token: SupportsStr,
            *,
            application_id: Optional[SupportsStr] = None
    ) -> Response[types.RoleConnection]:
        r = Route('GET', '/users/@me/applications/{application_id}/role-connection', application_id=application_id or self.client_id)
        return self.request(r, authorization=f'Bearer {access_token}')
    
    def update_user_application_role_connection(
            self,
            access_token: SupportsStr, *,
            data: types.RoleConnection,
            application_id: Optional[SupportsStr] = None
    ) -> Response[types.RoleConnection]:
        r = Route('PUT', '/users/@me/applications/{application_id}/role-connection', application_id=application_id or self.client_id)
        return self.request(r, authorization=f'Bearer {access_token}', json=data)
    
    def get_all_application_command_permissions(
            self,
            access_token: SupportsStr, *,
            guild_id: SupportsStr,
            application_id: Optional[SupportsStr] = None
    ) -> Response[List[app_command.GuildApplicationCommandPermissions]]:
        r = Route(
            'GET',
            '/applications/{application_id}/guilds/{guild_id}/commands/permissions',
            application_id=application_id or self.client_id,
            guild_id=guild_id
        )
        return self.request(r, authorization=f'Bearer {access_token}')
    
    def get_application_command_permissions(
            self,
            access_token: SupportsStr, *,
            guild_id: SupportsStr,
            command_id: SupportsStr,
            application_id: Optional[SupportsStr] = None
    ) -> Response[app_command.GuildApplicationCommandPermissions]:
        r = Route(
            'GET',
            '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
            application_id=application_id or self.client_id,
            guild_id=guild_id,
            command_id=command_id
        )
        return self.request(r, authorization=f'Bearer {access_token}')
    
    def update_application_command_permissions(
            self,
            access_token: SupportsStr, *,
            application_id: SupportsStr,
            guild_id: SupportsStr,
            command_id: SupportsStr,
            permissions: List[app_command.ApplicationCommandPermission]
    ) -> Response[app_command.GuildApplicationCommandPermissions]:
        r = Route(
            'PUT',
            '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
            application_id=application_id or self.client_id,
            guild_id=guild_id,
            command_id=command_id
        )
        data = {
            'permissions': permissions
        }
        return self.request(r, authorization=f'Bearer {access_token}', json=data)
