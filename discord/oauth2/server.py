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
import logging
import signal
import sys
from typing import (
    Iterable,
    List,
    Optional,
    TYPE_CHECKING,
    Union
)
from urllib.parse import quote as _uriquote
from uuid import uuid4

import aiohttp.web as web

from .client import AccessTokenStore, OAuth2Client

if TYPE_CHECKING:
    from .enums import OAuth2Scope
    from .models import (
        AccessToken,
    )

__all__ = (
    'BasicOAuth2Server',
)

_log = logging.getLogger(__name__)


def _cancel_tasks(loop):
    try:
        task_retriever = asyncio.Task.all_tasks
    except AttributeError:
        # future proofing for 3.9 I guess
        task_retriever = asyncio.all_tasks

    tasks = {t for t in task_retriever(loop=loop) if not t.done()}

    if not tasks:
        return

    _log.info('Cleaning up after %d tasks.', len(tasks))
    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    _log.info('All tasks finished cancelling.')

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'Unhandled exception during OAuth2Client.run shutdown.',
                'exception': task.exception(),
                'task': task
            })


def _cleanup_loop(loop):
    try:
        _cancel_tasks(loop)
        if sys.version_info >= (3, 6):
            loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        _log.info('Closing the event loop.')
        loop.close()


class BasicOAuth2Server(web.Application):
    """
    A basic server for handling OAuth2 authorization.
    
    This has the following endpoints by default:
    
    - ``/authorize`` - The authorization endpoint. Will redirect to the Discord OAuth2 page with the given scopes.
    - ``/callback`` - The callback endpoint  (redirect_uri). Will exchange the code returned by discord for an access token.
    
    You can add your own endpoints by using the :meth:`~aiohttp.web.Application.add_routes` method.
    
    .. note::
        
        You don't need to use this, you can use any web framework you want.
    
    Example
    -------
    
    .. code-block:: python3
    
        import json
        import aiofiles
        import discord.oauth2 as oauth2
        
        
        class MyAccessTokenStore(oauth2.AccessTokenStore):
            ...
        
        
        server = MyOAuth2Server(
            CLIENT_ID,
            CLIENT_SECRET,
            access_token_store=MyAccessTokenStore(),
            scopes=[
                OAuth2Scope.IDENTIFY,
                OAuth2Scope.ACCESS_EMAIL,
                OAuth2Scope.ACCESS_GUILDS,
                OAuth2Scope.CONNECTIONS,
                OAuth2Scope.READ_GUILDS_MEMBERS,
                OAuth2Scope.WRITE_ROLE_CONNECTIONS
            ],
            redirect_uri="https://auth.example.com/discord-oauth2/callback",
            base_path='/discord-oauth2'
        )
        
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain('cert.pem', 'key.pem')
        
        server.run(host='auth.example.com', port=443, ssl_context=ssl_context, ...)
        
    
    """
    def __init__(
        self,
        client_id: int,
        client_secret: str,
        access_token_store: Optional[AccessTokenStore] = AccessTokenStore(),
        *,
        scopes: List[OAuth2Scope] = ['identify'],
        redirect_uri: str,
        state_required: bool = True,
        base_path: str = '',
        **kwargs
    ):
        """
        A basic server for handling OAuth2 authorization.
        

        Parameters
        ----------
        client_id: :class:`int`
            The client ID of your application.
        client_secret: :class:`str`
            The client secret of your application.
        access_token_store: :class:`AccessTokenStore`
            The access token store to use.
        scopes: List[:class:`OAuth2Scope`]
            The scopes to request.
        redirect_uri: :class:`str`
            The redirect URI to use.
        state_required: :class:`bool`
            Whether the state parameter is required.
        base_path: :class:`str`
            The base path to use for the routes.
        **kwargs
            Keyword arguments to pass to :class:`~aiohttp.web.Application`.
        """
        super().__init__(**kwargs)
        self.client_id: int = client_id
        self.oauth2_client = OAuth2Client(
            client_id,
            client_secret,
            access_token_store
        )
        self.scopes: List[str] = [str(scope) for scope in scopes]
        self.redirect_uri = redirect_uri
        self.auth_url = f'https://discord.com/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri={_uriquote(redirect_uri)}&scope={"%20".join(self.scopes)}'
        self.state_required = state_required
        self.router.add_get(f'{base_path}/authorize', self.authorize)
        self.router.add_get(f'{base_path}/callback', self.callback)
        
        self._states: List[str] = []
    
    async def store_state(self, request: web.Request, state: str) -> None:
        """
        Stores the ``state`` created in :meth:`~BasicOAuth2Server.create_state`.
        
        By default, this will store the state in a list.
        
        Parameters
        ----------
        request: :class:`aiohttp.web.Request`
            The request that is being handled.
        state: :class:`str`
            The ``state`` to store.
        """
        self._states.append(state)
    
    async def create_state(self, request: web.Request) -> str:
        """
        Creates a ``state`` to use for the authorization endpoint and stores it using :meth:`~BasicOAuth2Server.store_state`.
        
        By default, this will return a random UUID4.
        
        Parameters
        ----------
        request: :class:`aiohttp.web.Request`
            The request that is being handled.
        
        Returns
        -------
        :class:`str`
            The ``state`` to use.
        """
        state = uuid4().hex
        await self.store_state(request, state)
        return state
    
    async def check_state(self, request: web.Request, state: str) -> bool:
        """
        Checks if the ``state`` is valid.
        
        By default, this will trys to remove the ``state`` from the list of stored states - if it succeeds, it is valid.
        
        Parameters
        ----------
        request: :class:`aiohttp.web.Request`
            The request that is being handled.
        state: :class:`str`
            The ``state`` to check.
        
        Returns
        -------
        :class:`bool`
            Whether the ``state`` is valid.
        """
        try:
            self._states.remove(state)
        except ValueError:
            return False
        else:
            return True
    
    async def authorize(self, request: web.Request) -> Union[web.HTTPFound, web.HTTPBadRequest]:
        """
        The authorization endpoint.
        
        By default, this will redirect to the Discord OAuth2 page with the :attr:`~BasicOAuth2Server.scopes` given.
        
        .. note::
            The ``state`` this redirects to Discord with is generated by :meth:`~BasicOAuth2Server.create_state`.
            However, you can override this method to change how the state is generated. By default, it is a random UUID4.
        
        Parameters
        ----------
        request: :class:`~aiohttp.web.Request`
            The request to the authorization endpoint.
        
        Returns
        -------
        Union[:class:`~aiohttp.web.HTTPFound`, :class:`~aiohttp.web.HTTPBadRequest`]
            The redirect to Discord, or a bad request if the ``state`` is invalid.
        """
        if self.state_required:
            state = await self.create_state(request)
            return web.HTTPFound(f'{self.auth_url}&state={state}')
        else:
            return web.HTTPFound(self.auth_url)
        
    async def callback(self, request: web.Request) -> web.Response:
        """
        The callback endpoint.
        
        By default, this will exchange the code returned by Discord for an access token.
        
        .. note::
            The ``state`` this checks using :meth:`~BasicOAuth2Server.check_state` is generated by :meth:`~BasicOAuth2Server.create_state`.
        
        When the user has successfully authorized,
        :meth:`~BasicOAuth2Server.successfully_authorized_response` is called, and it's return value is returned.
        
        Parameters
        ----------
        request: :class:`~aiohttp.web.Request`
            The request from discords redirect containing the code and if set the ``state``.
        
        Returns
        -------
        :class:`~aiohttp.web.Response`
            The response to send to the user.
        """
        try:
            code = request.query.get('code')
        except KeyError:
            return web.HTTPBadRequest()
        else:
            if self.state_required:
                try:
                    state = request.query.get('state')
                except KeyError:
                    return web.HTTPBadRequest(text='Missing state')
                else:
                    state_ok = await self.check_state(request, state)
                    if not state_ok:
                        return web.HTTPBadRequest(text='State mismatch')
            access_token = await self.oauth2_client.authorize(code, self.redirect_uri)
            return await self.successfully_authorized_response(request, access_token)
    
    async def successfully_authorized_response(self, request: web.Request, access_token: AccessToken) -> web.Response:
        """|coro|
        The response to send when the user has successfully authorized.
        
        Parameters
        ----------
        request: :class:`~aiohttp.web.Request`
            The request to the callback endpoint.
        access_token: :class:`AccessToken`
            The access token.
        
        Returns
        -------
        :class:`~aiohttp.web.Response`
            The response to send to the user.
        """
        if 'identify' in access_token.scopes:
            user = await access_token.fetch_user()
        else:
            user = None
        template = """
        <!DOCTYPE html>
        <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="color-scheme" content="light dark">
        <title>Successfully authorized!</title>
        <style>
            .dark-mode {
                background-color: #36393f;
                color: white;
            }

            .light-mode {
                background-color: white;
                color: black;
            }

            @media (prefers-color-scheme: dark) {
                body {
                    background-color: #36393f;
                    color: white;
                }
            }
        </style>
    </head>
    <body style="background-color: #36393f; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: white; text-align: center;">
        <h1>Successfully authorized{{ user }}!</h1>
        <p>You can now close this page</p>
    </body>
</html>
"""
        return web.HTTPOk(text=template.replace('{{ user }}', f' as {str(user)}' if user else ''), content_type='text/html')
    
    def run(
        self,
        *,
        host: Union[str, Iterable[str]],
        port: Optional[int] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        **kwargs
    ):
        """
        Runs the server.
        
        .. important::
        
            This method is blocking. If you want to run it in a non-blocking way - for example from a bot - use :meth:`run_async` instead.
        
        Parameters
        ----------
        host: Union[:class:`str`, Iterable[:class:`str`]]
            The host to run the server on.
        port: Optional[:class:`int`]
            The port to run the server on.
        loop: Optional[:class:`~asyncio.AbstractEventLoop`]
            The event loop to use.
        **kwargs
            Keyword arguments to pass to :meth:`aiohttp.web.run_app`.
        """
        if not loop:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
    
        try:
            loop.add_signal_handler(signal.SIGINT, lambda: loop.stop())
            loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
        except NotImplementedError:
            pass
    
        async def runner():
            try:
                await self.oauth2_client.start()
                await web._run_app(self, host=host, port=port, **kwargs)
            finally:
                await self.oauth2_client.close()
    
        def stop_loop_on_completion(_):
            loop.stop()
    
        future = asyncio.ensure_future(runner(), loop=loop)
        future.add_done_callback(stop_loop_on_completion)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            _log.info('Received signal to close the event loop.')
        finally:
            future.remove_done_callback(stop_loop_on_completion)
            _log.info('Cleaning up tasks.')
            _cleanup_loop(loop)
    
        if not future.cancelled():
            try:
                return future.result()
            except KeyboardInterrupt:
                # I am unsure why this gets raised here but suppress it anyway
                return None
        