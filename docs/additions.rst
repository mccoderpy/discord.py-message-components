Additions and adjustments to discord.py builtin-functions
=========================================================

.. class:: discord.Client


    .. decorator:: on_click(custom_id=None)

        A decorator with which you can assign a function to a specific :class:`Button` (or its custom_id).

        .. important::
            The Function this decorator attached to must be an coroutine (means an awaitable) and take the same parameters as a :class:`on_raw_button_click`

        .. _button_click-parameters:

        :param custom_id: If the :attr:`custom_id` of the Button could not use as an function name or you want to give the function a different name then the custom_id use this one to set the custom_id.
        :type custom_id: Optional[:class:`str`]

        .. _button_click-example:

        **Example**

        .. code-block:: python

            # the Button
            Button(label='Hey im a cool blue Button',
                    custom_id='cool blue Button',
                    style=ButtonColor.blurple)

            # function that's called when the Button pressed
            @client.on_click(custom_id='cool blue Button')
            async def cool_blue_button(i: discord.Interaction, button):
                await i.respond('Hey you pressed a `cool blue Button`!', hidden=True)


        :raise TypeError: The coroutine passed is not actually a coroutine.


    .. decorator:: on_select(custom_id=None)

        A decorator with which you can assign a function to a specific :class:`SelectMenu` (or its custom_id).

        .. important::
            The Function this decorator attached to must be an coroutine(means an awaitable) and take the same parameters as a :class:`on_raw_selection_select`!

        .. _on_select-parameters:

        :param custom_id: If the :attr:`custom_id` of the :class:`SelectMenu` could not use as an function name or you want to give the function a different name then the custom_id use this one to set the custom_id.
        :type custom_id: Optional[:class:`str`]

        .. _on_select-example:

        **Example**

        .. code-block:: python

            # the SelectMenu
            SelectMenu(custom_id='choose_your_gender',
                       options=[
                            select_option(label='Female', value='Female', emoji='♀️'),
                            select_option(label='Male', value='Male', emoji='♂️'),
                            select_option(label='Trans/Non Binary', value='Trans/Non Binary', emoji='⚧')
                            ], placeholder='Choose your Gender')

            # function that's called when the SelectMenu is used
            @client.on_select()
            async def choose_your_gender(i: discord.Interaction, select_menu):
                await i.respond(f'You selected `{select_menu.values[0]}`!', hidden=True)


        :raise TypeError: The coroutine passed is not actually a coroutine.


.. _events:

Events
~~~~~~


.. function:: on_button_click(interaction, button)

    This Event will be triggered if a Button, that is attached to a Message wich is in the internal Cache, is pressed.

    :param interaction: The `Interaction <./interaction.html#Interaction>`_-object with all his attributes and methods to respond to the interaction
    :type interaction: :class:`discord.Interaction`
    :param button: The `ButtonClick <./interaction.html#ButtonClick>`_ if the message is ephemeral else `Button <./components.html#Button>`_. (this is also in the first parameter under ``component``).
    :type button: Union[:class:`Button`, :class:`ButtonClick`]

    .. _on_button_click-example:

    **Example**

    .. code-block:: python

        @client.event
        async def on_button_click(interaction: discord.Interaction, button):
            await interaction.respond('Hey you pressed an Button!', delete_after=10)


________________________________________________


.. function:: on_raw_button_click(interaction, button)

    This Event will be triggered if a Button, that is attached to **any** Message of this Bot is pressed.

    :param interaction: The :class:`discord.Interaction` that contains all information about the Interaction.
    :type interaction: :class:`discord.Interaction`
    :param button: The `ButtonClick <./interaction.html#ButtonClick>`_ if the message is ephemeral else `Button <./components.html#Button>`_. (this is also in the first parameter under ``component``).
    :type button: Union[:class:`Button`, :class:`ButtonClick`]

    .. _on_raw_button_click-example:

    **Example**

    .. code-block:: python

        @client.event
        async def on_raw_button_click(interaction: discord.Interaction, button):
            await interaction.respond('Hey you pressed an Button!', delete_after=10)



--------------------------------------------------

