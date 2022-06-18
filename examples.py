import os
import re
import sys
import typing
import asyncio
import inspect
from collections import defaultdict
from io import StringIO
from pprint import pprint
from pathlib import Path
from datetime import datetime
from discord.ext import commands
from discord.utils import to_json
from discord import Button, ButtonStyle, ActionRow, SelectMenu, SelectOption, SlashCommandOption as CommandOption, \
    option_str, option_int, option_float, SlashCommandOptionChoice, SlashCommandOption, OptionType, \
    ComponentInteraction, Permissions

import aiohttp
import discord
import logging
from logging.handlers import HTTPHandler


def replace_apimethodes():
    replaced = []
    for file in [p.as_posix() for p in Path('./discord').glob('*.py')]:
        with open(f'./{file}', 'r', encoding='UTF-8') as fp:
            content = fp.read()
        if 'APIMethodes' in content:
            content = content.replace('APIMethodes', 'API')
            with open(f'./{file}', 'w', encoding='UTF-8') as fp:
                fp.write(content)
            replaced.append(file)
    exit(f'replaced APIMethodes with API in {len(replaced)} files:\n' + "\n".join(replaced))


webhook_url = 'https://discord.com/api/webhooks/968875098192904263/E2-5aHFLjXayJ3QuXVaqxsYc5CCF2LxighcKExZxMiLrsYJpOY8Fs1kgrtiUx7mnRHl_'


class WebHookLogger(HTTPHandler):
    def __init__(self, host, url, method='POST', secure=False, credentials=None, context=None):
        super().__init__(host, url, method, secure, credentials, context)

    def emit(self, record) -> None:
        asyncio.get_event_loop().create_task(self.send_message(record))

    async def send_message(self, record) -> None:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(self.url, adapter=discord.AsyncWebhookAdapter(session=session))
            await webhook.send('```yaml\n{0.levelname}::{0.name}#{0.lineno} {1}\n```'.format(record, record.getMessage()), wait=True)


logging.basicConfig(level=logging.INFO)  # handlers=[WebHookLogger('discord.com:443', webhook_url)]


i = discord.Intents.all()
client = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'),
    strip_after_prefix=True,
    sync_commands_on_cog_reload=False,
    sync_commands=True,
    intents=i,
    gateway_version=10,
    remove_unused_commands=False,
    activity=discord.Activity(type=discord.ActivityType.competing, name='his bugs (lovely called features)')
)

# @client.command()
@commands.has_permissions(administrator=True)
async def start_bewerbung(ctx):
    await ctx.send('Was willst du werden?', components=[
        [            SelectMenu(custom_id='_select_it', options=[
                SelectOption(emoji='1️⃣', label='Developer', value='1',
                             description='Helfe beim der entwicklung von Software!'),
                SelectOption(emoji='2️⃣', label='Supporter', value='2',
                             description='Helfe Usern und unterstütze so das Team!'),
                SelectOption(emoji='3️⃣', label='Designer', value='3',
                             description='Gestalte den Server / Bot')],
                       placeholder='Wähle aus!')
        ]])


@client.on_select()
async def _select_it(i: discord.ApplicationCommandInteraction, select_menu):
    embed = discord.Embed(title='You have chosen:',
                          description=f"You have chosen " + '\n'.join([f'Option Nr° {o}' for o in select_menu.values]),
                          color=discord.Color.random())
    await i.respond(embed=embed, hidden=True)


@client.user_command(guild_ids=[852871920411475968])
async def userinfo(ctx: discord.ApplicationCommandInteraction, member: discord.Member):
    _roles = member.roles.copy()
    _roles.remove(member.guild.default_role)
    _roles.reverse()
    member: typing.Union[discord.User, discord.Member] = member
    user = await client.fetch_user(member.id)

    embed = discord.Embed(title=f'Userinfo for {member}',
                          description=f'This is a Userinfo for {member.mention}.',
                          timestamp=datetime.utcnow(),
                          color=member.color)

    to_add = [
        ('Name:', member.name, True),
        ('Tag:', member.discriminator, True),
        ('User-ID:', f'`{member.id}`', True),
        ('Statuses:', member.raw_status, True),
        ('Bot:', '✅' if member.bot else '❌'),
        ('Nitro:', '✅ Yes' if (await user.profile()).nitro or member.premium_since else '❔ Unknown', True),
        ('Nick:', member.nick, True),
        ('Created-at:', discord.utils.styled_timestamp(member.created_at, 'R'), True),
        ('Joined at', discord.utils.styled_timestamp(member.joined_at, 'R'), True),
        ('Roles:', '\n'.join([r.mention for r in _roles]), True)
    ]
    if member.premium_since:
        to_add.append(('Boosting since:', discord.utils.styled_timestamp(member.premium_since, 'R'), True))

    for name, value, inline in to_add:
        embed.add_field(name=name, value=value, inline=inline)

    embed.set_author(name=member.display_name, icon_url=member.display_avatar_url, url=f'https://discord.com/users/{member.id}')
    embed.set_footer(text=f'requested by {ctx.author}', icon_url=ctx.author.display_avatar_url)
    if not member.bot:
        if user.banner:
            embed.add_field(name='Banner', value=f'See the [banner](https://cdn.discordapp.com/banners/{user.id}/{user.banner}.{"gif" if user.is_banner_animated() else "webp"}) below', inline=False)
        else:
            embed.add_field(name='Banner Color', value=f'See the [banner-color](https://serux.pro/rendercolour?hex={hex(user.banner_color.value).replace("0x", "")}?width=500) below', inline=False)
        if user.banner:
            embed.set_image(url=user.banner_url)
        else:
            embed.set_image(url=f'https://serux.pro/rendercolour?hex={hex(user.banner_color.value).replace("0x", "")}&width=500')
    await ctx.respond(embed=embed, hidden=True)


@client.slash_command(base_name='documentation',
                      base_desc='Search\'s in the documentation.',
                      name='discordpy-message-components',
                      guild_ids=[852871920411475968])
async def library_docs(ctx: discord.ApplicationCommandInteraction, query: str):
    """Search's in the documentation of discord.py-message-components."""
    print(query)
    await ctx.respond(f'You are searching for [{query}](https://discordpy-message-components.readthedocs.io/en/latest/search.html?q={query.replace(" ", "%20")})')


