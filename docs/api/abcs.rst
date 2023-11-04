.. currentmodule:: discord

.. _discord_api_abcs:

Abstract Base Classes
-----------------------

An :term:`py:abstract base class` (also known as an ``abc``) is a class that models can inherit
to get their behaviour. The Python implementation of an :doc:`abc <py:library/abc>` is
slightly different in that you can register them at run-time. **Abstract base classes cannot be instantiated**.
They are mainly there for usage with :func:`py:isinstance` and :func:`py:issubclass`\.

This library has a module related to abstract base classes, some of which are actually from the :doc:`abc <py:library/abc>` standard
module, others which are not.

Snowflake
~~~~~~~~~~

.. attributetable:: discord.abc.Snowflake

.. autoclass:: discord.abc.Snowflake
    :members:

User
~~~~~

.. attributetable:: discord.abc.User

.. autoclass:: discord.abc.User
    :members:

PrivateChannel
~~~~~~~~~~~~~~~

.. attributetable:: discord.abc.PrivateChannel

.. autoclass:: discord.abc.PrivateChannel
    :members:

GuildChannel
~~~~~~~~~~~~~

.. attributetable:: discord.abc.GuildChannel

.. autoclass:: discord.abc.GuildChannel
    :members:

Messageable
~~~~~~~~~~~~

.. attributetable:: discord.abc.Messageable

.. autoclass:: discord.abc.Messageable
    :members:
    :exclude-members: history, typing

    .. automethod:: discord.abc.Messageable.history
        :async-for:

    .. automethod:: discord.abc.Messageable.typing
        :async-with:

Connectable
~~~~~~~~~~~~

.. attributetable:: discord.abc.Connectable

.. autoclass:: discord.abc.Connectable
