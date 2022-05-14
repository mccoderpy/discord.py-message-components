import re
import types
import typing
import pathlib
from io import StringIO

import os
import sys
import asyncio

import aiohttp
from discord.utils import to_json

import discord
import logging
import datetime as dt
import traceback
from discord.ext import commands
from discord import ActionRow, Button, ButtonStyle, BaseInteraction as Interaction, SelectMenu, SelectOption, \
    SlashCommandOption, OptionType, SlashCommandOptionChoice

datetime = dt.datetime


def log():
    return logging.getLogger(__name__)


from aioconsole import aexec

tixte_auth = "3167e71d-f0dd-4490-9010-a1d706cc452a"
tixte_auth_token = 'tx.3mHBIuoOY74SrlPF.jmRqjvhmyItk1Kf1.sAf6J8B5oszemiR0.UVst'


class DeveloperCommands(commands.Cog):
    def __init__(self, bot):
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
                       guild_ids=[852871920411475968],
                       options=[
                           SlashCommandOption(name='code',
                                         description='The Code to execute. Only Python 3 Code supportet.',
                                         option_type=str,
                                         required=False),
                           SlashCommandOption(name='response-markup',
                                         description='The markup to be used for the response (e.g. json, html, etc.) default: py',
                                         option_type=str,
                                         required=False),
                           SlashCommandOption(name='ephemeral',
                                         description='Whether the answer should only be visible to you',
                                         option_type=bool,
                                         required=False),
                           SlashCommandOption(name='file',
                                         description='The file to execute. Only Python 3 Code supportet.',
                                         option_type=discord.OptionType.attachment,
                                         required=False),
                       ],
                       connector={
                           'response-markup': 'rl'
                       })
    async def slash_eval(self, ctx: Interaction, code: str = '', rl: str = 'py', ephemeral: bool = False, file: 'discord.Attachment' = None):
        try:
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
                    await ctx.respond('You need to provide code or upload a code-file using the `file` parameter.')
                    return
            else:
                if code.startswith('```py\n'):
                    code = code[6:]
                if code.startswith('```'):
                    code = code[3:]
                if code.endswith('\n```'):
                    code = code[:-4]
                code.rstrip()
            sys.stdout = open(f'./data/file-output/eval-{ctx.id}.{rl}', 'w', encoding='utf-8')
            sys.stderr = sys.stdout
            failed = False
            before = [p for p in pathlib.Path('.').glob('*.*') if p.is_file()].copy()
            try:
                await asyncio.wait_for(aexec(code, {'ctx': ctx, 'self': self, 'code': code, **locals(), **globals(), **self.bot.cogs}), timeout=20)
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
            if 2000 >= len(result.rstrip()) >= 1:
                await ctx.respond(
                    f'```{rl}\n{result}\n```',
                    allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False,
                                                             replied_user=False),
                    files=[discord.File(p) for p in after])
            elif len(result.rstrip()) < 1:
                await ctx.respond('```\nNo Output\n```', files=[discord.File(p) for p in after])
            else:
                files = [discord.File(p) for p in after]
                files.append(discord.File(f'./data/file-output/eval-{ctx.id}.{rl}',
                                          f'Result for the command invoked by {ctx.author}.{rl}'))
                await ctx.respond(files=files,
                               allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False,
                                                                        replied_user=False))
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
    async def clearcmdchannel(self, ctx: commands.Context, guild: typing.Union[discord.Guild, int], channel: typing.Union[discord.TextChannel, int], amount: int = 100):
        if isinstance(guild, int):
            guild = self.bot.get_guild(guild)
        if isinstance(channel, int):
            channel = guild.get_channel(channel)
        await channel.purge(limit=amount, check=lambda m: m.author.id != self.bot.user.id and (not m.pinned))

    """@commands.Cog.slash_command(name='upload',
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

    # @commands.Cog.listener()
    async def on_interaction_create(self, data):
        __import__('pprint').pprint(data)

    def _reload_module(self, module: str):
        import importlib
        m: types.ModuleType = globals().get(module, locals().get(module, None))
        if m:
            return importlib.reload(m)
        else:
            raise ModuleNotFoundError(f'there is no Module `{module}` loaded')


def setup(bot):
    bot.add_cog(DeveloperCommands(bot))