@client.slash_command(base_name='permissions',
                      base_desc='Get or edit permissions for a user or a role.',
                      group_name='user',
                      group_desc='Get or edit permissions for a user.',
                      option_descriptions={'user': 'The user to get.',
                                           'channel': 'The channel permissions to get. If omitted, the guild permissions will be returned.'},
                      )
async def get(i: discord.ApplicationCommandInteraction, user: discord.Member, channel: discord.abc.GuildChannel = None):
    """Get permissions for a user."""
    permissions = []
    if channel:
        for name, value in channel.permissions_for(user):
            permissions.append({'name': name, 'value': {True: '✅', False: '❌', None: '⭕'}.get(value)})
        await i.respond(embed=discord.Embed(title=f'Permissions for {user} in {channel.name}', description='\n'.join(['{name} |  {value}'.format(**permission) for permission in permissions]), color=user.color, timestamp=datetime.now()).set_footer(text=f'invoked by {i.author}', icon_url=i.author.avatar_url))
    else:
        for name, value in user.guild_permissions:
            permissions.append({'name': name, 'value': {True: '✅', False: '❌', None: '⭕'}.get(value)})
        await i.respond(embed=discord.Embed(title=f'Permissions for {user}', description='\n'.join(['{name} |  {value}'.format(**permission) for permission in permissions]), color=user.color, timestamp=datetime.now()).set_footer(text=f'invoked by {i.author}', icon_url=i.author.avatar_url))

@client.slash_command(base_name='permissions',
                      group_name='user',
                      default_required_permissions=Permissions(administrator=True),
                      option_descriptions={'user': 'The user whose permissions are to be edited.',
                                           'channel': 'The channel permissions to edit. If omitted, the guild permissions will be edited.'},
                      guild_ids=[852871920411475968])
@commands.has_permissions(administrator=True)
async def edit(i: discord.ApplicationCommandInteraction, user: discord.Member, channel: typing.Optional[discord.TextChannel] = None):
    """Edit permissions for a user."""
    perms_embed = discord.Embed(
        description=f'Select/Unselect the Permissions the Member {user.mention} should have {f"in {channel.mention}" if channel else ""}.',
        timestamp=datetime.now())
    # perms_embed.add_field(name='NOTE:', value='If you unselect a permission the default-value would be used')
    permissions_selects = [SelectOption(label=name.replace('_', ' ').upper(), value=name, default=value or getattr(user.guild_permissions, name),
                                        description=inspect.cleandoc(getattr(discord.Permissions, name).__doc__)[36:136].split('\n')[0]) for
                           name, value in (channel.overwrites_for(user) if channel else user.guild_permissions)]
    components = [SelectMenu(custom_id=f'edit_permissions_for_{user.id}', options=options,
                             placeholder=f'Select the Permissions {user} should has/not-has', min_values=0,
                             max_values=len(options)) for options in [permissions_selects[x:x + 25] for x in
                                                                      range(0, len(permissions_selects),
                                                                            25)]]
    components = [ActionRow(components[0].set_custom_id(f'edit_permissions_for_{user.id}')), ActionRow(components[1].set_custom_id(f'edit_permissions_for_{user.id}_1')), ActionRow(Button(style=ButtonStyle.green, label='Apply', custom_id='accept'))]
    msg = await i.respond(embed=perms_embed, components=components, hidden=True)
    to_edit: typing.Union[discord.Permissions, discord.PermissionOverwrite] = channel.overwrites_for(user) if channel else discord.PermissionOverwrite(user.guild_permissions)

    def _check(i: discord.ComponentInteraction, s):
        return i.message_id == msg.id

    discord.Permissions()
    while True:
        try:
            done, pending = await asyncio.wait([client.loop.create_task(client.wait_for('selection_select', check=_check)),
                                                client.loop.create_task(client.wait_for('button_click', check=_check))],
                                               return_when=asyncio.FIRST_COMPLETED, timeout=60)
        except asyncio.TimeoutError:
            await i.edit(components=[c.disable_all_components() for c in msg.components])
        else:
            interaction, button_or_select = done.pop().result()
            if isinstance(button_or_select, SelectMenu):
                for value in button_or_select.values:
                    to_edit._set(value, True)
                for value in button_or_select.not_selected:
                    to_edit._set(value, None if channel else False)
                permissions_selects = [SelectOption(label=name.replace('_', ' ').upper(), value=name, default=value or getattr(user.guild_permissions, name),
                                                    description=inspect.cleandoc(getattr(discord.Permissions, name).__doc__)[36:136].split('\n')[0]) for name, value in to_edit]
                components = [SelectMenu(custom_id=f'edit_permissions_for_{user.id}', options=options,
                                         placeholder=f'Select the Permissions {user} should has/not-has', min_values=0,
                                         max_values=len(options)) for options in [permissions_selects[x:x + 25] for x in
                                                                                  range(0, len(permissions_selects),
                                                                                        25)]]
                components = [ActionRow(components[0].set_custom_id(f'edit_permissions_for_{user.id}')),
                              ActionRow(components[1].set_custom_id(f'edit_permissions_for_{user.id}_1')),
                              ActionRow(Button(style=ButtonStyle.green, label='Apply', custom_id='accept'))]
                await interaction.edit(components=components)
            elif isinstance(button_or_select, Button):
                await interaction.edit(components=[c.disable_all_components() for c in interaction.message.components])
                await user.edit(permissions=to_edit, reason=f'{i.author} used the {i.command.name}')
                break

@client.slash_command(base_name='permissions',
                      group_name='role',
                      group_desc='Get or edit permissions for a role.',
                      name='get',
                      option_descriptions={'role': 'The role to show the permissions for.',
                                           'channel': 'he channel permissions to get. If omitted, the guild permissions will be returned.'},
                      guild_ids=[852871920411475968])
