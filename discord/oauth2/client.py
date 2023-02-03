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

from typing import (
    Callable,
    Union
)

from .models import *


class OAuth2Client:
    def __init__(self, client_id: int, client_secret: Union[str, Callable[[], str]]):
        self.client_id: int = client_id
        self.__client_secret = lambda: client_secret if isinstance(client_secret, str) else client_secret
        self.access_tokens: Dict[int, AccessToken] = {}
    

    async def load_access_tokens(self) -> Dict[int, AccessToken]:
        return {}
    
    async def store_access_tokens(self) -> None:
        pass
    
    async def load_access_token(self, user_id: int, /) -> AccessToken:
        pass
    
    async def store_access_token(self) -> None:
        pass
    
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
        ...
