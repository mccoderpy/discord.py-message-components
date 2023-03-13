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
    List,
    NamedTuple
)
from typing_extensions import Literal


from . import utils
from .user import User
from .asset import Asset
from .team import Team
from .flags import ApplicationFlags

if TYPE_CHECKING:
    from .state import ConnectionState
    from .guild import Guild
    from .types.appinfo import AppInfo as AppInfoPayload

__all__ = (
    'InstallParams',
    'AppInfo',
)


class InstallParams(NamedTuple):
    """Represents the default install-parameters for an application.

    Attributes
    -------------
    scopes: List[:class:`str`]
        The scopes to add the application to the server with
    permissions: :class:`str`
        The permissions to request for the bot role
    """
    scopes: List[str]
    permissions: str


class AppInfo:
    """Represents the application info for the bot provided by Discord.


    Attributes
    -------------
    id: :class:`int`
        The application ID.
    name: :class:`str`
        The application name.
    owner: :class:`User`
        The application owner.
    team: Optional[:class:`Team`]
        The application's team.

        .. versionadded:: 1.3

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
    rpc_origins: Optional[List[:class:`str`]]
        A list of RPC origin URLs, if RPC is enabled.
    summary: :class:`str`
        If this application is a game sold on Discord,
        this field will be the summary field for the store page of its primary SKU.
        
        Deprecated: This field is deprecated and will be removed in API v11
        
        .. versionadded:: 1.3
        .. deprecated:: 2.0

    verify_key: :class:`str`
        The hex encoded key for verification in interactions and the
        GameSDK's `GetTicket <https://discord.com/developers/docs/game-sdk/applications#getticket>`_.

        .. versionadded:: 1.3

    guild_id: Optional[:class:`int`]
        If this application is a game sold on Discord,
        this field will be the guild to which it has been linked to.

        .. versionadded:: 1.3

    primary_sku_id: Optional[:class:`int`]
        If this application is a game sold on Discord,
        this field will be the id of the "Game SKU" that is created,
        if it exists.

        .. versionadded:: 1.3

    slug: Optional[:class:`str`]
        If this application is a game sold on Discord,
        this field will be the URL slug that links to the store page.

        .. versionadded:: 1.3

    cover_image: Optional[:class:`str`]
        If this application is a game sold on Discord,
        this field will be the hash of the image on store embeds

        .. versionadded:: 1.3

    custom_install_url: Optional[:class:`str`]
        The default invite-url for the bot if its set.
    
    install_params: Optional[:class:`InstallParams`]
        The settings for the application's default in-app authorization link, if enabled.
    
    privacy_policy_url: Optional[:class:`str`]
        The link to this application's Privacy Policy if set.

    terms_of_service_url: Optional[:class:`str`]
        The link to this application's Terms of Service if set.

    interactions_endpoint_url: Optional[:class:`str`]
        The endpoint that will receive interactions with this app if its set.
    """

    __slots__ = ('_state', 'description', 'id', 'name', 'rpc_origins',
                 'bot_public', 'bot_require_code_grant', 'owner', 'icon',
                 'summary', 'verify_key', 'team', 'guild_id', 'primary_sku_id',
                 'slug', 'custom_install_url', 'tags', '_flags', 'cover_image',
                 'privacy_policy_url', 'terms_of_service_url', 'install_params',
                 'interactions_endpoint_url')

    def __init__(self, *, state: ConnectionState, data: AppInfoPayload):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.icon: str = data['icon']
        self.rpc_origins: Optional[List[str]] = data['rpc_origins']
        self.bot_public: bool = data['bot_public']
        self.bot_require_code_grant: bool = data['bot_require_code_grant']
        self.custom_install_url: Optional[str] = data.get('custom_install_url', None)
        install_params = data.get('install_params', None)
        
        self.install_params: Optional[InstallParams] = InstallParams(install_params['scopes'], install_params['permissions']) if install_params else None
        
        self.tags: List[str] = data.get('tags', [])
        self._flags: int = data.get('flags', 0)
        self.owner: User = User(state=self._state, data=data['owner'])

        team = data.get('team')
        self.team: Optional[Team] = Team(state, team) if team else None

        self.summary = ''  # Deprecated - Will be removed in API v11
        self.verify_key: str = data['verify_key']

        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')

        self.primary_sku_id: Optional[int] = utils._get_as_snowflake(data, 'primary_sku_id')
        self.slug: Optional[str] = data.get('slug')
        self.cover_image: Optional[str] = data.get('cover_image')
        self.privacy_policy_url: Optional[str] = data.get('privacy_policy_url', None)
        self.terms_of_service_url: Optional[str] = data.get('terms_of_service_url', None)
        self.interactions_endpoint_url: Optional[str] = data.get('interactions_endpoint_url', None)

    def __repr__(self):
        return '<{0.__class__.__name__} id={0.id} name={0.name!r} description={0.description!r} public={0.bot_public} ' \
               'owner={0.owner!r}>'.format(self)

    @property
    def icon_url(self) -> Asset:
        """:class:`.Asset`: Retrieves the application's icon asset.

        This is equivalent to calling :meth:`icon_url_as` with
        the default parameters ('webp' format and a size of 1024).

        .. versionadded:: 1.3
        """
        return self.icon_url_as()

    def icon_url_as(
            self,
            *,
            format: Literal['png', 'jpeg', 'jpg', 'webp'] = 'webp',
            size=1024
    ) -> Asset:
        """Returns an :class:`Asset` for the icon the application has.

        The format must be one of 'webp', 'jpeg', 'jpg' or 'png'.
        The size must be a power of 2 between 16 and 4096.

        .. versionadded:: 1.6

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
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_icon(self._state, self, 'app', format=format, size=size)

    @property
    def cover_image_url(self) -> Asset:
        """:class:`.Asset`: Retrieves the cover image on a store embed.

        This is equivalent to calling :meth:`cover_image_url_as` with
        the default parameters ('webp' format and a size of 1024).

        .. versionadded:: 1.3
        """
        return self.cover_image_url_as()

    def cover_image_url_as(self, *, format='webp', size=1024) -> Asset:
        """Returns an :class:`Asset` for the image on store embeds
        if this application is a game sold on Discord.

        The format must be one of 'webp', 'jpeg', 'jpg' or 'png'.
        The size must be a power of 2 between 16 and 4096.

        .. versionadded:: 1.6

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the image to. Defaults to 'webp'.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_cover_image(self._state, self, format=format, size=size)

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: If this application is a game sold on Discord,
        this field will be the guild to which it has been linked

        .. versionadded:: 1.3
        """
        return self._state._get_guild(int(self.guild_id))

    @property
    def flags(self) -> ApplicationFlags:
        return ApplicationFlags._from_value(self._flags)