async def get_role(i: discord.ApplicationCommandInteraction, role: discord.Role, channel: discord.TextChannel = None):
    """Get permissions for a role."""
    permissions = []
    if channel:
        for name, value in channel.overwrites_for(role):
            if value is None:
                for _name, _value in channel.overwrites_for(i.guild.default_role):
                    if _name == name:
                        value = _value
                        break
                if value is None:
                    value = getattr(i.guild.default_role.permissions, name)
            permissions.append({'name': name, 'value': {True: '✅', False: '❌', None: '⭕'}.get(value)})
        await i.respond(embed=discord.Embed(title=f'Permissions for the Role {role.name} in {channel.name}', description='\n'.join(['{name} |  {value}'.format(**permission) for permission in permissions]), color=role.color, timestamp=datetime.now()).set_footer(text=f'invoked by {i.author}', icon_url=i.author.avatar_url))
    else:
        for name, value in role.permissions:
            permissions.append({'name': name, 'value': {True: '✅', False: '❌', None: '⭕'}.get(value)})
        await i.respond(embed=discord.Embed(title=f'Permissions for the Role {role.name}', description='\n'.join(['{name} |  {value}'.format(**permission) for permission in permissions]), color=role.color, timestamp=datetime.now()).set_footer(text=f'invoked by {i.author}', icon_url=i.author.avatar_url))

@client.slash_command(base_name='permissions',
                      group_name='role',
                      name='edit',
                      option_descriptions={'role': 'The role to edit.',
                                           'channel': 'The channel permissions to edit. If omitted, the guild permissions will be edited.'},
                      guild_ids=[852871920411475968])
@commands.has_permissions(manage_permissions=True)
async def edit_role(i: discord.ApplicationCommandInteraction, role: discord.Role, channel: discord.TextChannel = None):
    """Edit permissions for a role."""
    perms_embed = discord.Embed(description=f'Select/Unselect the Permissions {role.mention} should have {f"in {channel.mention}" if channel else ""}',
                                timestamp=datetime.now())
    # perms_embed.add_field(name='NOTE:', value='If you unselect a permission the default-value would be used')
    permissions_selects = [SelectOption(label=name.replace('_', ' ').upper(), value=name, default=value, description=inspect.cleandoc(getattr(discord.Permissions, name).__doc__)[36:136]) for name, value in (channel.overwrites_for(role) if channel else role.permissions)]
    components = [SelectMenu(custom_id=f'edit_permissions_for_{role.id}', options=options, placeholder=f'Select the Permissions {role} should has/not-has', min_values=0, max_values=len(options)) for options in [permissions_selects[x:x+25] for x in range(0, len(permissions_selects), 25)]] # ja ich mache weirde Sachen xD
    msg = await i.respond(embed=perms_embed, components=[components], hidden=True)
    interaction, select_menu = await client.wait_for('selection_select', check=lambda inter, sm: inter.message.id == msg.id)
    to_edit = discord.PermissionOverwrite()
    for value in select_menu.values:
        to_edit._set(value, True)
    for value in select_menu.not_selected:
        to_edit._set(value, None if channel else False)
    await role.edit(permissions=to_edit, reason=f'{i.author} used the {i.command.name}')

numbers = []
for i in range(2, 43):
    numbers.append(str(i))

@client.slash_command(name='autocomplete', options=[
    CommandOption(option_type=str,
                  name='text',
                  description='A Word to send.',
                  autocomplete=True,
                  ),
    CommandOption(option_type=int,
                  name='number',
                  description='A Number between 2 und 42.',
                  min_value=2,
                  max_value=42,
                  autocomplete=True)])
async def autocomplete_test(i: discord.ApplicationCommandInteraction, text: str, number: int):
    """Just a command to test Auto-completion for options."""
    await i.respond(f'your choice was {number}\n`{text}`.')

@autocomplete_test.autocomplete_callback
async def callback_for_autocomplete_command(i: discord.AutocompleteInteraction, text: option_str = '', number: option_int = 0):
    if text and text.focused:
        suggestion_words = [
            'nothing', 'your', 'hand', 'lag', 'brain', 'is', 'great', 'make', 'made', 'library', 'i',
            'you', 'are', 'big', 'little', 'discord', 'autocomplete', 'suggest', 'my', 'text', 'this',
            'rain', 'python', 'frog', 'water', 'option', 'boy', 'girl', 'creative', 'weird', 'cringe',
            'discord.py', 'discord.py-message-components', 'wrapper', 'education', 'tree',
            *[str(m) for m in i.guild.members]
        ]
        words = text.split(' ')
        choices = []
        for word in suggestion_words:
            if words[-1].lower() in word:
                if len(choices) < 25:
                    t = ' '.join([*words[:-1], (word.capitalize() if ((len(words) >= 2 and words[-2].endswith('.')) or len(words) == 1) else word)])
                    choices.append(SlashCommandOptionChoice(name=t, value=t))
                else:
                    break
        if not choices:
            choices.append(SlashCommandOptionChoice(name=(text.capitalize() if ((len(words) >= 2 and words[-2].endswith('.')) or len(words) == 1) else text), value=text))
        await i.suggest(choices)
    elif number and number.focused:
        choices = [n for n in numbers if str(number) in n][:25]
        await i.suggest([SlashCommandOptionChoice(c, int(c)) for c in choices])
        # print(f'number is focused; the value is {number}.')
    else:
        await i.suggest([SlashCommandOptionChoice('Please enter a value', '0' if i.focused_option_name == 'text' else 0)])
        # print('The focused option hat no value.')

@client.slash_command(name='avatar', guild_ids=[852871920411475968])
async def avatar(i: discord.ApplicationCommandInteraction, member: CommandOption(discord.Member, name='member', description='The Member to get the avatar for.', required=False) = None, default: CommandOption(bool, name='default', description='show only the default avatar', required=False) = False):
    """Get the (guild-)avatar of a member."""
    member: typing.Union[discord.Member, discord.User] = member or i.author
    await i.respond(member.display_avatar_url if not default else member.avatar_url)


@client.slash_command(
    base_name='welcome-screen',
    base_desc='Shows or edit the welcome-screen for this guild.',
    name='show',
    guild_ids=[852871920411475968],
    default_required_permissions=Permissions(manage_guild=True)
)
async def show_welcome_screen(interaction: discord.ApplicationCommandInteraction):
    """Show the Welcome-Screen for this guild."""
    w_c = await interaction.guild.welcome_screen()
    if w_c:
        wc_embed = discord.Embed(title=f'Welcome screen for {interaction.guild}',
                                 description=f'```\n'
                                             f'{w_c.description or "No Description set"}\n'
                                             f'```')
        for channel in w_c.welcome_channels:
            wc_embed.add_field(name=channel.description,
                               value=f'{str(channel.emoji) if channel.emoji else ""} {channel.channel.mention}',
                               inline=False)
        await interaction.respond(embed=wc_embed)
    else:
        await interaction.respond('This guild has no welcome-screen set.', hidden=True)

