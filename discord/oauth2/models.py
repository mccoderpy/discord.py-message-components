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
    TYPE_CHECKING,
    TypeVar
)
from typing_extensions import (
    Self
)

from ..types.oauth2.models import *

from ..utils import (
    utcnow
)

from .scopes import OAuth2Scope

from datetime import (
    datetime,
    timedelta,
    timezone
)

if TYPE_CHECKING:
    from .client import OAuth2Client
    
T = TypeVar('T')

__all__ = (
    'AccessToken'
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
    
    This can be also used to store additional data that can be accessed through get item.
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
    
    def __str__(self) -> str:
        return self._access_token
    
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
        return self.refresh_token
    
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
        self.client = client
        return self
    
    @classmethod
    def from_raw_data(cls, client: OAuth2Client, data: AccessTokenData) -> AccessToken:
        expires_at = convert_to_datetime(data.pop('expires_in'), from_delta=True)
        return cls.with_client(client, expires_at=expires_at, **data)
        
    async def refresh(self, *, force: bool = False) -> Self:
        """|coro|
        
        Refreshes the access token and returns the new one.
        If the token is still valid it will instantly return it unless ``force`` is set.
        This also updates the :attr:`expires_at` and :attr:`refresh_token`.
        
        .. note::
            This is only available when :attr:`.client` is set
        
        Parameters
        ----------
        force: :class:`bool`
            Whether to force-refresh the access token, even when :meth:`.is_expired` returns :obj:`False`
        
        Raises
        ------
        AttributeError:
            The client attribute is not set
        
        Returns
        -------
        :class:`str`:
            The new access token
        """
        if not self.is_expired() and not force:
            return self.access_token
        
        client = self.client
        if not client:
            raise AttributeError('client attribute is not set so you can\'t call this from the access token directly')
        return self._client.refresh_access_token(self)
        