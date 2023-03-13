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

from ..enums import Enum

__all__ = (
    'OAuth2Scope',
    'GrantType',
    'ConnectionService',
)


class OAuth2Scope(Enum):
    """
    These are all the OAuth2 scopes that Discord supports.
    Some scopes require approval from Discord to use.
    Requesting them from a user without approval from Discord may cause errors or undocumented behavior in the OAuth2 flow.
    
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | Attribute                                               | Name                                     | Description                                                                                                        |
    +=========================================================+==========================================+====================================================================================================================+
    | .. attribute:: READ_ACTIVITIES                          | activities.read                          | allows your app to fetch data from a user's "Now Playing/Recently Played" list                                     |
    |                                                         |                                          | - **requires Discord approval**                                                                                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: WRITE_ACTIVITIES                         | activities.write                         | allows your app to update a user's activity                                                                        |
    |                                                         |                                          | - **requires Discord approval** (NOT REQUIRED FOR GAMESDK ACTIVITY MANAGER)                                        |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: READ_APPLICATIONS_BUILDS                 | applications.builds.read                 | allows your app to read build data for a user's applications                                                       |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: UPLOAD_APPLICATIONS_BUILDS               | applications.builds.upload               | allows your app to upload/update builds for a user's applications                                                  |
    |                                                         |                                          | - **requires Discord approval**                                                                                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: APPLICATIONS_COMMANDS                    | applications.commands                    | allows your app to use application-commands in a guild                                                             |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: UPDATE_APPLICATIONS_COMMANDS             | applications.commands.update             | allows your app to update its application-commands using a Bearer token - client credentials grant only            |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: UPDATE_APPLICATIONS_COMMANDS_PERMISSIONS | applications.commands.permissions.update | allows your app to update permissions for its commands in a guild a user has permissions to                        |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: APPLICATIONS_ENTITLEMENTS                | applications.entitlements                | allows your app to read entitlements for a user's applications                                                     |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: UPDATE_APPLICATIONS_STORE                | applications.store.update                | allows your app to read and update store data (SKUs, store listings, achievements, etc.) for a user's applications |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: BOT                                      | bot                                      | for oauth2 bots, this puts the bot in the user's selected guild by default                                         |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: CONNECTIONS                              | connections                              | allows ``/users/@me/connections`` to return linked third-party accounts                                            |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: READ_DM_CHANNELS                         | dm_channels.read                         | allows your app to see information about the user's DMs and group DMs                                              |
    |                                                         |                                          | - **requires Discord approval**                                                                                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: ACCESS_EMAIL                             | email                                    | enables ``/users/@me`` to return an ``email``                                                                      |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: JOIN_GROUPS                              | gdm.join                                 | allows your app to join users to a group dm                                                                        |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: ACCESS_GUILDS                            | guilds                                   | allows ``/users/@me/guilds`` to return basic information about all of a user's guilds                              |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: JOIN_GUILDS                              | guilds.join                              | allows ``/guilds/{guild.id}/members/{user.id}`` to be used for joining users to a guild                            |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: READ_GUILDS_MEMBERS                      | guilds.members.read                      | allows ``/users/@me/guilds/{guild.id}/member`` to return a user's member information in a guild                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: IDENTIFY                                 | identify                                 | allows ``/users/@me`` without ``email``                                                                            |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: READ_MESSAGES                            | messages.read                            | for local rpc server api access, this allows you to read messages from all client channels                         |
    |                                                         |                                          | (otherwise restricted to channels/guilds your app creates)                                                         |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: READ_RELATIONSHIPS                       | relationships.read                       | allows your app to know a user's friends and implicit relationships                                                |
    |                                                         |                                          | - **requires Discord approval**                                                                                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: WRITE_ROLE_CONNECTIONS                   | role_connections.write                   | allows your app to update a user's connection and metadata for the app                                             |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: ACCESS_RPC                               | rpc                                      | for local rpc server access, this allows you to control a user's local Discord client                              |
    |                                                         |                                          | - **requires Discord approval**                                                                                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: RPC_WRITE_ACTIVITIES                     | rpc.activities.write                     | for local rpc server access, this allows you to update a user's activity                                           |
    |                                                         |                                          | - **requires Discord approval**                                                                                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: RPC_READ_NOTIFICATIONS                   | rpc.notifications.read                   | for local rpc server access, this allows you to receive notifications pushed out to the user                       |
    |                                                         |                                          | - **requires Discord approval**                                                                                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: RPC_READ_VOICE                           | rpc.voice.read                           | for local rpc server access, this allows you to read a user's voice settings and listen for voice events           |
    |                                                         |                                          | - **requires Discord approval**                                                                                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: RPC_WRITE_VOICE                          | rpc.voice.write                          | for local rpc server access, this allows you to update a user's voice settings                                     |
    |                                                         |                                          | - **requires Discord approval**                                                                                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: VOICE                                    | voice                                    | allows your app to connect to voice on user's behalf and see all the voice members                                 |
    |                                                         |                                          | - **requires Discord approval**                                                                                    |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    | .. attribute:: CREATE_WEBHOOK                           | webhook.incoming                         | this generates a webhook that is returned in the oauth token response for authorization code grants                |
    +---------------------------------------------------------+------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
    
    .. important::
    
        :attr:`JOIN_GUILDS` and :attr:`BOT` require you to have a bot account linked to your application.
        Also, in order to add a user to a guild, your bot has to already belong to that guild.
    """
    READ_ACTIVITIES                          = 'activities.read'
    WRITE_ACTIVITIES                         = 'activities.write'
    READ_APPLICATIONS_BUILDS                 = 'applications.builds.read'
    UPLOAD_APPLICATIONS_BUILDS               = 'applications.builds.upload'
    APPLICATIONS_COMMANDS                    = 'applications.commands'
    UPDATE_APPLICATIONS_COMMANDS             = 'applications.commands.update'
    UPDATE_APPLICATIONS_COMMANDS_PERMISSIONS = 'applications.commands.permissions.update'
    APPLICATIONS_ENTITLEMENTS                = 'applications.entitlements'
    UPDATE_APPLICATIONS_STORE                = 'applications.store.update'
    BOT                                      = 'bot'
    CONNECTIONS                              = 'connections'
    READ_DM_CHANNELS                         = 'dm_channels.read'
    ACCESS_EMAIL                             = 'email'
    JOIN_GROUPS                              = 'gdm.join'
    ACCESS_GUILDS                            = 'guilds'
    JOIN_GUILDS                              = 'guilds.join'
    READ_GUILDS_MEMBERS                      = 'guilds.members.read'
    IDENTIFY                                 = 'identify'
    READ_MESSAGES                            = 'messages.read'
    READ_RELATIONSHIPS                       = 'relationships.read'
    WRITE_ROLE_CONNECTIONS                   = 'role_connections.write'
    ACCESS_RPC                               = 'rpc'
    RPC_WRITE_ACTIVITIES                     = 'rpc.activities.write'
    RPC_READ_NOTIFICATIONS                   = 'rpc.notifications.read'
    RPC_READ_VOICE                           = 'rpc.voice.read'
    RPC_WRITE_VOICE                          = 'rpc.voice.write'
    VOICE                                    = 'voice'
    CREATE_WEBHOOK                           = 'webhook.incoming'
    
    def __str__(self) -> str:
        return self.value