@client.slash_command(
    base_name='welcome-screen',
    base_desc='Shows or edit the welcome-screen for this guild.',
    group_name='edit',
    group_desc='Edit the welcome-screen for this guild.',
    name='add-channel',
    options=[
        CommandOption(
            option_type=discord.OptionType.channel,
            name='channel',
            description='The channel, for the welcome screen field.',
            channel_types=[discord.TextChannel]),
        CommandOption(
            option_type=str,
            name='description',
            description='The description, for the welcome screen field.'
        ),
        CommandOption(
            option_type=str,
            name='emoji',
            description='The emoji wich shows in front of the channel.',
            required=False
        )
    ],
    guild_ids=[852871920411475968]
)
@commands.has_permissions(manage_guild=True)
async def add_welcome_screen_channel(i: discord.ApplicationCommandInteraction, channel: discord.TextChannel, description: str, emoji: str = None):
    """Add a channel to the Welcome-Screen for this guild."""
    welcome_screen = await i.guild.welcome_screen()
    if emoji:
        try:
            emoji = discord.PartialEmoji.from_string(emoji)
        except ValueError:
            pass

    if len(welcome_screen.welcome_channels) == 5:
        return await i.respond('The maximum of welcome-screen channels is reached, you can\'t add more.')
    channels = welcome_screen.welcome_channels.copy()
    channels.append(discord.WelcomeScreenChannel(channel=channel, description=description, emoji=emoji))
    edited = await welcome_screen.edit(welcome_channels=channels, reason=f'{i.author} used the add-channel command')
    wc_embed = discord.Embed(
        title=f'The Welcome-screen for {i.guild} is now:',
        description=f'```\n'
                    f'{emoji} {edited.description or "No Description set"}\n'
                    f'```'
    )

    for w_channel in edited.welcome_channels:
        wc_embed.add_field(
            name=w_channel.description,
            value=f'{str(w_channel.emoji) if w_channel.emoji else ""} {w_channel.channel.mention}',
            inline=False
        )

    await i.respond(embed=wc_embed)


@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.display_avatar_url != after.display_avatar_url:
        channel = after.guild.get_channel(853000092156035083)
        await channel.send(f'{after.mention} {"guild-" if before.guild_avatar != after.guild_avatar else "user-"}avatar changed\n'
                           f'Before: {before.display_avatar_url}\n'
                           f'After: {after.display_avatar_url}',
                           allowed_mentions=discord.AllowedMentions(users=False))

@client.message_command(name='upload as sticker', guild_ids=[852871920411475968])
@commands.has_permissions(manage_stickers=True)
async def upload_as_sticker(i: discord.ApplicationCommandInteraction, message: discord.Message):
    if not message.attachments or (message.attachments and message.attachments[0].content_type.endswith('image')):
        return await i.respond('This message contains not image', hidden=True)
    else:
        await i.respond('please enter the name, description and tags for the sticker in this format:\n'
                        '_name_\n'
                        '_description_\n'
                        '_tags_\n')
        answer = await client.wait_for('message', check=lambda m: m.author == i.author and m.channel == i.channel)
        name, description, tags = [p for p in answer.content.split('\n') if p.lower() != 'none']
        await message.attachments[0].save(f'./images/{message.attachments[0].filename}')
        sticker = await i.guild.create_sticker(name=name, description=description, tags=tags, file=discord.UploadFile(f'./images/{message.attachments[0].filename}'), reason=f'{i.author} used the {i.command.name} command.')
        await i.respond(f'Successful created the sticker `{name}` with the description `{description}` and tags `{tags}.\n'
                        f'{sticker.image_url}')
        os.remove(f'./images/{message.attachments[0].filename}')
        

async def fetch_all_stickers(ctx):
    stickers = await client.fetch_all_nitro_stickers()
    # await ctx.send('\n'.join(str(sticker_p.banner_url) for sticker_p in stickers))

@client.command()
async def sticker(ctx: commands.Context, *_stickers):
    stickers = []
    for sticker in _stickers:
        stickers.extend([s for s in client.stickers if (sticker.lower() == s.name.lower() or sticker in s.tags) and s.format != discord.StickerType.lottie])
    if stickers and all([sticker.guild_id for sticker in stickers]):
        await ctx.send(content=f'Here {"is the Sticker" if len(stickers) == 1 else "are the Stickers"}.', stickers=stickers)
    else:
        if stickers :
            await ctx.send('\n'.join([str(sticker.image_url) for sticker in stickers]))

@client.slash_command(name='mute',
                      description='🤐 Mutes a Member for a specific time.',
                      option_descriptions={'member': 'The member to mute.',
                                           'months': 'How many months to mute the Member for.',
                                           'days': 'How many days to mute the Member for.',
                                           'hours': 'How many hours to mute the Member for.',
                                           'minutes': 'How many minutes to mute the Member for.',
                                           'reason': 'The reason for muting the Member. Shows up in the audit-log.'
                                           },
                      default_required_permissions=Permissions(administrator=True))
@commands.has_permissions(administrator=True)
async def mute(ctx: discord.ApplicationCommandInteraction,
               member: discord.Member,
               months: int = 0,
               days: int = 0,
               hours: int = 0,
               minutes: int = 0,
               *,
               reason: str = None):
    await ctx.defer()
    now = datetime.now()
    time = datetime(year=now.year,
                    month=now.month + months,
                    day=now.day + days,
                    hour=now.hour + hours,
                    minute=now.minute + minutes,
                    second=now.second)
    try:
        await member.mute(until=time, reason=reason or f'Muted by {ctx.author}({ctx.author.id})')
    except discord.Forbidden:
        return await ctx.respond(embed=discord.Embed(title='🛑 Missing Permissions 🛑',
                                                     description=f'I can\'t mute this Member as he is higher then me.'
                                                                 f'Move my highest role over his highest so that I can mute him.',
                                                     color=discord.Color.red(),
                                                     timestamp=datetime.utcnow()))
    embed = discord.Embed(title='Successful Muted ✅',
                          description=f'{member.mention} was successful muted until {discord.utils.styled_timestamp(time)}'
                                      f'by {ctx.author.mention}.',
                          color=discord.Color.green(),
                          timestamp=datetime.utcnow()
                          )
    if reason:
        embed.add_field(name='Reason:',
                        value=reason,
                        inline=False)
    embed.set_footer(text=f'Invoked by {ctx.author}({ctx.author.id})', icon_url=ctx.author.display_avatar_url)
    await ctx.respond(embed=embed)


