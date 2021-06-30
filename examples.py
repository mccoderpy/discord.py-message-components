import typing
import discord
from discord.ext import commands
from discord import ActionRow, Button, ButtonColor

client = commands.Bot(command_prefix=commands.when_mentioned_or('.!'), intents=discord.Intents.all(), case_insensitive=True)


# A Command that sends you a Message and edit it when you click a Button


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

    def _check(i: discord.Interaction, b: discord.ButtonClick):
        return i.message == msg and i.author == ctx.author

    interaction, button = await client.wait_for('button_click', check=_check)
    button_id = button.custom_id

    # This sends the Discord-API that the interaction has been received and is being "processed"
    await interaction.defer()  # if this is not used and you also do not edit the message within 3 seconds as described below, Discord will indicate that the interaction has failed.

    # If you use interaction.edit instead of interaction.message.edit, you do not have to deffer the interaction if your response does not last longer than 3 seconds.
    await interaction.edit(embed=an_embed.add_field(name='Choose', value=f'Your Choose was `{button_id}`'),
                           components=[components[0].disable_all_buttons(), components[1].disable_all_buttons()])

    # The Discord API doesn't send an event when you press a link button so we can't "receive" that.

client.run('your Bot-Token here')
########################################################################################################################


# Another command where a small embed is sent where you can move the small white ⬜ with the buttons.

pointers = []


class Pointer:
    
    """Just a small class that facilitates holding and changing the position of the square"""
    
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
    """This function ``renders`` and returns the image"""
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
async def on_raw_button_click(interaction: discord.Interaction, button: discord.ButtonClick):
    await interaction.defer()
    pointer: Pointer = get_pointer(interaction.guild)
    if not (message := interaction.message):
        message: discord.Message = await interaction.channel.fetch_message(interaction.message_id)
    if button.custom_id == "up":
        pointer.set_y(1)
        await message.edit(embed=discord.Embed(title="Little Game",
                                               description=display(x=pointer.possition_x, y=pointer.possition_y)),
                           components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up').disable_if(pointer.possition_y >= 9), empty_button),
                                       discord.ActionRow(arrow_button().set_label('←').set_custom_id('left').disable_if(pointer.possition_x <= 0),
                                                         arrow_button().set_label('↓').set_custom_id('down'),
                                                         arrow_button().set_label('→').set_custom_id('right').disable_if(pointer.possition_x >= 9))]
                           )
    elif button.custom_id == "down":
        pointer.set_y(-1)
        await message.edit(embed=discord.Embed(title="Little Game",
                                               description=display(x=pointer.possition_x, y=pointer.possition_y)),
                           components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                       discord.ActionRow(arrow_button().set_label('←').set_custom_id('left').disable_if(pointer.possition_x <= 0),
                                                         arrow_button().set_label('↓').set_custom_id('down').disable_if(pointer.possition_y <= 0),
                                                         arrow_button().set_label('→').set_custom_id('right').disable_if(pointer.possition_x >= 9))]
                           )
    elif button.custom_id == "right":
        pointer.set_x(1)
        await message.edit(embed=discord.Embed(title="Little Game",
                                               description=display(x=pointer.possition_x, y=pointer.possition_y)),
                           components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                       discord.ActionRow(arrow_button().set_label('←').set_custom_id('left'),
                                                         arrow_button().set_label('↓').set_custom_id('down'),
                                                         arrow_button().set_label('→').set_custom_id('right').disable_if(pointer.possition_x >= 9))]
                           )
    elif button.custom_id == "left":
        pointer.set_x(-1)
        await message.edit(embed=discord.Embed(title="Little Game",
                                               description=display(x=pointer.possition_x, y=pointer.possition_y)),
                           components=[discord.ActionRow(empty_button, arrow_button().set_label('↑').set_custom_id('up'), empty_button),
                                       discord.ActionRow(arrow_button().set_label('←').set_custom_id('left').disable_if(pointer.possition_x <= 0),
                                                         arrow_button().set_label('↓').set_custom_id('down'),
                                                         arrow_button().set_label('→').set_custom_id('right'))]
                           )