class GrantType(Enum):
    AUTHORIZATION_CODE = 'authorization_code'
    CLIENT_CREDENTIALS = 'client_credentials'
    REFRESH_TOKEN      = 'refresh_token'


class ConnectionService(Enum):
    """Represents the service of a :class:`Connection`.
    
    .. container:: operations
    
        .. describe:: str(x)
    
            Returns the connection type's name.
    
    +----------------------------------+----------------------+
    | Name                             | Value                |
    +==================================+======================+
    | .. attribute:: Battlenet         | battlenet            |
    +----------------------------------+----------------------+
    | .. attribute:: Crunchyroll       | crunchyroll          |
    +----------------------------------+----------------------+
    | .. attribute:: eBay              | ebay                 |
    +----------------------------------+----------------------+
    | .. attribute:: Epic_Games        | epicgames            |
    +----------------------------------+----------------------+
    | .. attribute:: Facebook          | facebook             |
    +----------------------------------+----------------------+
    | .. attribute:: GitHub            | github               |
    +----------------------------------+----------------------+
    | .. attribute:: Instagram         | instagram            |
    +----------------------------------+----------------------+
    | .. attribute:: League_of_Legends | leagueoflegends      |
    +----------------------------------+----------------------+
    | .. attribute:: PayPal            | paypal               |
    +----------------------------------+----------------------+
    | .. attribute:: Playstation       | playstation          |
    +----------------------------------+----------------------+
    | .. attribute:: Reddit            | reddit               |
    +----------------------------------+----------------------+
    | .. attribute:: Riotgames         | riotgames            |
    +----------------------------------+----------------------+
    | .. attribute:: Skype             | skype                |
    +----------------------------------+----------------------+
    | .. attribute:: Spotify           | spotify              |
    +----------------------------------+----------------------+
    | .. attribute:: Steam             | steam                |
    +----------------------------------+----------------------+
    | .. attribute:: TikTok            | tiktok               |
    +----------------------------------+----------------------+
    | .. attribute:: Twitch            | twitch               |
    +----------------------------------+----------------------+
    | .. attribute:: Twitter           | twitter              |
    +----------------------------------+----------------------+
    | .. attribute:: xBox              | xbox                 |
    +----------------------------------+----------------------+
    | .. attribute:: YouTube           | youtube              |
    +----------------------------------+----------------------+
    """
    Battlenet   = 'battlenet'
    Crunchyroll = 'crunchyroll'
    eBay        = 'ebay'
    Epic_Games   = 'epicgames'
    Facebook    = 'facebook'
    GitHub      = 'github'
    Instagram   = 'instagram'
    League_of_Legends = 'leagueoflegends'
    PayPal      = 'paypal'
    Playstation = 'playstation'
    Reddit      = 'reddit'
    Riotgames   = 'riotgames'
    Skype       = 'skype'
    Spotify     = 'spotify'
    Steam       = 'steam'
    TikTok      = 'tiktok'
    Twitch      = 'twitch'
    Twitter     = 'twitter'
    xBox        = 'xbox'
    YouTube     = 'youtube'
    
    def __str__(self) -> str:
        return self.value