@client.slash_command(name='unmute',
                      description='Un-mutes a Member that is muted.',
                      option_descriptions={
                          'member': 'The Member to un-mute.',
                          'reason': 'The reason for un-muting the Member. Shows up in the audit-log.'
                      },
                      default_required_permissions=Permissions(administrator=True))
@commands.has_permissions(administrator=True)
async def unmute(ctx: discord.ApplicationCommandInteraction, member: discord.Member, *, reason: str = None):
    if not member.communication_disabled_until:
        return await ctx.respond(embed=discord.Embed(title='Not muted',
                                                     description=f'The member {member.mention} is not muted.'
                                                                 f' Use `/mute` to mute a member.',
                                                     color=discord.Color.orange(),
                                                     timestamp=datetime.utcnow()))
    await member.edit(communication_disabled_until='', reason=reason or f'Unmuted by {ctx.author}({ctx.author.id})')
    embed = discord.Embed(title='Successful un-muted ✅',
                          description=f'{member.mention} was successful un-muted by {ctx.author.mention}.',
                          color=discord.Color.green(),
                          timestamp=datetime.utcnow()
                          )
    if reason:
        embed.add_field(name='Reason:',
                        value=reason,
                        inline=False)
    embed.set_footer(text=f'Invoked by {ctx.author}({ctx.author.id})', icon_url=ctx.author.display_avatar_url)
    await ctx.respond(embed=embed)

@client.user_command(name='un-mute')
async def unmute_user_command(ctx: discord.ApplicationCommandInteraction, member: discord.Member):
    if not member.communication_disabled_until:
        return await ctx.respond(embed=discord.Embed(title='Not muted',
                                                     description=f'The member {member.mention} is not muted.'
                                                                 f' Use `/mute` to mute a member.',
                                                     color=discord.Color.orange(),
                                                     timestamp=datetime.utcnow()))
    await ctx.respond('Enter the reason for un-muting the Member or `None` to don\'t give one.')
    try:
        reason_msg = await client.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=10)
    except asyncio.TimeoutError:
        reason = None
    else:
        if reason_msg.content.lower() == 'none':
            reason = None
        else:
            reason = reason_msg.content

    await member.edit(communication_disabled_until='', reason=reason or f'Unmuted by {ctx.author}({ctx.author.id})')
    embed = discord.Embed(title='Successful un-muted ✅',
                          description=f'{member.mention} was successful un-muted by {ctx.author.mention}.',
                          color=discord.Color.green(),
                          timestamp=datetime.utcnow()
                          )
    if reason:
        embed.add_field(name='Reason:',
                        value=reason,
                        inline=False)
    embed.set_footer(text=f'Invoked by {ctx.author}({ctx.author.id})', icon_url=ctx.author.display_avatar_url)
    await ctx.respond(embed=embed)

@client.command()
async def is_mute(ctx: commands.Context, member: discord.Member):
    await ctx.send(f'{member.mention} is muted until {discord.utils.styled_timestamp(member.communication_disabled_until)}.' if member.communication_disabled_until else f'{member.mention} is not muted.', allowed_mentions=discord.AllowedMentions(users=False))

@client.command()
async def buttons(ctx):
    msg_with_buttons = await ctx.send('Hey here are some Buttons', components=[[
        Button(label="Hey i\'m a red Button",
               custom_id="red", style=ButtonStyle.red),
        Button(label="Hey i\'m a green Button",
               custom_id="green", style=ButtonStyle.green),
        Button(label="Hey i\'m a blue Button",
               custom_id="blue", style=ButtonStyle.blurple),
        Button(label="Hey i\'m a grey Button",
               custom_id="grey", style=ButtonStyle.grey),
        Button(label="Hey i\'m a URL Button",
               url="https://pypi.org/project/discord.py-message-components",
               style=ButtonStyle.grey_url)
        ]])

    def check_button(i: discord.ComponentInteraction, b: discord.Button):
        return i.author == ctx.author and i.message == msg_with_buttons

    interaction, button = await client.wait_for('button_click', check=check_button)

    embed = discord.Embed(title='You pressed an Button',
                          description=f'You pressed a {button.custom_id} button.',
                          color=discord.Color.random())
    await interaction.respond(embed=embed)


@client.command()
async def _select(ctx):
    rtfd = client.get_emoji(859143812714070046)
    msg = await ctx.send("Hey select something", components=[[SelectMenu(custom_id='select_test', options=[SelectOption('Option 1', '1', '1️⃣', 'option Nr° 1'), SelectOption('Option 2', '2', description='this is the second option'), SelectOption('Read The Docs', 'Read The Docs', emoji=rtfd, description='Yust read the Fucking Docs')], placeholder='Select a Option', min_values=1), Button(label="Close", )]])
    i, s = await client.wait_for('selection_select', check=lambda i, s: i.message == msg)
    if s.values == 'Read The Docs':
        await i.respond('Just read the docs here [https://discordpy-message-components.readthedocs.io/en/latest/](https://www.youtube.com/watch?v=dQw4w9WgXcQ)', hidden=True)
    else:
        await i.respond(embed=discord.Embed(title='you selected something', description=f'Hey {i.author.mention}, you select {s.values}', color=discord.Color.green()))


@client.command()
async def select(ctx):
    msg_with_buttons_and_selects = await ctx.send('Hey here is an nice Select-Menu', components=[[
        Button(emoji='◀', custom_id="back",
               style=ButtonStyle.blurple),
        Button(emoji="▶",
               custom_id="next",
               style=ButtonStyle.blurple)],
        [
            SelectMenu(custom_id='_select_it', options=[
                SelectOption(emoji='1️⃣', label='Option Nr° 1', value='1', description='The first option'),
                SelectOption(emoji='2️⃣', label='Option Nr° 2', value='2', description='The second option'),
                SelectOption(emoji='3️⃣', label='Option Nr° 3', value='3', description='The third option'),
                SelectOption(emoji='4️⃣', label='Option Nr° 4', value='4', description='The fourth option')],
                       placeholder='Select some Options', max_values=3)
        ]])

    def check_selection(i: discord.ComponentInteraction, s):
        return i.author == ctx.author and i.message == msg_with_buttons_and_selects

    interaction, select = await client.wait_for('selection_select', check=check_selection)

    embed = discord.Embed(title='You have chosen:',
                          description=f"You have chosen "+'\n'.join([f'\nOption Nr° {o}' for o in select.values]),
                          color=discord.Color.random())
    await interaction.respond(embed=embed)


