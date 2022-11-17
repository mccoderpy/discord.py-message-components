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
    TYPE_CHECKING,
    Optional,
    Union,
    Dict,
    Any

)

import re
import sys
import copy
import json
import aiohttp
import logging
import asyncio
from collections import namedtuple

if sys.version_info <= (3, 7):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

from . import utils, __version__
from .errors import HTTPException


if TYPE_CHECKING:
    from .client import Client

MISSING = utils.MISSING

log = logging.getLogger(__name__)

__all__ = (
    'AutoUpdateChecker',
)


MinimalReleaseInfo = namedtuple('MinimalReleaseInfo', ('version', 'release', 'valid', 'use_instead'))
GitReleaseInfo = namedtuple('GitReleaseInfo', ('branch', 'version', 'release', 'commit', 'valid', 'use_instead'))
VERSION_REGEX = re.compile(r'\s*(\d+\.\d+(?:\.\d+)*(?:[-_.]?(?:alpha|beta|pre|preview|a|b|c|rc)(?:[-_.]?[0-9]+)?)?)(?:\+g([0-9a-f]{7,10}))?\s*')


class AutoUpdateChecker:
    """This internal class handels automatic request to the library api to check for updates."""
    def __init__(self, client: Client) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.client = client
        self.dispatch = client.dispatch
        self.task: Optional[asyncio.Task] = None  # Will be set by the Client instance
        self.__session: Optional[aiohttp.ClientSession] = None  # set this later in check_task
        self._vcs_url: Optional[str] = None
        self.current_release: Union[MinimalReleaseInfo, GitReleaseInfo, None] = None  # set this later in check_task
        self.__last_check_result: Dict[str, Any] = {}
        user_agent = 'DiscordBot (https://github.com/mccoderpy/discord.py-message-components {0}) Python/{1[0]}.{1[1]} aiohttp/{2}'
        self.user_agent = user_agent.format(__version__, sys.version_info, aiohttp.__version__)
        self.headers: Dict[str, str] = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json'
        }

    @property
    def last_check_result(self) -> Optional[Dict[str, Any]]:
        return self.__last_check_result

    @last_check_result.setter
    def last_check_result(self, value) -> None:
        raise NotImplementedError

    def get_session(self) -> aiohttp.ClientSession:
        if self.__session.closed:
            self.__session = aiohttp.ClientSession('https://api.discord4py.dev')
        return self.__session

    async def request(
            self,
            method: str,
            route: str,
            data: Optional[Dict[str, Any]] = None
    ) -> Any:
        from .http import json_or_text  # circular imports

        params = {}
        headers = self.headers.copy()

        if data is not None:
            params['data'] = json.dumps(data)
            headers['Content-Type'] = 'application/json'

        params['headers'] = headers

        for tries in range(5):
            async with self.get_session() as session:
                async with session.request(method, route, **params) as resp:
                    data = await json_or_text(resp)
                    if 400 > resp.status >= 200:
                        return data
                    elif resp.status >= 400:
                        log.warning('%s %s status was not 200. Was %d', method, route, resp.status)
                        error = HTTPException(resp, data)
                        log.error(*error.args)
                        await asyncio.sleep(5 + tries * 2)
                        continue

    async def get_current_release(self) -> Union[MinimalReleaseInfo, GitReleaseInfo]:
        dist = importlib_metadata.distribution('discord.py-message-components')
        version, release = VERSION_REGEX.match(dist.version).groups()
        if release:
            direct_url_file = dist.read_text('direct_url.json')
            if direct_url_file:
                direct_url = json.loads(direct_url_file)
                self._vcs_url = vcs_url = direct_url['url']
                url_is_valid = await self.validate_vcs_url(vcs_url)
                vcs_info = direct_url['vcs_info']
                branch = vcs_info.get('requested_revision', None)
                commit_id = vcs_info.get('commit_id', None)
                return GitReleaseInfo(branch, version, release, commit_id, url_is_valid, MISSING)
            else:
                info = await self.find_release(version, release)
                if info is not None:
                    return GitReleaseInfo(info['branch'], version, release, info['commit'], True, MISSING)
                else:
                    log.warning('Unknown release used. Version checks will not be performed')
        else:
            return MinimalReleaseInfo(version, release, True, MISSING)

    async def validate_vcs_url(self, url: str) -> bool:
        d = await self.request('POST', '/is-valid-vcs-url', data={'url': url})
        return d['valid']

    async def find_release(self, version: str, release: str) -> Optional[Dict[str, Any]]:
        pass

    async def check_task(self) -> None:
        log.debug('Starting auto update checker task')
        self.__session = aiohttp.ClientSession('https://api.discord4py.dev')
        self.current_release = current_release = await self.get_current_release()
        if current_release is not None:
            self.headers['Discord4py-Version'] = current_release.version
            self.headers['Discord4py-Release'] = current_release.release
            self.headers['Discord4py-Branch'] = getattr(current_release, 'branch', 'unknown')
        if current_release and current_release.valid:
            if type(current_release) is GitReleaseInfo:
                log.info(f'Running on version {current_release.version} ({current_release.release}) of branch {current_release.branch}')
            else:
                log.debug(f'Running on version {current_release.version}')
            while self.loop.is_running():
                await self.run_check()
                await asyncio.sleep(300)
        else:
            await self.__session.close()
            log.warning('Update checker task stopped')

    async def run_check(self) -> None:
        log.debug('Checking for updates')
        data = await self.request('GET', f'/branch/{self.current_release.branch}/releases/latest')
        if self.last_check_result == data:
            return  # Why should we overwrite it here when it is equal?
        self.__last_check_result = data

        if not data['active']:
            self.current_release.valid = False
            self.current_release.use_instead = use_instead = data.get("use_instead", None)

            log.warning(
                f'You are using a branch of the library that has been deleted and will no longer receive updates!'
                f'Consider updating to {use_instead + "branch instead" if use_instead else "an other branch"}.'
            )
            self.dispatch('used_branch_deleted', use_instead)
            log.info('Stopped update checker task')
            self.task.cancel()
        else:
            before = copy.copy(self.current_release)
            version, release = data['v'], data['r']
            if version != before.version or release != before.release:
                self.dispatch('update_available', before, GitReleaseInfo(before.branch, version, release, MISSING, True, MISSING))
                self.show_update_notice(
                    f'{self.current_release.version} ({self.current_release.release})',
                    f'{version} ({release})'
                )

    def show_update_notice(self, actual: str, latest: str) -> None:
        stream_supports_color = utils.stream_supports_colour(sys.stdout)
        if stream_supports_color:
            fmt = f'[\x1b[94;1mNOTICE\x1b[0m] New version for discord4py available: \x1b[31m{actual}\x1b[0m -> \x1b[32m{latest}\x1b[0m\n' \
                  f'[\x1b[94;1mNOTICE\x1b[0m] Update to the latest version using \x1b[92mpip install -U git+{self._vcs_url}@{self.current_release.branch}\x1b[0m'
        else:
            fmt = f'New version available: {actual} -> {latest}\n' \
                  f'Update to the latest version using "pip install -U git+{self._vcs_url}@{self.current_release.branch}"'
        print(fmt.format(actual=actual, latest=latest))

    def start(self):
        self.task = self.loop.create_task(self.check_task())
