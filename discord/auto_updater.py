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

import asyncio
import aiohttp

import logging

from typing import (
    TYPE_CHECKING,
    Optional,
    Union,
    Dict,
    List,
    Any

)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .client import Client

__all__ = ('AutoUpdateChecker',)


class  AutoUpdateChecker:
    """This internal class handels automatic request to the library api to check for updates."""
    def __init__(self, client: Client) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.client = client
        self.dispatch = client.dispatch

    async def check_task(self) -> None:
        logger.debug('Started auto update checker task')
        while self.loop.is_running():
            await self.run_check()
            await asyncio.sleep(600)

    async def run_check(self) -> None:
        logger.debug('Checking for updates')
        pass
