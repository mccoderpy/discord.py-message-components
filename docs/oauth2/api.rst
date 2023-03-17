:og:title: discord4py OAuth2 API Reference
:og:description: This section outlines the OAuth2 API of discord4py

.. meta::
    :description: This section outlines the OAuth2 API of discord4py

.. currentmodule:: discord.oauth2


OAuth2 API Reference
====================

.. _client:

The following section outlines the OAuth2 API of discord4py

OAuth2 Client
~~~~~~~~~~~~~

.. attributetable:: OAuth2Client

.. autoclass:: OAuth2Client()
    :members:

Access Token Store
~~~~~~~~~~~~~~~~~~

.. attributetable:: AccessTokenStore

.. autoclass:: AccessTokenStore()
    :members:

.. _models:

Models
------

Access Token
~~~~~~~~~~~~

.. attributetable:: AccessToken

.. autoclass:: AccessToken()
    :members:

Access Token Info
~~~~~~~~~~~~~~~~~

.. attributetable:: AccessTokenInfo

.. autoclass:: AccessTokenInfo()
    :members:

.. autoclass:: PartialAppInfo()
    :members:

Connection
~~~~~~~~~~

.. attributetable:: Connection

.. autoclass:: Connection()
    :members:

Role Connection
~~~~~~~~~~~~~~~

.. attributetable:: RoleConnection

.. autoclass:: RoleConnection()
    :members:

Partial Guild
~~~~~~~~~~~~~

.. attributetable:: PartialGuild

.. autoclass:: PartialGuild()
    :members:
    :inherited-members:

Guild Member
~~~~~~~~~~~~

.. attributetable:: GuildMember

.. autoclass:: GuildMember
    :members:
    :inherited-members:

Partial Guild Integration
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialGuildIntegration

.. autoclass:: PartialGuildIntegration()
    :members:
    :inherited-members:

User
~~~~

.. autoclass:: User()
    :members:
    :inherited-members:

Partial User
~~~~~~~~~~~~

.. attributetable:: PartialUser

.. autoclass:: PartialUser()
    :members:
    :inherited-members:

.. _enumerations:

Enumerations
------------

.. autoclass:: OAuth2Scope()

.. autoclass:: ConnectionService()

Exceptions
----------
The following exceptions are thrown by the oauth2 sub-package

.. _exceptions:

.. autoexception:: OAuth2Exception

.. autoexception:: AccessTokenExpired
    :members:

.. autoexception:: AccessTokenNotRefreshable

.. autoexception:: InvalidAccessToken

.. autoexception:: InvalidRefreshToken

.. autoexception:: InvalidAuthorizationCode

.. autoexception:: UserIsAtGuildLimit

Exception Hierarchy
~~~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`discord.DiscordException`
        - :exc:`OAuth2Exception`
            - :exc:`AccessTokenExpired`
            - :exc:`AccessTokenNotRefreshable`
            - :exc:`InvalidAccessToken`
            - :exc:`InvalidRefreshToken`
            - :exc:`InvalidAuthorizationCode`
            - :exc:`UserIsAtGuildLimit`