.. function:: on_selection_select(interaction, select_menu)

    This Event will be triggered if a :class:`SelectMenu`, that is attached to a Message of this Bot wich is in the internal Cache, is used.


    .. _on_selection_select-example:

    **Example**

    .. code-block:: python

        @client.event
        async def on_selection_select(interaction: discord.Interaction, select_menu):
            await interaction.respond(f'Hey {interaction.author.mention} you select {", ".join(select_menu.values)}!', hidden=True)



________________________________________________


.. function:: on_raw_selection_select(interaction, select_menu)

    This Event will be triggered if a :class:`SelectMenu`, that is attached to **any** Message of this Bot is used.
    
    :param interaction: The `Interaction <./interaction.html#Interaction>`_ that contains all information about the Interaction.
    :type interaction: :class:`discord.Interaction`
    :param select: The `SelectionSelect <./interaction.html#SelectionSelect>`_ if the message is ephemeral else `SelectMenu <./components.html#SelectMenu>`_  but with the :attr:`values` wich contains a list of the selected options. (this is also in the first parameter under ``component``).
    :type select: Union[:class:`SelectMenu`, :class:`SelectionSelect`]

    .. _on_raw_selection_select-example:

    **Example**

    .. code-block:: python

        @client.event
        async def on_raw_selection_select(interaction: discord.Interaction, select_menu):
            await interaction.edit(f'Hey {interaction.author.mention} you select {", ".join(select_menu.values)}!', hidden=True)


_______________________________________

.. _abc-messageable:

.. class:: abc.Messageable

    This has the same methods as a normal message as well except for a change to the :meth:`send` method.

    .. _abc-messageable-send:

    .. classmethod:: send(**kwargs)

        .. _abc-messageable-send-parameters:

        These are the parameters that have been added by this, the others are still present and can be seen in the docs of discord.py

        :param components: A List of components that should send with the Message these can be either in `ActionRow <./components.html#actionrow>`_'s or in :class:`list`'s.
        :type components: Optional[List[Union[List[Button, SelectionSelect], ActionRow[Button, SelectionSelect]]]]
        :param embeds: A List of up to 10 :class:`discord.Embed`'s that should send with the Message.
        :type embeds:  Optional[List[discord.Embed]]

_____________________________

.. class:: ext.commands.Cog

    This class has also the decorators for custom_id's as the normal :class:`discord.Client` Class.

    .. decorator:: commands.Cog.on_click(custom_id=None)

        This works like the :meth:`discord.Client.on_click` decorator of the :class:`discord.Client` but it give ``self`` (The Cog-Class) as the 1. Parameter.

        **Example**

        .. code-block:: python

            # The Button
            Button(label='Hello', custom_id='my_button')

            #The decorator
            @commands.Cog.on_click()
            async def my_button(i: discord.Interaction, button):
                await i.respond('Hey you pressed a Button!')

    .. decorator:: commands.Cog.on_select(custom_id=None)

        This works like the :meth:`discord.Client.on_select` decorator of the :class:`discord.Client` but it give ``self`` (The Cog-Class) as the 1. Parameter.

        **Example**

        .. code-block:: python

            # The SelectMenu
            SelectMenu(custom_id='select_decorator_example',
                       options=[
                           SelectOption('The 1. Option', '1', 'The first option you have', '1️⃣'),
                           SelectOption('The 2. Option', '2', 'The second option you have', '2️⃣')
                       ], placeholder='Select a Option')

            #The decorator
            @commands.Cog.on_select()
            async def select_decorator_example(i: discord.Interaction, select_menu):
                await i.edit(content=f'You choice was the {select_menu.values[0]}. Option. 😀')

----------------------------------

.. _discord-message:

.. class:: discord.Message

and

