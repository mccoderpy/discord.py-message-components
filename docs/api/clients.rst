.. currentmodule:: discord

Clients
--------

Client
~~~~~~~

.. attributetable:: Client

.. autoclass:: Client
    :members:
    :exclude-members: fetch_guilds, event, once, slash_command, message_command, user_command, on_click, on_select, on_submit

    .. automethod:: Client.event()
        :decorator:

    .. automethod:: Client.once(name=None, check=None)
        :decorator:

    .. automethod:: Client.fetch_guilds
        :async-for:

    .. automethod:: Client.slash_command
        :decorator:

    .. automethod:: Client.message_command
        :decorator:

    .. automethod:: Client.user_command
        :decorator:

    .. automethod:: Client.on_click
        :decorator:

    .. automethod:: Client.on_select
        :decorator:

    .. automethod:: Client.on_submit
        :decorator:


AutoShardedClient
~~~~~~~~~~~~~~~~~~

.. attributetable:: AutoShardedClient

.. autoclass:: AutoShardedClient
    :members:
