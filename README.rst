.. image:: https://cdn.discordapp.com/attachments/852872100073963532/854711446767796286/discord.py-message-components.png
    :target: https://pypi.org/project/discord.py-message-components
    :alt: Name of the project
            
.. image:: https://discord.com/api/guilds/852871920411475968/embed.png
  :target: https://discord.gg/sb69muSqsg
  :alt: Discord Server Invite

.. image:: https://img.shields.io/pypi/v/discord.py-message-components.svg
  :target: https://pypi.python.org/pypi/discord.py-message-components
  :alt: PyPI version info

.. image:: https://img.shields.io/pypi/pyversions/discord.py-message-components.svg
  :target: https://pypi.python.org/pypi/discord.py-message-components
  :alt: PyPI supported Python versions
  
.. image:: https://static.pepy.tech/personalized-badge/discord-py-message-components?period=total&units=international_system&left_color=grey&right_color=green&left_text=Downloads
  :target: https://pepy.tech/project/discord.py-message-components
  :alt: Total downloads for the project

The Original `discord.py <https://pypi.org/project/discord.py>`_ Library made by `Rapptz <https://github.com/Rapptz>`_ with implementation of the `Discord-Message-Components <https://discord.com/developers/docs/interactions/message-components>`_ by `mccoderpy <https://github.com/mccoderpy/>`_

Questions, Bugs or Ideas
________________________

Open a Issue/Pull request on `GitHub <https://github.com/mccoderpy/discord.py-message-components/pulls>`_, join the `support-Server <https://discord.gg/sb69muSqsg>`_ or send me a direct-message on `Discord <https://discord.com/channels/@me>`_: ``mccuber04#2960``

Installing
__________

**Python 3.5.3 or higher is required**

first uninstall the original `discord.py <https://pypi.org/project/discord.py>`_ Library:

.. code:: sh

    # Linux/macOS
    python3 -m pip uninstall discord.py

    # Windows
    py -3 -m pip uninstall discord.py

then install `this Library <https://pypi.org/project/discord.py-message-components>`_ using:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U discord.py-message-components

    # Windows
    py -3 -m pip install -U discord.py-message-components

Examples
--------

A Command that sends you a Message and edit it when you click a Button:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import typing
    import discord
    from discord.ext import commands
    from discord import ActionRow, Button, ButtonColor

    client = commands.Bot(command_prefix=commands.when_mentioned_or('.!'), intents=discord.Intents.all(), case_insensitive=True)

    @client.command(name='buttons', description='sends you some nice Buttons')
    async def buttons(ctx: commands.Context):
        components = [ActionRow(Button(label='Option Nr.1',
                                       custom_id='option1',
                                       emoji="🆒",
                                       style=ButtonColor.green
                                       ),
                                Button(label='Option Nr.2',
                                       custom_id='option2',
                                       emoji="🆗",
                                       style=ButtonColor.blurple)),
                      ActionRow(Button(label='A Other Row',
                                       custom_id='sec_row_1st option',
                                       style=ButtonColor.red,
                                       emoji='😀'),
                                Button(url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                       label="This is an Link",
                                       emoji='🎬'))
                      ]
        an_embed = discord.Embed(title='Here are some Button\'s', description='Choose an option', color=discord.Color.random())
        msg = await ctx.send(embed=an_embed, components=components)

        def _check(i: discord.RawInteractionCreateEvent):
            return i.message == msg and i.member == ctx.author

        interaction: discord.RawInteractionCreateEvent = await client.wait_for('interaction_create', check=_check)
        button_id = interaction.button.custom_id

        # This sends the Discord-API that the interaction has been received and is being "processed"
        await interaction.defer()  # if this is not used and you also do not edit the message within 3 seconds as described below, Discord will indicate that the interaction has failed.

        # If you use interaction.edit instead of interaction.message.edit, you do not have to deffer the interaction if your response does not last longer than 3 seconds.
        await interaction.edit(embed=an_embed.add_field(name='Choose', value=f'Your Choose was `{button_id}`'),
                               components=[components[0].disable_all_buttons(), components[1].disable_all_buttons()])

        # The Discord API doesn't send an event when you press a link button so we can't "receive" that.


    client.run('You Bot-Token here')


