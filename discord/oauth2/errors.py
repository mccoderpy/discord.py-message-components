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
from ..errors import DiscordException

__all__ = (
    'OAuth2Exception',
    'AccessTokenExpired',
    'AccessTokenNotRefreshable',
    'InvalidAccessToken',
    'InvalidRefreshToken',
    'InvalidAuthorizationCode',
    'UserIsAtGuildLimit'
)


class OAuth2Exception(DiscordException):
    """Base class for all OAuth2 errors."""
    pass


class AccessTokenExpired(OAuth2Exception):
    """Exception raised when an access token has expired."""
    def __init__(self, refreshable: bool = True):
        if refreshable:
            msg = 'This access token has expired and needs to be refreshed first.'
        else:
            msg = 'This access token has expired and the user must re-authorize the application.'
        self.refreshable = refreshable
        super().__init__(msg)


class AccessTokenNotRefreshable(OAuth2Exception):
    """Exception raised when a token is not refreshable."""
    def __init__(self):
        super().__init__('This token is not refreshable as it is missing a refresh_token')


class InvalidAccessToken(OAuth2Exception):
    """Exception raised when an invalid access token is used."""
    def __init__(self):
        super().__init__('The access token is invalid or has expired.')


class InvalidRefreshToken(OAuth2Exception):
    """Exception raised when an invalid refresh token is used."""
    def __init__(self):
        super().__init__('The refresh token is invalid or has expired.')


class InvalidAuthorizationCode(OAuth2Exception):
    """Exception raised when an invalid authorization code is used."""
    def __init__(self):
        super().__init__('The authorization code is invalid or has expired.')


class UserIsAtGuildLimit(OAuth2Exception):
    """Exception raised when the user is at the guild limit."""
    def __init__(self):
        super().__init__('This user can\'t be added to the guild as they are at the 100 (200 with nitro) server limit.')
