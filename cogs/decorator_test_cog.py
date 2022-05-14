import io
import sys
import discord
import asyncio
import traceback
import translators
from io import StringIO, BytesIO
from datetime import datetime
from discord.ext import commands
from discord import ActionRow, Button, SelectMenu, SelectOption, ButtonStyle, TextInput, ApplicationCommandInteraction


class DecoratorsTest(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot

    @commands.command()
    async def test_cog_decorator(self, ctx):
        await ctx.send('Press the Button below!\nThis Button was pressed 0 times.', components=[[discord.Button(label='Press on me', custom_id='decorator_test', style=3)]])

    @commands.Cog.on_click(custom_id='decorator_test')
    async def _test(self, i: discord.ComponentInteraction):
        await i.edit(content=f'Press the Button below!\nThis Button was pressed {int(i.message.content.split()[-2])+1} times.')

    @commands.command()
    async def gender(self, ctx):
        await ctx.send(embed=discord.Embed(title='Choose your Gender below.'), components=[[
            SelectMenu(custom_id='choose_your_gender',
                       options=[
                           SelectOption(label='Female', value='Female', emoji='♀️'),
                           SelectOption(label='Male', value='Male', emoji='♂️'),
                           SelectOption(label='Trans/Non Binary', value='Non Binary', emoji='⚧')
                       ], placeholder='Choose your Gender')
        ]])

    # function that's called when the SelectMenu is used
    @commands.Cog.on_select()
    async def choose_your_gender(self, i: discord.ComponentInteraction):
        await i.respond(f'You selected `{i.component.values[0]}`!', hidden=True)

    #@commands.command()
    async def interaction_types(self, ctx):
        components = [ActionRow(
            Button('msg_with_source', '4'),
            Button('deferred_msg_with_source', '5'),
            Button('deferred_update_msg', '6'),
            Button('update_msg', '7'),
            Button('hidden', 'enable_hidden')
        ), ActionRow(
            SelectMenu(
                'interaction_types_example',
                [
                    SelectOption('msg_with_source', '4', 'Respond with a message', '4️⃣'),
                    SelectOption('deferred_msg_with_source', '5', 'ACK an interaction[...]; user sees a loading state', '5️⃣'),
                    SelectOption('deferred_update_msg', '6', 'ACK an interaction[...]; no loading state', '6️⃣'),
                    SelectOption('update_msg', '7', 'Edit the message the component was attached to', '7️⃣'),
                    SelectOption('show_modal', '9', 'Respond to the interaction by sending a popup modal', '7️⃣')
                ]
            )
        )]

        embed = discord.Embed(title='Interaction Callback Type', description='These are all interaction-callback-types you could use for slash-commands and message-components:', color=discord.Color.green())
        await ctx.send(embed=embed, components=components)

    @commands.Cog.on_click()
    async def enable_hidden(self, i: discord.ComponentInteraction, b):
        components = i.message.components.copy()
        components[0].disable_component_at(0)
        components[0].disable_component_at(2)
        components[0][3].style = ButtonStyle.green
        await i.edit(components=i.message.components[0].disable_component_at(0))

    # @commands.Cog.listener()
    async def _raw_button_click(self, i: discord.ComponentInteraction, b):
        if b.custom_id in [4, 5, 6, 7]:
            if i.message.components[0][0].disabled is True:
                hidden = True
            else:
                hidden = False
            _type = b.custom_id
            if _type == 4:
                await i.respond('This is of type `4`')
            elif _type == 5:
                await i.defer(5, hidden=hidden)
                await asyncio.sleep(5)
                await i.respond('Yes that is of type `5`')
            elif _type == 6:
                await i.defer(hidden=hidden)
                await asyncio.sleep(5)
                await i.edit(embeds=[i.message.embeds[0], discord.Embed(title='This is of type `6`')])
            elif _type == 7:
                msg = await i.edit(embed=i.message.embeds[0].add_field(name=i.author, value='This is of type `7`'))
                await asyncio.sleep(5)
                msg.embeds[0].clear_fields()
                await i.message.edit(embed=msg.embeds[0])

    #@commands.Cog.on_select()
    async def interaction_types_example(self, i: discord.ComponentInteraction, s):
        _type = s.values[0]
        if _type == 4:
            await i.respond('This is of type `4`')
        elif _type == 5:
            await i.defer(5)
            await asyncio.sleep(5)
            await i.respond('Yes this is of type `5`')
        elif _type == 6:
            await i.defer()
            await asyncio.sleep(5)
            await i.edit(embeds=[i.message.embeds[0], discord.Embed(title='This is of type `6`')])
        elif _type == 7:
            msg = await i.edit(embed=i.message.embeds[0].add_field(name=i.author, value='This is of type `7`'))
            await asyncio.sleep(5)
            msg.embeds[0].clear_fields()
            await i.message.edit(embed=msg.embeds[0])
        elif _type == 9:
            await i.respond_with_modal(
                discord.Modal(
                    title='This is of type 9',
                    custom_id='response_types_example_modal',
                    components=[
                        TextInput(
                            style=1,
                            label='This is a short(single-line) input',
                            placeholder='Enter something in here.',
                            custom_id='short_input'
                        ),
                        TextInput(
                            style=2,
                            label='This is a long(multi-line) input',
                            placeholder='Enter something longer in here.',
                            custom_id='long_input'
                        )
                    ]
                )
            )
            modal_interaction: discord.ModalSubmitInteraction = await self.bot.wait_for('modal_submit', check=lambda mi: mi.author == i.author)
            embed = discord.Embed(color=discord.Color.green())
            embed.add_field(
                name='Content of short input:',
                value=modal_interaction.get_field('short_input').value,
                inline=False
            )
            embed.add_field(
                name='Content of long input:',
                value=modal_interaction.get_field('long_input').value,
                inline=False
            )
            await modal_interaction.respond(embed=discord.Embed(color=discord.Color.green()))

    @commands.command()
    async def edit_hidden(self, ctx):
        await ctx.send('Press the Button', components=[Button('Hey', 'edit_hidden_msg')])

    @commands.Cog.on_click()
    async def edit_hidden_msg(self, interaction: discord.ComponentInteraction, button):
        await interaction.respond('Hello', components=[[Button('Test', 'test_hidden_edit')]], hidden=True)

    @commands.Cog.on_click()
    async def test_hidden_edit(self, interaction: discord.ComponentInteraction, button):
        await interaction.edit(conent='Nice!')

    @commands.command()
    async def thinking(self, ctx):
        await ctx.send('Press the button to make me think',
                       components=[ActionRow(Button('Think', 'think_example', ButtonStyle.green, '🤔'))])

    @commands.Cog.on_click()
    async def think_example(self, i: discord.ComponentInteraction, button):
        await i.defer(discord.InteractionCallbackType.deferred_msg_with_source)
        await asyncio.sleep(3)
        await i.edit(content=f'{i.author.mention} I have no idea 💡')

    @commands.command()
    async def melon(self, ctx):
        await ctx.send('Press the button to order a melon',
                       components=[ActionRow(Button('Melon', 'type_6', ButtonStyle.green, '🍉'))])

    @commands.Cog.on_click()
    async def type_6(self, i: discord.ComponentInteraction, button):
        await i.defer()
        await asyncio.sleep(3)
        await i.edit(content=None, embed=discord.Embed(title='Here is your order', timestamp=datetime.utcnow()).set_image(url='attachment://watermelon-1969949_960_720.webp'),
                     file=discord.File('watermelon-1969949_960_720.webp'),
                     components=[])

    @commands.command()
    async def change(self, ctx):
        await ctx.send('Press the button and see...',
                       components=[ActionRow(Button('Press', 'edit_', ButtonStyle.blurple, '😀'))])

    @commands.Cog.on_click()
    async def edit_(self, i: discord.ComponentInteraction, button):
        await i.edit(content='Hello this is `InteractionCallbackType.update_msg`', components=[i.message.components[0].disable_all_buttons()])

    @commands.command()
    async def respond(self, ctx):
        await ctx.send('Press the button and see...',
                       components=[ActionRow(Button('I will respond', 'respond_', ButtonStyle.red, '😎'))])

    @commands.Cog.on_click()
    async def respond_(self, i: discord.ComponentInteraction, button):
        await i.respond('Hello There 👋')

    @commands.command()
    async def url(self, ctx):
        await ctx.send('This is a green Button', components=[Button('Read The Docs', style=ButtonStyle.url, emoji='<:rtfd:859143812714070046>', url='https://discordpy-message-components.readthedocs.io/en/latest/')])

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def perms(self, ctx, member: discord.Member):
        print(ctx.channel.permissions_for(member))
        embed = discord.Embed(title=f'Permissions for {member}', description=f'These are the Permissions {member.mention} has:')
        for permission in member.guild_permissions:
            embed.add_field(name=permission[0], value=permission[1], inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def style(self, ctx):
        time = datetime(2004, 10, 4, 7, 45)
        msg = '\n'.join([f'**{repr(style)}:** {discord.utils.styled_timestamp(time, style)}' for style in discord.TimestampStyle])
        await ctx.send(msg)

    @commands.command()
    async def edit_me(self, ctx):
        await ctx.send('Click me!', components=[[Button('Click me!', 'click_on_me')]])

    @commands.Cog.on_click()
    async def click_on_me(self, i: discord.ComponentInteraction, b: Button):
        b.disable_if(4 < 16)
        await i.edit(components=i.message.components)

    @commands.Cog.slash_command(base_name='test',
                                name='cog',
                                description='A test in a cog.',
                                guild_ids=[852871920411475968])
    async def cog_test(self, ctx: discord.ApplicationCommandInteraction):
        await ctx.respond('Press the Button', components=[ActionRow(
            Button(label='Press me',
                   custom_id=f'callback-button-press-{ctx.id}',
                   style=ButtonStyle.blurple,
                   emoji='🔴')
        )])

    @commands.Cog.on_click(r'callback-button-press-[0-9]{16,21}')
    async def callback_for_cog_test(self, ctx: discord.ComponentInteraction, button: Button):
        msg = await ctx.respond(f'The custom-id of the Button is `{button.custom_id}`.')
        print(msg)

    @commands.Cog.slash_command(base_name='test',
                                name='ne',
                                description='Another test in a cog.',
                                guild_ids=[852871920411475968])
    async def cog_test1(self, ctx: discord.ApplicationCommandInteraction):
        m = await ctx.defer()
        await ctx.respond(m.id)
        await asyncio.sleep(3)
        await ctx.respond('This command is in a cog too lol.')

    @cog_test1.error
    async def cog_test_error(self, ctx, exc):
        await ctx.channel.send(f'```py\n{exc}\n```')

    @commands.command()
    async def time(self, ctx: commands.Context, *, date_and_time: datetime):
        await ctx.send(discord.utils.styled_timestamp(date_and_time))

    #@time.error
    async def time_error(self, ctx, exc):
        await ctx.send(f'```py\n{exc}\n```')

    @commands.Cog.message_command(guild_ids=[852871920411475968])
    async def translate(self, interaction: discord.ApplicationCommandInteraction, message):
        if not message.content:
            return await interaction.respond('There is no content that could be translated.', hidden=True)
        await interaction.defer(hidden=True)
        translated = await asyncio.to_thread(translators.google,
                                             query_text=message.content,
                                             to_language=interaction.author_locale.value,
                                             sleep_seconds=4)
        if len(translated) > 2000:
            new_file = io.StringIO()
            file = new_file.write(translated)
            return await interaction.respond(file=discord.File(file, filename=f'{interaction.id}_translated.txt'), hidden=True)
        await interaction.respond(translated, hidden=True)

    @translate.error
    async def translate_error(self, ctx: ApplicationCommandInteraction, exc: Exception):
        f = StringIO()
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        f.writelines(tb)
        embed = discord.Embed(
            title='❗Translation failed❗',
            color=discord.Color.red()
        )
        if len(content:= f.getvalue()) <= 3980:
            embed.description = f'```py\n'\
                                f'{content}'\
                                f'\n```'
            try:
                await ctx.respond(embed=embed, hidden=True)
            except discord.HTTPException:
                await ctx.channel.send(embed=embed)
        else:
            try:
                await ctx.respond(file=discord.File(f), hidden=True)
            except discord.HTTPException:
                await ctx.channel.send(file=discord.File(f))

    @commands.Cog.user_command(guild_ids=[852871920411475968])
    async def userinfo(self, interaction: discord.ApplicationCommandInteraction, member: discord.Member):
        _roles = member.roles.copy()
        _roles.remove(member.guild.default_role)  # skipp @everyone
        _roles.reverse()

        embed = discord.Embed(
            title=f'Userinfo for {member}',
            description=f'This is a Userinfo for {member.mention}.',
            timestamp=datetime.utcnow(),
            color=member.color
        )

        to_add = [
            ('Name:', member.name, True),
            ('Tag:', member.discriminator, True),
            ('User-ID:', member.id, True),
            ('Nitro:', '✅ Yes' if member.premium_since else '❔ Unknown', True),
            ('Nick:', member.nick, True),
            ('Created-at:', discord.utils.styled_timestamp(member.created_at, 'R'), True),
            ('Joined at', discord.utils.styled_timestamp(member.joined_at, 'R'), True)
        ]
        if member.premium_since:
            to_add.append(('Premium since:', discord.utils.styled_timestamp(member.premium_since, 'R'), True))
        try:
            roles_list = f'{_roles.pop(0)}'
        except IndexError:  # The Member don't has any roles
            roles_list = '`None`'
        else:
            for role in _roles:
                updated = f'{roles_list}, {role.mention}'
                if updated > 1024:
                    roles_list = updated
                else:
                    break
        to_add.append((f'Roles: {len(member.roles) - 1}', roles_list, True))

        for name, value, inline in to_add:
            embed.add_field(name=name, value=value, inline=inline)

        embed.set_author(name=member.display_name, icon_url=member.display_avatar_url,
                         url=f'https://discord.com/users/{member.id}')
        embed.set_footer(text=f'Requested by {interaction.author}', icon_url=interaction.author.display_avatar_url)
        if not member.bot:
            user = await self.bot.fetch_user(member.id)  # to get the banner data we need to fetch the user
            if user.banner:
                embed.add_field(name='Banner', value=f'See the [banner]({user.banner_url}) below', inline=False)
            else:
                embed.add_field(name='Banner Color',
                                value=f'See the [banner-color](https://serux.pro/rendercolour?hex={hex(user.banner_color.value).replace("0x", "")}?width=500) below',
                                inline=False)
            if user.banner:
                embed.set_image(url=user.banner_url)
            else:
                embed.set_image(
                    url=f'https://serux.pro/rendercolour?hex={hex(user.banner_color.value).replace("0x", "")}&width=500')
        await interaction.respond(embed=embed, hidden=True)

    #@commands.Cog.listener()
    async def on_application_command_error(self, cmd, interaction, exception):
        print(exception)
        if interaction._command.type.chat_input and cmd.type == discord.OptionType.sub_command:
            if cmd.parent.type == discord.OptionType.sub_command_group:
                name = f'sub-command {cmd.name} of sub-command-group {cmd.parent.name} of command {cmd.parent.parent.name}'
            else:
                name = f'sub-command {cmd.name} of command {cmd.parent.name}'
        else:
            name = cmd.name

        try:
            fp = StringIO()
            print('Ignoring exception in {type} {name}({id})'.format(type=interaction.command.type,
                                                                     name=name,
                                                                     id=interaction.command.id),
                  file=fp)
            traceback.print_exception(type(exception), exception, exception.__traceback__, file=fp)
            print(fp.read())
            if len(content:= fp.read()) > 1991:
                await asyncio.wait_for(interaction.channel.send(file=discord.File(fp)), timeout=10)
            else:
                await interaction.channel.send(f'```py\n{content}\n```')
            del fp
        except Exception as exc:
            raise exc

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, guild: discord.Guild, event: discord.GuildScheduledEvent):
        print(event)

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, guild: discord.Guild, before: discord.GuildScheduledEvent, after: discord.GuildScheduledEvent):
        print(after)

    @commands.Cog.listener()
    async def on_ready(self):
        print(self.bot.get_guild(852871920411475968).events)

    @commands.Cog.slash_command()
    async def test2(self, ctx):
        await ctx.respond(
            'Ja oder nein?',
            components=[
                [Button('Ja', 'test2:yes', ButtonStyle.green, emoji='✅'), Button('Nein', 'test2:no', ButtonStyle.green, emoji='❌')]
            ]
        )

    @commands.Cog.on_click('test2')
    async def test2_callback(self, ctx, button):
        if button.custom_id.endswith('yes'):
            await ctx.respond('Du hast `Ja` gesagt.', hidden=True)
        elif button.custom_id.endswith('no'):
            await ctx.respond('Du hast `Nein` gesagt.', hidden=True)


def setup(bot):
    bot.add_cog(DecoratorsTest(bot))
