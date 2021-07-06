Additions and adjustments to discord.py buildin-functions
=========================================================

.. _discord-Client:

:class:`discord.Client`
~~~~~~~~~~~~~~~~~~~~~~~

.. _on_click_decorator:

:func:`on_click`
________________
    
A decorator with which you can assign a function to a specific :class:`Button` (or its custom_id).

.. note::
    This will always give exactly one Parameter of type `discord.Interaction <./interaction.html#discord-interaction>`_ like an `raw_button_click-Event <#on-raw-button-click>`_.

.. important::
    The Function this decorator attached to must be an corountine (means an awaitable)

.. _button_click-parameters:

Parameters
-----------

.. _on_click-custom_id:

    :attr:`custom_id`: Optional[str]

        If the :attr:`custom_id` of the Button could not use as an function name or you want to give the function a diferent name then the custom_id use this one to set the custom_id.

.. _button_click-example:

Example
-------

.. code-block:: python

    # the Button
    Button(label='Hey im a cool blue Button',
            custom_id='cool blue Button',
            style=ButtonColor.blurple)

    # function thats called when the Button pressed
    @client.on_click(custom_id='cool blue Button')
    async def cool_blue_button(i: discord.Interaction):
        await i.respond('Hey you pressed a `cool blue Button`!', hidden=True)

Raises
------
:class:`TypeError`
    The coroutine passed is not actually a coroutine.

________________________________________

.. _on_select_decorator:

:func:`on_select`
_________________
A decorator with which you can assign a function to a specific :class:`SelectMenu` (or its custom_id).

.. note::
    This will always give exactly one Parameter of type `discord.Interaction <./interaction.html#discord-interaction>`_ like an `raw_selection_select-Event <#on-raw-button-click>`_.

.. important::
    The Function this decorator attached to must be an corountine (means an awaitable)

.. _on_select-parameters:

Parameters
----------

    .. _on_select-custom_id:

    :attr:`custom_id`: Optional[str]

        If the :attr:`custom_id` of the SelectMenu could not use as an function name or you want to give the function a diferent name then the custom_id use this one to set the custom_id.

.. _on_select-example:

Example
-------

.. code-block:: python

    # the SelectMenu
    SelectMenu(custom_id='choose_your_gender',
               options=[
                    select_option(label='Female', value='Female', emoji='♀️'),
                    select_option(label='Male', value='Male', emoji='♂️'),
                    select_option(label='Non Binary', value='Non Binary', emoji='⚧')
                    ], placeholder='Choose your Gender')

    # function thats called when the SelectMenu is used
    @client.on_select()
    async def choose_your_gender(i: discord.Interaction):
        await i.respond(f'You selected `{i.component.values[0]}`!', hidden=True)

Raises
------
:class:`TypeError`
    The coroutine passed is not actually a coroutine.

________________________________________________

.. _events:

Events
~~~~~~

.. _on_button_click:

:func:`on_button_click`
_______________________

This Event will be triggered if a Button, that is attached to a Message wich is in the internal Chage, is pressed.
It will returns two Parameters:

    The `Interaction <./interaction.html#interaction>`_ and the `ButtonClick <./interaction.html#buttonclick>`_ (this is also in the first parameter under ``component``). 

.. _on_button_click-example:

Example
--------

    .. code-block:: python

        @client.event
        async def on_button_click(interaction: discord.Interaction, button: discord.ButtonClick):
            await interaction.respond('Hey you pressed an Button!', delete_after=10)

________________________________________________

.. _on_raw_button_click:

:func:`on_raw_button_click`
___________________________

This Event will be triggered if a Button, that is attached to a Message of this Bot is pressed.
It will returns one Parameter:
    
    The `Interaction <./interaction.html#interaction>`_.

.. note::
    If the ``message`` is not in the internal Chage this parameter would be ``None`` until you set it manualy by fetching the message or using aiter :meth:`Interaction.respond` or :meth:`Interaction.edit`.

.. _on_raw_button_click-example:

Example
--------

    .. code-block:: python

        @client.event
        async def on_raw_button_click(interaction: discord.Interaction):
            await interaction.defer()
            if not interaction.message:
                interaction.message = await interaction.channel.fetch_message(interaction.message_id)
            await interaction.message.delete()
            await interaction.respond('Hey you pressed an Button!', delete_after=10)