Another (complex) Example where a small Embed will be send; you can move a small white ⬜ with the Buttons:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    pointers = []


    class Pointer:
        def __init__(self, guild: discord.Guild):
            self.guild = guild
            self._possition_x = 0
            self._possition_y = 0

        @property
        def possition_x(self):
            return self._possition_x

        def set_x(self, x: int):
            self._possition_x += x
            return self._possition_x

        @property
        def possition_y(self):
            return self._possition_y

        def set_y(self, y: int):
            self._possition_y += y
            return self._possition_y


    def get_pointer(obj: typing.Union[discord.Guild, int]):
        if isinstance(obj, discord.Guild):
            for p in pointers:
                if p.guild.id == obj.id:
                    return p
            pointers.append(Pointer(obj))
            return get_pointer(obj)

        elif isinstance(obj, int):
            for p in pointers:
                if p.guild.id == obj:
                    return p
            guild = client.get_guild(obj)
            if guild:
                pointers.append(Pointer(guild))
                return get_pointer(guild)
            return None


    def display(x: int, y: int):
        base = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ]
        base[y].__setitem__(x, 1)
        base.reverse()
        return ''.join(f"\n{''.join([str(base[i][w]) for w in range(len(base[i]))]).replace('0', '⬛').replace('1', '⬜')}" for i in range(len(base)))


    empty_button = discord.Button(style=discord.ButtonStyle.Secondary, label=" ", custom_id="empty", disabled=True)


    def arrow_button():
        return discord.Button(style=discord.ButtonStyle.Primary)


    @client.command(name="start_game")
    async def start_game(ctx: commands.Context):
        pointer: Pointer = get_pointer(ctx.guild)
        await ctx.send(embed=discord.Embed(title="Little Game",
                                           description=display(x=0, y=0)),
                       components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                   discord.ActionRow(arrow_button().update(disabled=True).set_label('←').set_custom_id('left').disable_if(pointer.possition_x <= 0),
                                                     arrow_button().set_label('↓').set_custom_id('down').disable_if(pointer.possition_y <= 0),
                                                     arrow_button().set_label('→').set_custom_id('right'))
                                   ]
                       )


    @client.event
    async def on_raw_interaction_create(interaction: discord.RawInteractionCreateEvent):
        await interaction.defer()
        pointer: Pointer = get_pointer(interaction.guild)
        if not (message := interaction.message):
            message: discord.Message = await interaction.channel.fetch_message(interaction.message_id)
        if interaction.button.custom_id == "up":
            pointer.set_y(1)
            await message.edit(embed=discord.Embed(title="Little Game",
                                                   description=display(x=pointer.possition_x, y=pointer.possition_y)),
                               components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up').disable_if(pointer.possition_y >= 9), empty_button),
                                           discord.ActionRow(arrow_button().set_label('←').set_custom_id('left').disable_if(pointer.possition_x <= 0),
                                                             arrow_button().set_label('↓').set_custom_id('down'),
                                                             arrow_button().set_label('→').set_custom_id('right').disable_if(pointer.possition_x >= 9))]
                               )
        elif interaction.button.custom_id == "down":
            pointer.set_y(-1)
            await message.edit(embed=discord.Embed(title="Little Game",
                                                   description=display(x=pointer.possition_x, y=pointer.possition_y)),
                               components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                           discord.ActionRow(arrow_button().set_label('←').set_custom_id('left').disable_if(pointer.possition_x <= 0),
                                                             arrow_button().set_label('↓').set_custom_id('down').disable_if(pointer.possition_y <= 0),
                                                             arrow_button().set_label('→').set_custom_id('right').disable_if(pointer.possition_x >= 9))]
                               )
        elif interaction.button.custom_id == "right":
            pointer.set_x(1)
            await message.edit(embed=discord.Embed(title="Little Game",
                                                   description=display(x=pointer.possition_x, y=pointer.possition_y)),
                               components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                           discord.ActionRow(arrow_button().set_label('←').set_custom_id('left'),
                                                             arrow_button().set_label('↓').set_custom_id('down'),
                                                             arrow_button().set_label('→').set_custom_id('right').disable_if(pointer.possition_x >= 9))]
                               )
        elif interaction.button.custom_id == "left":
            pointer.set_x(-1)
            await message.edit(embed=discord.Embed(title="Little Game",
                                                   description=display(x=pointer.possition_x, y=pointer.possition_y)),
                               components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                           discord.ActionRow(arrow_button().set_label('←').set_custom_id('left').disable_if(pointer.possition_x <= 0),
                                                             arrow_button().set_label('↓').set_custom_id('down'),
                                                             arrow_button().set_label('→').set_custom_id('right'))]
                               )