@client.command()
async def embeds(ctx):
    embeds = [discord.Embed(title="Hello", description="First Embed", color=discord.Color.blue()), discord.Embed(title="World", description="Second Embed", color=discord.Color.green())]
    msg = await ctx.send(embeds=embeds)
    await asyncio.sleep(5)
    await msg.edit(embeds=[discord.Embed(title="Hello", description="First Embed", color=discord.Color.blue()).set_footer(text="This Embed was edited"), discord.Embed(title="World", description="Second Embed", color=discord.Color.green()).set_footer(text="This Embed was edited")])


@client.command()
async def decorator(ctx):
    await ctx.send('Press the Button below.', components=[[Button(label="Clicke me", custom_id="hello button", style=ButtonStyle.blurple)]])


async def _button(i: discord.ComponentInteraction):
    await i.respond('Yes the decorators works.')


@client.command()
async def roles(ctx):
    options = [
        SelectOption('Updates', '860952540886335508', 'Receive notification of new library-updates.'),
        SelectOption('Surveys ping', '865600429734887456', 'You will be asked about functions for the library.')
    ]
    await ctx.send(embed=discord.Embed(title='Select your Roles below.', color=discord.Color.random()), components=[[SelectMenu(custom_id="choice_roles", options=options, placeholder="Select the roles you would like to receive", max_values=3, min_values=0)]])


@client.command()
async def custom_emoji(ctx):
    await ctx.send('Gehen die auch als string?', components=[Button(emoji='<a:NeverRickRoleme:853981649053941781>', custom_id='this will never be used lol', style=4)])


@client.on_select()
async def choice_roles(interaction: discord.ComponentInteraction, select_menu):
    await interaction.defer()
    roles_to_add = []
    if select_menu.values:
        for _id in select_menu.values:
            role = interaction.guild.get_role(_id)
            if role and role not in interaction.member.roles:
                roles_to_add.append(role)
        if roles_to_add:
            await interaction.author.add_roles(*roles_to_add, reason='Self-Roles')
            await interaction.respond(f"Successful added {', '.join([r.mention for r in roles_to_add])} to you.", hidden=True)
    roles_to_remove = []
    for option in select_menu.all_option_values:
        role = interaction.guild.get_role(option)
        if role and (role in interaction.author.roles) and (role not in roles_to_add):
            roles_to_remove.append(role)
    if roles_to_remove:
        await interaction.author.remove_roles(*roles_to_remove, reason='Self-Roles')
        await interaction.respond(f"Successful removed {', '.join([r.mention for r in roles_to_remove])} from you.", hidden=True)

# the SelectMenu


@client.command()
@commands.is_owner()
async def testle(ctx):
    if not ctx.author.dm_channel:
        await ctx.author.create_dm()
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(ctx.message.jump_url)
    else:

        await ctx.send(embed=discord.Embed(title='hm', description=ctx.author.dm_channel), components=[ActionRow(Button(label='DM', url=f'https://discord.com/channels/@me/{ctx.author.dm_channel.id}'))])


@client.event
async def on_ready():
    print('Beb. Boob.')

@client.command()
async def docs_select_gender(ctx):
    await ctx.send(embed=discord.Embed(title='Choose your Gender below.'), components=[[
        SelectMenu(custom_id='choose_your_gender',
                   options=[
                       SelectOption(label='Female', value='Female', emoji='♀️'),
                       SelectOption(label='Male', value='Male', emoji='♂️'),
                       SelectOption(label='Trans./Non Binary', value='Non Binary', emoji='⚧')
                   ],
                   placeholder='Choose your Gender')
       ]])


# function that's called when the SelectMenu is used
@client.on_select()
async def choose_your_gender(i: discord.ComponentInteraction, select):
    await i.respond(f'You selected `{i.component.values[0]}`!', hidden=True)

@client.command()
async def file(ctx: commands.Context, name: str, *, description: str = None):
    await ctx.send(file=discord.File('./docs/imgs/ict4example.gif', name, description))

@client.slash_command(base_name='test',
                      base_desc='Just something to test',
                      guild_ids=[852871920411475968])
async def main(ctx: discord.ApplicationCommandInteraction):
    """Test stuff."""
    await ctx.respond('This command is in the main.')

@client.on_click(r'callback-[0-9]{16,21}')
async def some_callback(interaction, button):
    re.match(r'callback-[0-9]{16,21}', button.custom_id)


tixte_auth = "3167e71d-f0dd-4490-9010-a1d706cc452a"
tixte_auth_token = 'tx.3mHBIuoOY74SrlPF.jmRqjvhmyItk1Kf1.sAf6J8B5oszemiR0.UVst'


@client.slash_command(
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
        ctx: discord.ApplicationCommandInteraction,
        file: discord.Attachment,
        domain: str = 'my-code.is-from.space',
        name: str = None,
        random_name: bool = False
):
        msg = await ctx.respond(f'uploading file to `{domain}`...')
        form = aiohttp.FormData()
        form.add_field(name='payload_json',
                       value=to_json({"upload_source":"custom","domain": domain.rstrip(), "type": 1, "name": name or file.filename})
                       )
        form.add_field(name='file',
                       content_type=file.content_type,
                       value=(await file.read()))
        async with aiohttp.ClientSession(headers={'Authorization': tixte_auth}) as tixte:
            async with tixte.request('POST', f'https://api.tixte.com/v1/upload?random={"true" if random_name else "false"}', data=form, ssl=False) as resp:
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
async def tixte_domains_getter(interaction: discord.AutocompleteInteraction, *args, **kwargs):
        async with aiohttp.ClientSession(headers={'Authorization': tixte_auth_token,}) as tixte:
            async with tixte.get('https://api.tixte.com/v1/users/@me/domains', ssl=False) as resp:
                data = await resp.json()
        await interaction.suggest([SlashCommandOptionChoice(name=f'{d["name"]} - {d["uploads"]} uploads', value=f'{d["name"]}') for d in data['data']['domains']])