________________________________________________

.. _on_selection_select:

:func:`on_selection_select`
___________________________

This Event will be triggered if a :class:`SelectionSelect`, that is attached to a Message of this Bot wich is in the internal Chage, is used.
It will returns two Parameters:
    
    The `Interaction <./interaction.html#interaction>`_ and the `SelectionSelect <./interaction.html#selectionselect>`_ (this is also in the first parameter under ``component``). 

.. _on_selection_select-example:

Example
--------

    .. code-block:: python

        @client.event
        async def on_selection_select(interaction: discord.Interaction, select: discord.SelectionSelect):
            await interaction.respond(f'Hey {interaction.author.mention} you select {", ".join(select.values)}!', hidden=True)

________________________________________________

.. _on_raw_selection_select:

:func:`on_raw_selection_select`
_______________________________

This Event will be triggered if a :class:`SelectionSelect`, that is attached to a Message of this Bot is used.
It will returns one Parameter:
    
    The `Interaction <./interaction.html#interaction>`_.

.. note::
    If the ``message`` is not in the internal Chage the ``message`` parameter of :class:`discord.Interaction` would be ``None`` until you set it manualy by fetching the message or using aiter :meth:`Interaction.respond` or :meth:`Interaction.edit`.

.. _on_raw_selection_select-example:

Example
--------

    .. code-block:: python

        @client.event
        async def on_raw_selection_select(interaction: discord.Interaction, select: discord.SelectionSelect):
            await interaction.defer() #It is better to defer here because the fetching of the message (if necessary) can take longer than 3 seconds.
            if not interaction.message:
                interaction.message = await interaction.channel.fetch_message(interaction.message_id)
            await interaction.edit(f'Hey {interaction.author.mention} you select {", ".join(select.values)}!', hidden=True)

__________________________________________________________________________________

.. _abc-messageable:

:class:`abc.Messageable`
~~~~~~~~~~~~~~~~~~~~~~~~

.. _abc-messageable-methods:

Methods
_______
This has the same methods as a normal message as well except for a change to the :meth:`send` method.

.. _abc-messageable-send:

:meth:`send`
____________

.. _abc-messageable-send-parameters:

Parameters
-----------
    These are the parameters that have been added by this, the others are still present and can be seen in the docs of discord.py
    
    .. _abc-messageable-send-components:

    :attr:`components`: Optional[List[Union[List[Buttton, SelectionSelect], ActionRow[Button, SelectionSelect]]]]

        A List of components that should send with the Message these can be either in `ActionRow <./components.html#actionrow>`_'s or in :class:`list`'s.
    
    .. _abc-messageable-send-embeds:

    :attr:`embeds`: Optional[List[discord.Embed]]
    
        A List of up to 10 :class:`discord.Embed`'s that should send with the Message.

_____________________________

.. _discord-message:

:class:`discord.Message`
~~~~~~~~~~~~~~~~~~~~~~~~

.. _discord-message-attributes:

Attributes
__________
This has the same attributes as a normal message but one is added in addition

    :attr:`components`: Optional[List[ActionRow[Union[Button, SelectMenu]]]]

        A list containing the components of the message

Methods
_______
This has the same methods as a normal message but one is added in addition
.. _discord-message-edit:

:meth:`edit`
____________
    This takes the same parameters as the normal edit function except for two added parameters.

.. _discord-message-edit-parameters:

Parameters
-----------
    These are the parameters that have been added by this, the others are still present and can be seen in the docs of discord.py
    
    .. _discord-message-edit-components:

    :attr:`components`: Optional[List[Union[List[Buttton, SelectionSelect], ActionRow[Button, SelectionSelect]]]]

        A List of components that should replace the previous ones these can be either in `ActionRow <./components.html#actionrow>`_'s or in :class:`list`'s.
    
    .. _discord-message-edit-embeds:

    :attr:`embeds`: Optional[List[discord.Embed]]
    
        A list of up to 10 :class:`discord.Embeds` to replace the previous ones

.. toctree:: 
   :maxdepth: 2
   :caption: Contents: 


Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
