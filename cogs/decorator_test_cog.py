import io
import re
import sys

import aiohttp

import discord
import asyncio
import traceback
import translators
from io import StringIO, BytesIO
from datetime import datetime, timedelta
from discord.ext import commands
from discord import ActionRow, Button, SelectMenu, SelectOption, ButtonStyle, TextInput, ApplicationCommandInteraction, \
    Localizations, SlashCommandOption, OptionType, SlashCommandOptionChoice
from discord import SlashCommandOptionChoice as Choice, SlashCommandOption as Option

tixte_auth = "3167e71d-f0dd-4490-9010-a1d706cc452a"
tixte_auth_token = 'tx.3mHBIuoOY74SrlPF.jmRqjvhmyItk1Kf1.sAf6J8B5oszemiR0.UVst'


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
    #@commands.Cog.on_select()
    async def choose_your_gender(self, i: discord.ComponentInteraction, select):
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

    @commands.Cog.on_select()
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
            await modal_interaction.respond(embed=embed)

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
        await i.defer(6)
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
        await i.defer(hidden=True)
        await asyncio.sleep(1)
        await i.respond('Hello There 👋', hidden=True)

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

    @commands.Cog.message_command(name_localizations=Localizations(german='übersetzen'),guild_ids=[852871920411475968])
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
            roles_list = f'{_roles.pop(0).mention}'
        except IndexError:  # The Member don't has any roles
            roles_list = '`None`'
        else:
            for role in _roles:
                updated = f'{roles_list}, {role.mention}'
                if len(updated) < 1024:
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
                if user.banner_color:
                    embed.add_field(name='Banner Color',
                                    value=f'See the [banner-color](https://serux.pro/rendercolour?hex={hex(user.banner_color.value).replace("0x", "")}?width=500) below',
                                    inline=False)
            if user.banner:
                embed.set_image(url=user.banner_url)
            else:
                if user.banner_color:
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
        print(before)
        print(after)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, guild: discord.Guild, event: discord.GuildScheduledEvent):
        print(event)

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

    @commands.Cog.slash_command(
        name='upload',
        description='Uploads the given file(s) to mccubers\' Tixte account.',
        guild_ids=[852871920411475968],
        options=[SlashCommandOption(option_type=OptionType.attachment,
                                    name='file',
                                    description='The file to upload'),
                 SlashCommandOption(option_type=str,
                                    name='domain',
                                    description='Select a domain where the file should be uploaded to.',
                                    autocomplete=True,
                                    required=False),
                 SlashCommandOption(option_type=str,
                                    name='name',
                                    description='Optional: The new filename',
                                    required=False),
                 SlashCommandOption(option_type=bool,
                                    name='use-random-name',
                                    description='Optional: use random filename',
                                    required=False)
                 ],
        connector={'use-random-name': 'random_name'})
    async def tixte_upload(
            self,
            ctx: discord.ApplicationCommandInteraction,
            file: discord.Attachment,
            domain: str = 'my-code.is-from.space',
            name: str = None,
            random_name: bool = False
    ):
        msg = await ctx.respond(f'uploading file to `{domain}`...')
        form = aiohttp.FormData()
        form.add_field(name='payload_json',
                       value=discord.utils.to_json({"upload_source": "custom", "domain": domain.rstrip(), "type": 1,
                                      "name": name or file.filename})
                       )
        form.add_field(name='file',
                       content_type=file.content_type,
                       value=(await file.read()))
        async with aiohttp.ClientSession(headers={'Authorization': tixte_auth}) as tixte:
            async with tixte.request('POST',
                                     f'https://api.tixte.com/v1/upload?random={"true" if random_name else "false"}',
                                     data=form, ssl=False) as resp:
                data = await resp.json()

        if not data['success'] == True:
            return await msg.edit(content=f'**`Error occurred:`**```json\n{data["error"]["message"]}\n```')

        embed = discord.Embed(title=data['data']['message'], description=f'Here is your file: {data["data"]["url"]}')
        embed.set_image(url=data['data']['direct_url'])
        await msg.edit(content='',
                       embed=embed,
                       components=[[
                           Button(label='open in browser',
                                  url=data['data']['url']),
                           Button(label='delete file',
                                  custom_id=f'tixte:delete:{data["data"]["deletion_url"].split("?")[0]}',
                                  style=ButtonStyle.red,
                                  emoji='🗑️')
                       ]])

    @tixte_upload.autocomplete_callback
    async def tixte_domains_getter(self, interaction: discord.AutocompleteInteraction, *args, **kwargs):
        async with aiohttp.ClientSession(headers={'Authorization': tixte_auth_token, }) as tixte:
            async with tixte.get('https://api.tixte.com/v1/users/@me/domains', ssl=False) as resp:
                data = await resp.json()
        await interaction.suggest(
            [SlashCommandOptionChoice(name=f'{d["name"]} - {d["uploads"]} uploads', value=f'{d["name"]}') for d in
             data['data']['domains']])

    @commands.Cog.on_click(r'tixte:delete:https://.*')
    async def tixte_delete(self, interaction: discord.ComponentInteraction, button):
        before_embed = interaction.message.embeds[0]
        before_components = interaction.message.components
        msg = await interaction.edit(embed=discord.Embed(title='⚠Warning: ❗This action is not reversible❗⚠',
                                                         description='Are you sure you want to delete this file permanently?'),
                                     components=[
                                         [Button(label='Yes', custom_id='tixte:delete:yes', style=ButtonStyle.red),
                                          Button(label='No', custom_id='tixte:delete:cancel', style=ButtonStyle.red)]])
        try:
            inter, but = await self.bot.wait_for('button_click', check=lambda i, b: b.custom_id in ['tixte:delete:yes','tixte:delete:cancel'],
                                               timeout=10)
        except asyncio.TimeoutError:
            await msg.edit(embed=before_embed, components=before_components)
        else:
            if but.custom_id == 'tixte:delete:yes':
                url = re.match(r'tixte:delete:(?P<url>https://.*)', button.custom_id).group('url')
                async with aiohttp.ClientSession(
                        headers={'Authorization': tixte_auth, 'Media-Type': 'application/json'}) as tixte:
                    async with tixte.request('GET', f'{url}?auth={tixte_auth}', ssl=False) as resp:
                        data = await resp.json()
                await inter.edit(embed=discord.Embed(title=data['data']['message'], color=discord.Color.green()),
                                 components=[])
            else:
                await inter.edit(embed=before_embed, components=before_components)

    @commands.Cog.slash_command(
        name="start-voice-activity",
        description='Creates a voice channel activity',
        options=[
            Option(
                name="activity-type",
                description="The activity to start.",
                   option_type=str,
                   choices=[
                       Choice(
                           ac['name'],
                           ac['value']
                       ) for ac in [
                           {"name": "YouTube Together",
                            "value": "880218394199220334"},
                           {"name": "Betrayal.io",
                            "value": "773336526917861400"},
                           {"name": "Poker Night",
                            "value": "755827207812677713"},
                           {"name": "Fishington.io",
                            "value": "814288819477020702"},
                           {"name": "Chess in the Park",
                            "value": "832012586023256104"},
                           {'name': 'Doodle',
                            'value': '878067389634314250'},
                           {'name': 'Letter Tile',
                            'value': '879863686565621790'},
                           {'name': 'Word Snacks',
                            'value': '879863976006127627'},
                           {'name': 'Awkword',
                            'value': '879863881349087252'},
                           {'name': 'Click Dis',
                            'value': '832012854282158180'},
                           {'name': 'Sketchy Artist',
                            'value': '879864070101172255'},
                           {'name': 'SpellCast',
                            'value': '852509694341283871'},
                           {'name': 'Checkers in the Park',
                            'value': '832013003968348200'}
                       ]
                   ]
            ),
            Option(
                name="voice-channel",
                description="the voice-channel i should create the activity for",
                option_type=discord.VoiceChannel,
                required=False
            )],
        connector={'voice-channel': 'voice_channel', 'activity-type': 'activity_type'}
    )
    async def start_voice_activity(self, ctx: ApplicationCommandInteraction, activity_type: str, voice_channel: discord.VoiceChannel = None):
        if channel := ((ctx.author.voice.channel if ctx.author.voice else None) if not voice_channel else voice_channel):
            try:
                invite = await channel.create_invite(target_application_id=activity_type, target_type=2, max_age=600)
            except discord.Forbidden:
                await ctx.respond(
                    f'**⚠It looks like I\'m missing one or more of these permissions in {channel.mention} that are needed to start an activity⚠**\n'
                    f'> **`Create Invites`**, **`Use Activities`**',
                    hidden=True
                )
            else:
                invite_embed = discord.Embed(
                    title="Voice Activity started",
                    description=f"I have started the voice activity in [{channel.mention}]({invite.url})",
                    color=discord.Color.green()
                )
                invite_embed.add_field(
                    name='Join',
                    value=f'[Klick here to join the activity]({invite})',
                    inline=False
                )
                invite_embed.add_field(
                    name='Note:',
                    value=f'This invite will expires in {discord.utils.styled_timestamp(datetime.now() + timedelta(minutes=10), discord.TimestampStyle.relative)}',
                    inline=False
                )
                await ctx.respond(
                    f'[{channel.mention}]({invite.url})',
                    embed=invite_embed,
                    delete_after=600
                )
        else:
            await ctx.respond(
                "You need to choice a voice-channel or bee in one to start a voice activity.",
                hidden=True
            )


def setup(bot):
    bot.add_cog(DecoratorsTest(bot))