.. class:: discord.PartialMessage

    .. _discord-message-attributes:


    This has the same attributes as a normal message but one is added in addition

    .. attribute:: components

        A Optional[List[:class:`ActionRow`]] containing the components of the message.

    .. attribute:: all_components

        Returns all :class:`Button`'s and :class:`SelectMenu`'s that are contained in the message

        .. note::
            This is equal to:
            .. code-block:: python

                for action_row in self.components:
                    for component in action_row:
                        yield component

        :yields: Union[:class:`Button`, :class:`SelectMenu`]

    .. attribute:: all_buttons

        Returns all :class:`Button`'s that are contained in the message

        .. note::
            This is equal to:
            .. code-block:: python

                for action_row in self.components:
                    for component in action_row:
                        yield component

        :yields: :class:`Button`

    .. attribute:: all_select_menus

        Returns all :class:`SelectMenu`'s that are contained in the message

        .. note::
            This is equal to:
            .. code-block:: python

                for action_row in self.components:
                    for component in action_row:
                        if isinstance(component, SelectMenu):
                            yield component

        :yields: :class:`SelectMenu`

    This has the same methods as a normal message but one is added in addition.

    .. _discord-message-edit:

    .. method:: edit(**kwargs)

        This takes the same parameters as the normal :func:`edit` function except for two added parameters.

        .. _discord-message-edit-parameters:

        :param components: A List of components that should replace the previous ones these can be either in `ActionRow <./components.html#actionrow>`_'s or in :class:`list`'s.
        :type components: Optional[List[Union[List[:class:`Button`, :class:`SelectMenu`], ActionRow[:class:`Button`, :class:`SelectMenu`]]]]
        :param embeds: A list of up to 10 :class:`discord.Embed`'s to replace the previous ones(This is also usable for normal Messages).
        :type embeds: Optional[List[:class:`discord.Embed`]]

utils
~~~~~

.. function:: styled_timestamp(timestamp, style)

    A small function that returns a styled timestamp for discord, this will be displayed accordingly in the Discord client depending on the :attr:`style` specified.

    Timestamps will display the given timestamp in the user's timezone and locale.

    :param timestamp: Union[`datetime.datetime <https://docs.python.org/3/library/datetime.html#datetime.datetime>`_, :class:`int`]
        The timestamp; A :class:`datetime.datetime` object or an already completed timestamp.

    :param style: Optional[Union[:class:`TimestampStyle`, :class:`str`]]
        How the timestamp should be displayed in Discord; this can either be a :class:`TimestampStyle` or directly the associated value.

        :default: :class:`TimestampStyle.short`

    **Example**

    .. code-block:: python

        @client.command()
        async def time(ctx):
            await ctx.send(discord.utils.styled_timestamp(datetime.now(), discord.TimestampStyle.long))

.. class:: TimestampStyle

    .. note::
        This is located in discord.enums but i place it here

    The Styles you could use for the :attr:`style` of a :class:`styled_timestamp`

    See also in the `Discord-Documentation <https://discord.com/developers/docs/reference#message-formatting-timestamp-styles>`_

    +----------------------------------+-------+-----------------+--------------------------------+
    | NAME                             | VALUE | DESCRIPTION     | EXAMPLE                        |
    +==================================+=======+=================+================================+
    | .. attribute:: short_time        |  't'  | Short Time      | .. image:: imgs/short_time.png |
    +----------------------------------+-------+-----------------+--------------------------------+
    | .. attribute:: long_time         |  'T'  | Long Time       | .. image:: imgs/long_time.png  |
    +----------------------------------+-------+-----------------+--------------------------------+
    | .. attribute:: short_date        |  'd'  | Short Date      | .. image:: imgs/short_date.png |
    +----------------------------------+-------+-----------------+--------------------------------+
    | .. attribute:: long_date         |  'D'  | Long Date       | .. image:: imgs/long_date.png  |
    +----------------------------------+-------+-----------------+--------------------------------+
    | .. attribute:: short             |  'f'  | Short Date/Time | .. image:: imgs/short.png      |
    +----------------------------------+-------+-----------------+--------------------------------+
    | .. attribute:: long              |  'F'  | Long Date/Time  | .. image:: imgs/long.png       |
    +----------------------------------+-------+-----------------+--------------------------------+
    | .. attribute:: relative          |  'R'  | Relative Time   | .. image:: imgs/relative.png   |
    +----------------------------------+-------+-----------------+--------------------------------+

.. toctree::
   :maxdepth: 3
   :caption: Contents: 


Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
