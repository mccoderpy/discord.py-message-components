import re
import types
import pathlib
from collections import namedtuple
from io import StringIO

import os
import sys
import json
import asyncio
from itertools import chain

import aiohttp
from aioconsole import aexec
from typing import Any, Optional, Union, List, Dict

from discord.utils import to_json

import discord
import logging
import datetime as dt
import traceback
from discord.ext import commands
from discord import ActionRow, Button, ButtonStyle, BaseInteraction as Interaction, \
    ApplicationCommandInteraction as APPCI, SelectMenu, SelectOption, \
    SlashCommandOption as Option, OptionType, SlashCommandOptionChoice, Permissions, ApplicationCommandInteraction, \
    AutocompleteInteraction, option_str
from discord import Permissions
from discord import Localizations
from discord import SlashCommandOptionChoice as Choice


datetime = dt.datetime

log = logging.getLogger(__name__)




tixte_auth = "3167e71d-f0dd-4490-9010-a1d706cc452a"
tixte_auth_token = 'tx.3mHBIuoOY74SrlPF.jmRqjvhmyItk1Kf1.sAf6J8B5oszemiR0.UVst'



_callbackMessage = namedtuple(
    '_callbackMessage',
    ('content', 'embed', 'embeds', 'file', 'files', 'components', 'allowed_mentions'),
    defaults=(None, None, None, None, None, None, None),
    module=__name__
)


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


class DeveloperCommands(commands.Cog):
    def __init__(self, bot):
        self.pepy_statistics: Optional[dict] = None
        self.bot: commands.Bot = bot
        self.load_time = datetime.now()

    @commands.command(name='eval', aliases=['run', 'excec', 'excecute'])
    @commands.is_owner()
    async def _eval(self, ctx: commands.Context, *, code: str = ''):
        if 4 >= len(code) >= 2:
            rl = code.rstrip()
        else:
            match = re.search('\n``` *([a-z]{2,4})', code)
            if match:
                rl = match.groups()[0]
                code = code[:-len(rl)]
            else:
                rl = 'py'
            rl = rl.rstrip().lower()
            code.rstrip()
        if not code:
            if ctx.message.attachments:
                code = (await ctx.message.attachments[0].read()).decode('utf-8')
            else:
                return await ctx.reply('You need to enter `code` or upload a file with code to excecute.')
        else:
            code = code.replace('```py\n', '').replace('\n```', '')
            code.rstrip()
        sys.stdout = open(f'./data/file-output/eval-{ctx.message.id}.{rl}', 'w', encoding='utf-8')
        sys.stderr = sys.stdout
        failed = False
        before = [p for p in pathlib.Path('.').glob('*.*') if p.is_file()].copy()
        async with ctx.typing():
            try:
                await asyncio.wait_for(aexec(code, {'ctx': ctx, 'self': self, 'code': code, **locals(), **globals(), **self.bot.cogs}), timeout=20)
            except Exception as exc:
                traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stdout)
                failed = True
        sys.stdout.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        if failed:
            os.rename(f'./data/file-output/eval-{ctx.message.id}.{rl}', f'./data/file-output/eval-{ctx.message.id}.py')
            rl = 'py'
        with open(f'./data/file-output/eval-{ctx.message.id}.{rl}', encoding='utf-8') as fp:
            result = fp.read().strip()
            if rl != 'py':
                result = result.replace('True', 'true').replace('False', 'false').replace('None', 'null').replace('\'', '\"')
        after = [p for p in pathlib.Path('.').glob('*.*') if p.is_file() and (p not in before)]
        for index, p in enumerate(after):
            file = f'{p.stem}'
            if p.suffix:
                file += p.suffix
            after[index] = file
        after = sorted(after, key=lambda f: f[4:])
        if 2000 >= len(result.rstrip()) >= 1:
            await ctx.reply(
                f'```{rl}\n{result.rstrip()}\n```', allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False),
                files=[discord.File(p) for p in after])
        elif len(result.rstrip()) < 1:
            await ctx.reply('```\nNo Output\n```', files=[discord.File(p) for p in after])
        else:
            files = [discord.File(p) for p in after]
            files.append(discord.File(f'./data/file-output/eval-{ctx.message.id}.{rl}', f'Result for the command invoked by {ctx.author}.{rl}'))
            await ctx.reply(files=files, allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False))
        os.remove(f'./data/file-output/eval-{ctx.message.id}.{rl}')
        for file in after:
            os.remove(file)

    @_eval.error
    async def eval_error(self, ctx, exc):
        if not isinstance(exc, commands.NotOwner):
            try:
                file = f'./data/file-output/eval-{ctx.message.id}.py'
                with open(file, 'r') as fp:
                    before = fp.read()
                with open(file, 'w+') as fp:
                    traceback.print_exception(type(exc), exc, exc.__traceback__, file=fp)
                    large = bool(len(fp.read().rstrip()) > 2000)
                    if not large:
                        before = fp.read()[len(before):]
                if large:
                    await ctx.reply(file=discord.File(file))
                else:
                    await ctx.reply(f'```py\n{exc}\n\r{before.rstrip()}\n```')
                os.remove(file)
            except Exception as exc:
                try:
                    f = StringIO()
                    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
                    f = f.writelines(tb)
                except Exception as exc:
                    raise exc
            finally:
                [os.remove(f'./data/file-output/{file}') for file in os.listdir('./data/file-output/')]

    @commands.command(name="reload", description="reloads an Cog")
    @commands.is_owner()
    async def reload(self, ctx, *, cog: str):
        try:
            self.bot.reload_extension(f'cogs.{cog}')
            print(f"reloaded Cog {cog}.py")
            await ctx.send(f"The Cog `{cog}` has been successful reloaded", delete_after=20)
        except commands.ExtensionNotLoaded:
            await ctx.send(f"There is no Extension with the Name `{cog}` loaded", delete_after=20)
        except Exception:
            with open("./data/error.py", "w") as error:
                error.write(f"Es ist folgender Fehler beim Versuch den Cog {cog} neu zuladen aufgetreten:\n\n")
                traceback.print_exc(file=error)
            await ctx.send(file=discord.File(fp="./data/error.py"))
        await ctx.message.delete()

    @commands.Cog.slash_command(name='eval',
                       description='executes a python code',
                       guild_ids=[852871920411475968, 823982544235135016],
                       options=[
                           Option(name='code',
                                         description='The Code to execute. Only Python 3 Code supportet.',
                                         option_type=str,
                                         required=False),
                           Option(name='response-markup',
                                         description='The markup to be used for the response (e.g. json, html, etc.) default: py',
                                         option_type=str,
                                         required=False),
                           Option(name='ephemeral',
                                         description='Whether the answer should only be visible to you',
                                         option_type=bool,
                                         required=False),
                           Option(name='file',
                                         description='The file to execute. Only Python 3 Code supportet.',
                                         option_type=discord.OptionType.attachment,
                                         required=False),
                       ],
                       connector={
                           'response-markup': 'rl'
                       })
    async def slash_eval(self, ctx: APPCI, code: str = '', rl: str = 'py', ephemeral: bool = False, file: 'discord.Attachment' = None):
        try:
            __callback = discord.embeds.EmbedProxy(_callbackMessage()._asdict()) # type: ignore
            await ctx.defer(hidden=ephemeral)
            match = re.search('\n```([a-z]{2,4})', code)
            if match:
                rl = match.groups()[0]
                code = code[:-len(rl)]
                rl = rl.rstrip().lower()
                code.rstrip()
            if not code:
                if file:
                    code = (await file.read()).decode('utf-8')
                else:
                    return await ctx.respond('You need to provide **`code`** or upload a file using the **`file`** parameter.', delete_after=10)
            else:
                if code.startswith('```py\n'):
                    code = code[6:]
                elif code.startswith('```'):
                    code = code[3:]
                if code.endswith('\n```'):
                    code = code[:-4]
                code.rstrip()
            sys.stdout = open(f'./data/file-output/eval-{ctx.id}.{rl}', 'w', encoding='utf-8')
            sys.stderr = sys.stdout
            failed = False
            before = [p for p in pathlib.Path('.').glob('*.*') if p.is_file()].copy()
            try:
                await asyncio.wait_for(aexec(code, {'ctx': ctx, 'self': self, 'code': code, 'callback': __callback, **locals(), **globals(), **self.bot.cogs}), timeout=20)
            except Exception as exc:
                traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stdout)
                failed = True
            sys.stdout.close()
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            if failed:
                os.rename(f'./data/file-output/eval-{ctx.id}.{rl}',
                          f'./data/file-output/eval-{ctx.id}.py')
                rl = 'py'
            with open(f'./data/file-output/eval-{ctx.id}.{rl}', encoding='utf-8') as fp:
                result = fp.read().strip()
                if rl != 'py':
                    result = result.replace('True', 'true').replace('False', 'false').replace('None', 'null').replace('\'', '\"')
            after = [p for p in pathlib.Path('.').glob('*.*') if p.is_file() and (p not in before)]
            for index, p in enumerate(after):
                file = f'{p.stem}'
                if p.suffix:
                    file += p.suffix
                after[index] = file
            after = sorted(after, key=lambda f: f[4:])
            callback_msg_fields = {k: v for k, v in __callback.__dict__.items() if v is not None}
            if 2000 >= len(result.rstrip()) >= 1:
                await ctx.respond(
                    f'```{rl}\n{result}\n```',
                    allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False,
                                                             replied_user=False),
                    files=[discord.File(p) for p in after])
            elif len(result.rstrip()) < 1:
                await ctx.respond(
                    '```\nNo Output\n```',
                    files=[discord.File(p) for p in after],
                    **callback_msg_fields
                )
            else:
                files = [discord.File(p) for p in after]
                files.append(discord.File(f'./data/file-output/eval-{ctx.id}.{rl}',
                                          f'Result for the command invoked by {ctx.author}.{rl}'))
                await ctx.respond(
                    files=files,
                    allowed_mentions=discord.AllowedMentions.none(),
                    **callback_msg_fields
                )
            os.remove(f'./data/file-output/eval-{ctx.id}.{rl}')
            for file in after:
                os.remove(file)
        except Exception as exc:
            try:
                file = f'./data/file-output/eval-{ctx.id}.py'
                with open(file, 'r') as fp:
                    before = fp.read()
                with open(file, 'w+') as fp:
                    traceback.print_exception(type(exc), exc, exc.__traceback__, file=fp)
                    large = bool(len(fp.read().rstrip()) > 2000)
                    if not large:
                        before = fp.read()[len(before):]
                if large:
                    await ctx.respond(file=discord.File(file))
                else:
                    await ctx.respond(f'```py\n{exc}\n{before.rstrip()}\n```')
                os.remove(file)
            except Exception as exc:
                try:
                    f = StringIO()
                    tb = traceback.format_exception(type(exc),exc, exc.__traceback__)
                    f = f.writelines(tb)
                    await asyncio.wait_for(ctx.respond(file=discord.File(f)), timeout=10)
                    del f
                except asyncio.TimeoutError:
                    pass
                except Exception as exc:
                    raise exc
            finally:
                [os.remove(f'./data/file-output/{file}') for file in os.listdir('./data/file-output/')]

    @commands.command()
    @commands.is_owner()
    async def log(self, ctx):
        await ctx.send(file=discord.File('./data/output-log.log'))
        # emojis = ''; [(emojis.__add__(str(e))) for e in self.bot.emojis if (len(emojis) + len(str(e)) < 2000)]; print(emojis)

    @commands.command()
    @commands.is_owner()
    async def console(self, ctx):
        # from _io import StringIO
        await ctx.send(sys.stdout)

    @commands.command()
    @commands.is_owner()
    async def clearcmdchannel(self, ctx: commands.Context, guild: Union[discord.Guild, int], channel: Union[discord.TextChannel, int], amount: int = 100):
        if isinstance(guild, int):
            guild = self.bot.get_guild(guild)
        if isinstance(channel, int):
            channel = guild.get_channel(channel)
        await channel.purge(limit=amount, check=lambda m: m.author.id != self.bot.user.id and (not m.pinned))

    @commands.Cog.slash_command(
        name='clear',
        description='Deletes the last x messages in the chat.',
        description_localizations=Localizations(german='Löscht die letzten x Nachrichten im Chat.'),
        default_required_permissions=Permissions(manage_messages=True),
        options=[
            Option(
                option_type=int,
                name='count',
                description='The number (x) of messages that should be deleted.',
                description_localizations=Localizations(german='Wie viele (x) Nachrichten gelöscht werden sollen.'),
                max_value=100,
                min_value=2
            ),
            Option(
                option_type=discord.Member,
                name='member',
                description='The member wich last x messages should be deleted.',
                description_localizations=Localizations(
                    german='Der Member dessen letzten x Nachrichten gelöscht werden sollen.'
                ),
                required=False
            ),
            Option(
                option_type=str,
                name='members',
                description='Separated by a , the member wich last x messages should be deleted. Separated by a ,',
                description_localizations=Localizations(
                    german='Per , getrennt, die Member deren letzten x Nachrichten gelöscht werden sollen.'
                ),
                required=False,
                converter=commands.Greedy[discord.Member]
            ),
            Option(
                option_type=str,
                name='before',
                name_localizations=Localizations(german='vor'),
                description='If specified, the last x messages before this message are deleted.',
                description_localizations=Localizations(
                    german='Wenn angegeben werden die letzten x Nachrichten nach dieser Nachricht gelöscht.'
                ),
                required=False,
                converter=commands.MessageConverter
            ),
            Option(
                option_type=str,
                name='after',
                name_localizations=Localizations(german='nach'),
                description='If specified, the last x messages after this message are deleted.',
                description_localizations=Localizations(
                    german='Wenn angegeben werden die letzten x Nachrichten vor dieser Nachricht gelöscht.'
                ),
                required=False,
                converter=commands.MessageConverter
            ),
            Option(
                option_type=str,
                name='reason',
                name_localizations=Localizations(german='grund'),
                description='The reason for deleting message are deleted.',
                description_localizations=Localizations(
                    german='Der Grund warum die Nachrichten gelöscht werden.'
                ),
                required=False,
            )

        ],
        guild_ids=[852871920411475968])
    async def clear(self,
                    ctx: APPCI,
                    count: int,
                    member: discord.Member = None,
                    members: Optional[List[discord.Member]] = [],
                    before: discord.Message = None,
                    after: discord.Message = None,
                    reason: str = None,
                    around: discord.Message = None):
        if not ctx.author.permissions_in(ctx.channel).manage_messages:
            return
        if members and len(members) == 1 and member == members[0]:
            member = members[0]
        question = await ctx.respond(
            embed=discord.Embed(
                title=f"deleting messages",
                description=f'[{ctx.author.mention}]\n are you sure to delete the'
                            f' last {count} messages {f"from {member.mention}" if member else (f"{len(members)} members" if members else "in this Channel")}?',
                color=discord.Color.red()),
            components=[
                [
                    discord.Button(
                        label="Yes",
                        emoji="✅",
                        style=discord.ButtonColor.green,
                        custom_id="Yes"
                    ),
                    discord.Button(
                        label="No",
                        emoji="❌",
                        style=discord.ButtonColor.red,
                        custom_id="No"
                    )
                ]
            ]
        )

        def check(i: discord.ComponentInteraction, b: discord.Button):
            return i.message.id == question.id and i.author.id == ctx.author.id

        try:
            i, b = await self.bot.wait_for("button_click", check=check, timeout=10)
            await i.defer()
            if b.custom_id == 'Yes':
                await question.delete()

                def check_params(m: discord.Message):
                    if member:
                        if m.author.id == member.id: return True
                    else:
                        if members:
                            if m.author in members: return True
                        else:
                            return True

                deleted = await ctx.channel.purge(limit=count, check=check_params, before=before, after=after,
                                                  around=around)
                deleted_from = []
                for m in deleted:
                    if m.author not in deleted_from:
                        deleted_from.append(m.author)
                m_count = len(deleted_from)
                embed = discord.Embed(
                    description=f'Deleted `{len(deleted)}` messages from {m_count} member{"s" if m_count > 1 else ""}| {discord.utils.styled_timestamp(datetime.now(), "R")}',
                    color=discord.Color.green()
                )
                if reason:
                    embed.add_field(name='Reason:', value=f'```\n{reason}\n```', inline=False)
                embed.add_field(
                    name='Deleted messages from:',
                    value=', '.join([m.mention for m in deleted_from])
                )
                await i.channel.send(embed=embed)
            else:
                await question.delete()
        except asyncio.TimeoutError:
            await question.delete()

    @commands.Cog.slash_command(
        name="reload",
        description="reloads a Cog",
        description_localizations=Localizations(german='Läd einen Cog neu'),
        default_required_permissions=8,
        options=[
            Option(
                name="cog",
                description="The Cog to reload",
                description_localizations=Localizations(german='Der Cog, der neu geladen werden soll'),
                option_type=str,
                autocomplete=True
            ),
            Option(
                name='sync-commands',
                description='Whether slash-commands should be updated; default False',
                description_localizations=Localizations(
                    german='Ob Slash-Commands synchronisiert werden sollen; standardgemäß False'),
                option_type=bool,
                required=False
            )
        ],
        connector={'sync-commands': 'sync_slash_commands'}
    )
    @commands.is_owner()
    async def reload(self, ctx, cog: str, sync_slash_commands: bool = False):
        before = getattr(self.bot, 'sync_commands_on_cog_reload', False)
        self.bot.sync_commands_on_cog_reload = sync_slash_commands
        await ctx.defer(hidden=True)
        try:
            self.bot.reload_extension(f'cogs.{cog}')
            log.info(f"reloaded Cog \033[32m{cog}\033[0m")
            await ctx.respond(
                f"The Cog `{cog}` has been successful reloaded{' and the slash-commands synced.' if sync_slash_commands is True else '.'}",
                hidden=True)
        except commands.ExtensionNotLoaded:
            await ctx.respond(f"There is no extension with the Name `{cog}` loaded", hidden=True)
        except Exception:
            with open("error.py", "w") as error:
                error.write(f"Es ist folgender Fehler beim Versuch den Cog {cog} neu zuladen aufgetreten:\n\n")
                traceback.print_exc(file=error)
            await ctx.respond(file=discord.File(fp="error.py"))
            os.remove('error.py')
        self.sync_commands_on_cog_reload = before

    @reload.autocomplete_callback
    async def reload_cog_autocomplete(self, i, cog: str = None, sync_slash_commands: bool = False):
        if cog:
            await i.suggest(
                [Choice(name, c.__init__.__globals__['__file__'].split('\\')[-1].replace('.py', '')) for name, c in
                 self.bot.cogs.items() if (name.lower().startswith(cog.lower()) or c.__init__.__globals__['__file__'].split('\\')[-1].lower().startswith(cog.lower()))])
        else:
            await i.suggest(
                [Choice(name, c.__init__.__globals__['__file__'].split('\\')[-1].replace('.py', '')) for name, c in
                 self.bot.cogs.items()])

    """@commands.Cog.slash_command(name='upload',
                                description='Uploads the given file(s) to mccubers\' Tixte account.',
                                guild_ids=[852871920411475968],
                                options=[Option(option_type=OptionType.attachment,
                                                            name='file',
                                                            description='The file to upload'),
                                         Option(option_type=str,
                                                            name='domain',
                                                            description='Select a domain where the file should be uploaded to.',
                                                            autocomplete=True,
                                                            required=False),
                                         Option(option_type=str,
                                                            name='name',
                                                            description='Optional: The new filename',
                                                            required=False))

    @commands.is_owner()"""
    async def tixte_upload(self,
                     ctx: discord.ApplicationCommandInteraction,
                     file: discord.Attachment,
                     domain: str = 'mccoder-py-needs.to-sleep.xyz',
                     name: str = None):
        msg = await ctx.respond(f'uploading file to {domain}...', hidden=True)
        form = aiohttp.FormData()
        form.add_field(name='payload_json',
                       value=to_json({"upload_source":"custom","domain": domain.rstrip(), "type": 1, "name": name or file.filename})
                       )
        form.add_field(name='file',
                       content_type=file.content_type,
                       value=(await file.read()))
        async with aiohttp.ClientSession(headers={'Authorization': tixte_auth}) as tixte:
            async with tixte.request('POST', 'https://api.tixte.com/v1/upload?random=false', data=form, ssl=False,) as resp:
                data = await resp.json()

        if not data['success'] == True:
            return await msg.edit(content=f'```json\n{data["error"]["message"]}\n```')

        embed = discord.Embed(title=data['data']['message'], description=f'Here is your file: {data["data"]["url"]}')
        embed.set_image(url=data['data']['direct_url'])
        await msg.edit(embed=embed,
                       components=[[
                           Button(label='open in browser',
                                  url=data['data']['url']),
                           Button(label='delete file',
                                  custom_id=f'tixte:delete:{data["data"]["deletion_url"].split("?")[0]}',
                                  style=ButtonStyle.red,
                                  emoji='🗑️')
                       ]])

    #@tixte_upload.autocomplete_callback
    async def tixte_domains_getter(self, interaction: discord.AutocompleteInteraction, *args, **kwargs):
        print('Es geht')
        async with aiohttp.ClientSession(headers={'Authorization': tixte_auth_token}) as tixte:
            async with tixte.post('https://api.tixte.com/v1/users/@me/domains', ssl=False) as resp:
                data = await resp.json()
        print(data)
        await interaction.suggest([SlashCommandOptionChoice(name=f'{d["name"]} Uploads: {data["uploads"]}', value=f'{d["name"]}') for d in data['data']['domains']])

    # print(tixte_upload.autocomplete_func)

    #@commands.Cog.on_click(r'tixte:delete:(yes|cancel)')
    async def tixte_delete(self, interaction: discord.ComponentInteraction, button):
        before_embed = interaction.message.embeds[0]
        before_components = interaction.message.components
        msg = await interaction.edit(embed=discord.Embed(title='⚠Warning: ❗This action is not reversible❗⚠',
                                                   description='Are you sure you want to delete this file permanently?'),
                               components=[[Button(label='Yes', custom_id='tixte:delete:yes', style=ButtonStyle.red),
                                            Button(label='No', custom_id='tixte:delete:cancel', style=ButtonStyle.red)]])
        try:
            inter, but = await self.bot.wait_for('button_click', check=lambda i, b: i.message == interaction.message and b.custom_id in ['tixte:delete:yes', 'tixte:delete:cancel'], timeout=10)
        except asyncio.TimeoutError:
            pass
            # await msg.edit(embed=before_embed, components=before_components)
        else:
            if but.custom_id == 'tixte:delete:yes':
                url = re.search(r'tixte:delete:(?P<url>[.*])', button.custom_id).group('url')
                async with aiohttp.ClientSession(headers={'Authorization': tixte_auth}) as tixte:
                    async with tixte.request('GET', f'{url}?auth={tixte_auth}', ssl=False) as resp:
                        data = await resp.json()
                print(data)
                await inter.edit(embed=discord.Embed(title='✅File was successful deleted✅', color=discord.Color.green), components=[])
            else:
                await inter.edit(embed=before_embed, components=before_components)

    @commands.Cog.slash_command(
        name='statistics',
        description='Get the PyPI download statistics for the library',
        description_localizations=Localizations(german='Rufe die Statistiken für die Library auf'),
        options=[
            Option(
                option_type=str,
                name='version',
                description='For wich version the statistics should be displayed for.',
                description_localizations=Localizations(
                    german="Für welche Versionen die Statistiken angezeigt werden sollen."
                ),
                autocomplete=True,
                requiered=False
            ),
            Option(
                option_type=str,
                name='from',
                description='For wich day the statistics should be displayed for.',
                description_localizations=Localizations(
                    german="Für welche Tag die Statistiken angezeigt werden sollen."
                ),
                autocomplete=True,
                requiered=False
            )
        ],
        connector={
            'from': '_from'
        }
    )
    async def show_statistics(self, ctx: ApplicationCommandInteraction, version: str = 'all', _from: str = 'last_day'):
        if not (statistics := self.pepy_statistics):
            async with aiohttp.ClientSession(headers={'Content-Type': 'application/json'}) as session:
                async with session.get('https://api.pepy.tech/api/v2/projects/discord.py-message-components') as resp:
                    resp.raise_for_status()
                    self.pepy_statistics = statistics = json.loads(await resp.text())
        if _from == 'last_day':
            all_downloads = [{k: v} for k, v in statistics['downloads'].items()][-1]
        else:
            all_downloads = statistics['downloads']
        if version != 'all' and _from != 'last_day' and version not in all_downloads:
            try:
                return await ctx.respond(f'There are no statistics for this version on <t:{int(datetime.fromisoformat(_from).timestamp()+43200)}:D>.', hidden=True)
            except:
                return await ctx.respond(f'`{_from}` is not a valid date.', hidden=True)
        statistics_embed = discord.Embed(
            title='Total statistics' if _from == 'total' else f'Statistics from {f"<t:{int(datetime.fromisoformat(_from).timestamp()+43200)}:D>" if _from != "last_day" else f"<t:{int(datetime.fromisoformat(list(all_downloads)[0]).timestamp()+43200)}:D>"}',
            description=f'Here are the download statistics from [PyPI](https://pypi.org/discord.py-message-components) for {"version" if version != "all" else "all"} {version if version != "all" else "versions"}.',
            color=discord.Color.green()
        )
        if version != "all":
            all_downloads = {day: {v: download_count for v, download_count in downloads.items() if v == version} for day, downloads in all_downloads.items()}
        all_downloads[list(all_downloads.keys())[0]]['Total'] = f'{sum([sum([count for count in counts.values()]) for counts in all_downloads.values()])}\n'
        if _from == 'total':
            versions = {}
            for day, downloads in all_downloads.items():
                for v, download_count in downloads.items():
                    try:
                        versions[v] += download_count
                    except KeyError:
                        versions[v] = download_count
            versions = dict(sorted(versions.items(), key=lambda c: c, reverse=True))
            statistics_embed.add_field(
                name=f'Total downloads per version from <t:{int(datetime.fromisoformat(list(all_downloads)[0]).timestamp()+43200)}:R> to <t:{int(datetime.fromisoformat(list(all_downloads)[-1]).timestamp()+43200)}:R>:',
                value='\n'.join([f'**{v}:** `{count}`' for v, count in versions.items()]),
                inline=False
            )
        else:
            statistics_embed.add_field(
                name=f'Downloads from <t:{int(datetime.fromisoformat(list(all_downloads)[0]).timestamp()+43200)}:R>:',
                value='\n'.join([f'**{v}:** `{count}`' for v, count in dict(sorted(all_downloads[list(all_downloads)[0]].items(), key=lambda c: c, reverse=True)).items()]),
                inline=False
            )
        statistics_embed.add_field(
            name='Total downloads:',
            value=f'`{statistics["total_downloads"]}`',
            inline=False
        )
        await ctx.respond(embed=statistics_embed)
        self.pepy_statistics = None

    @show_statistics.autocomplete_callback
    async def get_versions(self, ctx: AutocompleteInteraction, version: option_str = '', _from: option_str = ''):
        if not (statistics:= self.pepy_statistics):
            async with aiohttp.ClientSession(headers={'Content-Type': 'application/json'}) as session:
                async with session.get('https://api.pepy.tech/api/v2/projects/discord.py-message-components') as resp:
                    resp.raise_for_status()
                    self.pepy_statistics = statistics = json.loads(await resp.text())
        if ctx.focused_option_name == 'version':
            if not version:
                version = ''
            versions = statistics['versions']
            await ctx.send_choices([Choice('all', 'all')] + [Choice(v, v) for v in versions if version in v][:24])
        else:
            if not _from:
                _from = ''
            days = [Choice('last', 'last_day'), Choice('total', 'total')]
            days.extend([Choice(day, day) for day in statistics['downloads'] if _from in day])
            await ctx.send_choices(days[:25])

    def _reload_module(self, module: str):
        import importlib
        m: types.ModuleType = globals().get(module, locals().get(module, None))
        if m:
            return importlib.reload(m)
        else:
            raise ModuleNotFoundError(f'there is no Module `{module}` loaded')


def setup(bot):
    bot.add_cog(DeveloperCommands(bot))