@client.on_click(r'tixte:delete:https://.*')
async def tixte_delete(interaction: discord.ComponentInteraction, button):
        before_embed = interaction.message.embeds[0]
        before_components = interaction.message.components
        msg = await interaction.edit(embed=discord.Embed(title='⚠Warning: ❗This action is not reversible❗⚠',
                                                   description='Are you sure you want to delete this file permanently?'),
                               components=[[Button(label='Yes', custom_id='tixte:delete:yes', style=ButtonStyle.red),
                                            Button(label='No', custom_id='tixte:delete:cancel', style=ButtonStyle.red)]])
        try:
            inter, but = await client.wait_for('button_click', check=lambda i, b: b.custom_id in ['tixte:delete:yes', 'tixte:delete:cancel'], timeout=10)
        except asyncio.TimeoutError:
            await msg.edit(embed=before_embed, components=before_components)
        else:
            if but.custom_id == 'tixte:delete:yes':
                url = re.match(r'tixte:delete:(?P<url>https://.*)', button.custom_id).group('url')
                async with aiohttp.ClientSession(headers={'Authorization': tixte_auth, 'Media-Type': 'application/json'}) as tixte:
                    async with tixte.request('GET', f'{url}?auth={tixte_auth}', ssl=False) as resp:
                        data = await resp.json()
                await inter.edit(embed=discord.Embed(title=data['data']['message'], color=discord.Color.green()), components=[])
            else:
                await inter.edit(embed=before_embed, components=before_components)

from discord import Modal, TextInput
@client.command()
async def interaction_types(ctx):
    components = [ActionRow(
        SelectMenu(
            custom_id='interaction_types_example',
            placeholder='Select a interaction response type to show.',
            options=
            [
                SelectOption('msg_with_source', '4', 'Respond with a message', '4️⃣'),
                SelectOption('deferred_msg_with_source', '5', 'ACK an interaction[...]; user sees a loading state', '5️⃣'),
                SelectOption('deferred_update_msg', '6', 'ACK an interaction[...]; no loading state', '6️⃣'),
                SelectOption('update_msg', '7', 'Edit the message the component was attached to', '7️⃣'),
                SelectOption('show_modal', '9', 'Respond to the interaction by sending a popup modal', '9️⃣')
            ]
        )
    )]

    embed = discord.Embed(title='Interaction Callback Type', description='These are all interaction-callback-types you could use for slash-commands and message-components:', color=discord.Color.green())
    await ctx.send(embed=embed, components=components)

@client.on_select()
async def interaction_types_example(i: discord.ComponentInteraction, s):
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
            Modal(
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
        modal_interaction: discord.ModalSubmitInteraction = await client.wait_for('modal_submit', check=lambda mi: mi.author == i.author)
        embed = discord.Embed(title='This was response type 9', color=discord.Color.green())
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


from typing import Union, Optional, List, Dict, Any
from itertools import chain

def color_dict(obj: Union[Dict[str, Any], Any],
               *,
               highlight: str = None,
               key_color: str = '\033[91m',
               bool_color: str = '\33[94m',
               int_color: str = '\033[34m',
               str_color: str = '\033[93m',
               highlight_color_fg: str = '\033[97m',
               highlight_color_bg: str = '\033[43m',
               __is_key = False) -> Dict[str, Any]:
    if not isinstance(obj, (dict, list, tuple, set)):
        if isinstance(obj, (bool, type(None))):
            c_type = bool_color
            obj = f'{bool_color}{obj}\033[0m'
        elif isinstance(obj, (int, float)):
            c_type = int_color
            obj = f'{int_color}{obj}\033[0m'
        elif isinstance(obj, str):
            c_type = str_color
            if not __is_key:
                obj = f'{str_color}\'{obj}\'\033[0m'
            else:
                obj = f'{key_color}{obj}\033[0m'
        else:
            c_type = '\033[39m'
        if highlight:
            if not isinstance(highlight, (list, tuple, set)):
                highlight = [highlight]
            for to_highlight in highlight:
                obj = str(obj).replace(str(to_highlight), f'{highlight_color_fg}{highlight_color_bg}{to_highlight}\033[49m{c_type}')

        return obj
    else:
        o_type = obj.__class__
        colored_obj = o_type()
        if isinstance(obj, dict):
            for key, value in obj.items():
                colored_obj[color_dict(key, key_color=key_color, bool_color=bool_color, int_color=int_color, str_color=str_color, highlight=highlight, __is_key=True)] = color_dict(value, key_color=key_color, bool_color=bool_color, int_color=int_color, str_color=str_color, highlight=highlight)
        else:
            for value in obj:
                if isinstance(value, (dict, list, tuple)):
                    colored_obj.__iadd__([color_dict(value, key_color=key_color, bool_color=bool_color, int_color=int_color, str_color=str_color, highlight=highlight)])
                else:
                    colored_obj = o_type(chain(colored_obj, [color_dict(value, bool_color=bool_color, int_color=int_color, str_color=str_color, highlight=highlight)]))
        return colored_obj

import json
def color_dumps(obj: Dict[str, Any], highlight: Optional[Union[str, List[str]]] = None, **kwargs):
    return json.dumps(color_dict(obj, highlight=highlight, **kwargs), separators=(', ', '\033[31m:\033[0m '), indent=4).replace('\\u001b', '\033').replace('"', '')

_cogs = [p.stem for p in Path('./cogs').glob('*_cog.py')]
[(client.load_extension(f'cogs.{ext}'), print(f'{ext} was loaded successfully')) for ext in _cogs]

"""for commands in client._guild_specific_application_commands.values():
    for commands_by_type in commands.values():
        for command in commands_by_type.values():
            print(color_dumps(command.to_dict(), highlight=('poll')))"""
"""for commands_by_type in client._application_commands_by_type.values():
    for command in commands_by_type.values():
        print(color_dumps(command.to_dict(), highlight=('autocomplete', 'A')))"""

# exit()
# pprint(client._guild_specific_application_commands[852871920411475968]['chat_input']['upload'])
# print(client._guild_specific_application
#_commands[852871920411475968]['chat_input']['upload'].autocomplete_func)
# from pprint import pprint

# pprint(client._guild_specific_application_commands.values())
# exit()
# loop = asyncio.get_event_loop()
"""for commands in client._guild_specific_application_commands.values():
    for commands_by_type in commands.values():
        for command in commands_by_type.values():
            pprint(f'type: {command.type} name: {command.name}')
            pprint(command.to_dict())

"""
# exit()






client.run('ODYxMjU5NzM5NDcxMTUxMTI0.YOHMow.91MmFGELEfMWBz_wZLIiNAjp0aU')

# client.run('ODUyODczMzc5MDU2ODQ0ODUw.YMNKOw.-r5sxhDroKgvNfz0EbNmVcH65og')
SelectMenu(custom_id='select_example',
           options=[
               SelectOption('The 1. Option', '1', 'The first option you have', '1️⃣'),
               SelectOption('The 2. Option', '1', 'The second option you have', '2️⃣')
           ], placeholder='Select a Option')


async def hello_there(i: discord.ComponentInteraction, button: discord.Button):
    await i.respond(embeds=[discord.Embed(), discord.Embed(), discord.Embed(), discord.Embed(), discord.Embed(), discord.Embed(), discord.Embed()])


@client.on_click('^edit-temp-channel$')
async def edit_temp_channel(ctx: discord.ComponentInteraction, button):
    if not ctx.author.voice:
        return await ctx.respond('You need to be in a temp-channel to use this.', hidden=True)
    channel: discord.VoiceChannel = ctx.author.voice.channel
    if not ctx.author.permissions_in(channel).manage_channels:
        return await ctx.respond('You can\'t use this as you are not the owner of this temp-channel.', hidden=True)
    modal = Modal(
        title='Edit channel',
        custom_id=f'edit-temp-channel-modal:{channel.id}',
        components=[
            [
                TextInput(
                    label='Channel Name',
                    custom_id='channel-name',
                    value=channel.name,
                    placeholder='This value must not be empty',
                    max_length=25,
                    min_length=1
                )
            ],
            [
                TextInput(
                    label='Max members',
                    custom_id='max-channel-members',
                    value=str(channel.user_limit),
                    placeholder='Member limit',
                    max_length=2,
                    min_length=0,
                    required=False
                )
            ]
        ]
    )
    await ctx.respond_with_modal(modal)

@client.on_submit('^edit-temp-channel-modal:\d*$')
async def edit_temp_channel_modal_submit(ctx: discord.ModalSubmitInteraction):
    channel: discord.VoiceChannel = ctx.guild.get_channel(int(ctx.custom_id.split(':')[-1]))
    if not channel:
        return await ctx.respond('This channel does not exist anymore', hidden=True)
    before_name = channel.name
    before_limit = channel.user_limit
    name = ctx.get_field('channel-name').value or channel.name
    limit = ctx.get_field('max-channel-members').value or None
    if limit:
        limit = int(limit)
    if not ctx.author.permissions_in(channel).manage_channels:
        return await ctx.respond('You can\'t use this as you don\'t have the permissions anymore.', hidden=True)
    if before_name == name and before_limit == limit:
        await ctx.respond('Nothing has changed 🤷.', hidden=True)
    else:
        await channel.edit(name=name, user_limit=limit, reason=f'Edited by {ctx.author} by using the control-pannel.')
        updated_embed = discord.Embed(
            title='Successfully updated the channel.',
        )
        if before_name != name:
            updated_embed.add_field(name='Changed name', value=f'From `{before_name}` to `{name}`', inline=False)
        if before_limit != limit:
            updated_embed.add_field(name='Changed user limit', value=f'From `{before_limit}` to `{limit}`', inline=False)
        await ctx.respond(embed=updated_embed, hidden=False)

@client.on_click('^temp-voice-kick-members$')
async def temp_voice_kick_members(ctx: discord.ComponentInteraction, button):
    if not ctx.author.voice:
        return await ctx.respond('You need to be in a temp-channel to use this.', hidden=True)
    channel: discord.VoiceChannel = ctx.author.voice.channel
    if not ctx.author.permissions_in(channel).move_members:
        return await ctx.respond('You can\'t use this as you are not the owner of this temp-channel.', hidden=True)
    if len(channel.members) < 2:
        return await ctx.respond('You can\'t use this as there is nobody to kick out.', hidden=True)
    components = [
        [
            SelectMenu(
                custom_id=f'temp-channel-kick-members-submit:{channel.id}',
                max_values=len(channel.members) - 1,
                options=[
                    SelectOption(label=str(m), value=str(m.id)) for m in channel.members if m.id != ctx.author.id
                ]
            )
        ]
    ]
    await ctx.respond(embed=discord.Embed(title='Select the members that should be kicked'), components=components, hidden=True)

@client.on_select('^temp-channel-kick-members-submit:\d*$')
async def temp_channel_modal_submit(ctx: discord.ComponentInteraction, select: SelectMenu):
    channel: discord.VoiceChannel = ctx.guild.get_channel(int(select.custom_id.split(':')[-1]))
    if not ctx.author.voice and not ctx.author.permissions_in(channel).move_members:
        return await ctx.respond('You need to be in a temp-channel to use this.', hidden=True)
    if not ctx.author.permissions_in(channel).manage_channels:
        return await ctx.respond('You can\'t use this as you don\'t have the permissions anymore.', hidden=True)
    to_kick: List[discord.Member] = [member for member in channel.members if member.id in select.values]
    cant_kick = []
    for m in to_kick:
        if m.top_role > ctx.guild.me.top_role or m.guild_permissions.administrator:
            cant_kick.append(m)
            continue
        try:
            await m.edit(voice_channel=None, reason=f'Kicked by {ctx.author} by using the control-panel.')
        except discord.Forbidden:
            cant_kick.append(m)
    if cant_kick and len(cant_kick) == len(to_kick):
        return await ctx.respond(embed=discord.Embed(
            title='❌❗Kicking failed❗❌',
            description='I can\'t kick any of this member(s) as they are above my highest role.',
            color=discord.Color.red()
        ), hidden=True)
    kicked = len(to_kick) - len(cant_kick)
    kicked_embed = discord.Embed(title=f'Successful kicked {kicked} member{"s" if kicked > 1 else ""}',color=discord.Color.green())
    if len(cant_kick):
        kicked_embed.add_field(
            name=f'❌❗Failed to kick these member{"s" if len(cant_kick) > 1 else ""}❗❌',
            value=f'{", ".join([m.mention for m in cant_kick])}\n'
                  f'**This is usually the case when they are above my highest role.**'
        )
    await ctx.respond(embed=kicked_embed, hidden=True)


