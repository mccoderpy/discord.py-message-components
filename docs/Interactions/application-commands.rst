.. currentmodule:: discord


ApplicationCommand
~~~~~~~~~~~~~~~~~~~

.. attributetable:: ApplicationCommand

.. autoclass:: ApplicationCommand()
    :exclude-members: error
    :members:

    .. automethod:: error
        :decorator:

SlashCommand
~~~~~~~~~~~~~

.. attributetable:: SlashCommand

.. autoclass:: SlashCommand()
    :members:
    :inherited-members:
    :exclude-members: autocomplete_callback

    .. automethod:: autocomplete_callback
        :decorator:


.. attributetable:: SubCommand

.. autoclass:: SubCommand()
    :members:
    :exclude-members: autocomplete_callback, error

    .. automethod:: autocomplete_callback
        :decorator:

    .. automethod:: error
        :decorator:

SlashCommandOption
~~~~~~~~~~~~~~~~~~~

.. attributetable:: SlashCommandOption

.. autoclass:: SlashCommandOption()
    :members:
    :inherited-members:

SlashCommandOptionChoice
~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: SlashCommandOptionChoice

.. autoclass:: SlashCommandOptionChoice()
    :members:
    :inherited-members:

UserCommand
~~~~~~~~~~~~~

.. attributetable:: UserCommand

.. autoclass:: UserCommand()
    :members:
    :inherited-members:

MessageCommand
~~~~~~~~~~~~~~~

.. attributetable:: MessageCommand

.. autoclass:: MessageCommand()
    :members:
    :inherited-members:

GuildAppCommandPermissions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: GuildAppCommandPermissions

.. autoclass:: GuildAppCommandPermissions()
    :members:

AppCommandPermissions
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: AppCommandPermission

.. autoclass:: AppCommandPermission()
    :members:


Miscellaneous
~~~~~~~~~~~~~

.. attributetable:: Mentionable

.. autoclass:: Mentionable()
    :members: