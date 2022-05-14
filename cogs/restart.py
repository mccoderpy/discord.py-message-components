import __future__
import inspect
import os
import sys
import types
import typing
import asyncio
import discord
import logging
import datetime as dt
import traceback
from discord.ext import commands
from discord import ActionRow, Button, ButtonStyle, BaseInteraction as Interaction, SelectMenu, SelectOption

datetime = dt.datetime

def log():
    return logging.getLogger(__name__)
from pathlib import Path
import discord_slash.model
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_permission, create_option
from discord_slash.utils.manage_commands import create_choice as cc



def GetHumanReadable(size, precision=2):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    suffixIndex = 0
    while size > 1024 and suffixIndex < 4:
        suffixIndex += 1  # increment the index of the suffix
        size = size/1024.0  # apply the division
    return "%.*f%s" % (precision, size, suffixes[suffixIndex])

from types import ModuleType, FunctionType
from gc import get_referents

# Custom objects know their class.
# Function objects seem to know way too much, including modules.
# Exclude modules as well.
BLACKLIST = type, ModuleType, FunctionType


def get_size(obj, no_bot: bool = False):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError('get_size() does not take argument of type: '+ str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and (not isinstance(obj, (commands.Bot, discord.Client)) if no_bot else True) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size


class RestartCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_time = datetime.now()

    @cog_ext.cog_slash(name="reload",
                       description="reloads an Cog",
                       default_permission=False,
                       permissions={852871920411475968:
                                        [create_permission(693088765333471284, 2, True)],
                                    720395641255100528:
                                        [create_permission(693088765333471284, 2, True)],
                                    879815586484486175:
                                        [create_permission(693088765333471284, 2, True)]
                                    },
                       options=[create_option(name="cog", description="The Cog to reload", option_type=3, required=True,
                                              choices=[
                                                  cc("music", "music"),
                                                  cc("praktisches","praktisches"),
                                                  cc("help", "help"),
                                                  cc("autorole", "auto-role"),
                                                  cc("restart", "restart"),
                                                  cc('developer-commands_cog', 'developer-commands')
                                              ]
                                              ),
                                create_option(name='sync-commands',
                                              description='Whether slash-commands should be updated; default False',
                                              option_type=bool,
                                              required=False)
                                ],
                       connector={
                           'sync-commands': 'sync_slash_commands'
                       }
                       )
    @commands.is_owner()
    async def reload(self, ctx, cog: str, sync_slash_commands: bool = False):
        before = self.bot.slash.sync_on_cog_reload
        self.bot.slash.sync_on_cog_reload = sync_slash_commands
        await ctx.defer(hidden=True)
        try:
            self.bot.reload_extension(f'bot.cogs.{cog}')
            print(self.bot.time(), f"reloaded Cog \033[91m{cog}\033[0m")
            await ctx.send(f"The Cog `{cog}` has been successful reloaded{' and the slash-commands synced.' if sync_slash_commands is True else '.'}", hidden=True)
        except commands.ExtensionNotLoaded:
            await ctx.send(f"There is no Extension with the Name `{cog}` loaded", hidden=True)
        except Exception:
            with open("./data/error.py", "w") as error:
                error.write(f"Es ist folgender Fehler beim Versuch den Cog {cog} neu zuladen aufgetreten:\n\n")
                traceback.print_exc(file=error)
            await ctx.send(file=discord.File(fp="./data/error.py"))
        self.bot.slash.sync_on_cog_reload = before


    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, *,  name):
        try:
            self.bot.load_extension(name=f'bot.cogs.{name}')
            print(self.bot.time(), f"loaded Cog `{name}.py`")
            await ctx.send(f"The Cog `{name}` has been successful loaded", delete_after=20)
        except commands.ExtensionNotFound:
            await ctx.send(f"There is no Extension with the Name `{name}` found in `{Path('.').absolute()}\\bot\\cogs`")
        except Exception:
            with open("./data/error.py", "w") as error:
                error.write(f"'Es ist folgender Fehler beim Versuch den Cog `{name}` zu laden aufgetreten:'\n\n")
                traceback.print_exc(file=error)
            await ctx.send(file=discord.File(fp="./data/error.py"))
        await ctx.message.delete()

    @load.error
    async def load_cog_error(self, ctx, args):
        pass

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, *, name):
        try:
            self.bot.unload_extension(name=f'bot.cogs.{name}')
            print(self.bot.time(), f"loaded Cog `{name}.py`")
            await ctx.send(f"The Cog `{name}` has been successful unloaded", delete_after=20)
        except commands.ExtensionNotLoaded:
            await ctx.send(f"There is no Extension with the Name `{name}` unloaded.", delete_after=20)
        except Exception:
            with open("./data/error.py", "w") as error:
                error.write(f"'Es ist folgender Fehler beim Versuch den Cog `{name}` zu entladen aufgetreten:'\n\n")
                traceback.print_exc(file=error)
            await ctx.send(file=discord.File(fp="./data/error.py"))
        await ctx.message.delete()

    @unload.error
    async def unload_cog_error(self, ctx, args):
        pass

    @commands.command()
    @commands.is_owner()
    async def cogs(self, ctx: commands.Context):
        embed = discord.Embed(title="States:",
                              description=f'Main-Bot:\n'
                                          f'**Start-Time:** <t:{int(self.bot.start_time.timestamp())}:R>\n'
                                          f'**Size:** `{GetHumanReadable((await asyncio.get_event_loop().run_in_executor(None, get_size, self.bot)))}`\n'
                                          f'**Commands:** `{len(self.bot.commands)}`\n'
                                          f'**Listeners:** `{len(self.bot._listeners) + len([v for v in self.bot.extra_events.values()])}`\n'
                                          f'**Slash-Commands:** `{len(self.bot.slash.commands.values())}`',
                              timestamp=datetime.utcnow(),
                              color=discord.Color.green())
        for cog in self.bot.cogs.values():
            func_list = [getattr(cog, x) for x in dir(cog)]
            res = [x for x in func_list if isinstance(x, (discord_slash.model.CogBaseCommandObject, discord_slash.model.CogSubcommandObject))]
            embed.add_field(name=cog.qualified_name,
                            value=f'**Load Time:** <t:{int(cog.load_time.timestamp())}:R>\n'
                                  f'**Size:** `{GetHumanReadable((await asyncio.get_event_loop().run_in_executor(None, get_size, cog, True)))}`\n'
                                  f'**Commands:** `{len(cog.get_commands())}`\n'
                                  f'**Listeners:** `{len(cog.get_listeners())}`\n'
                                  f'**Slash-Commands:** `{len(res)}`')
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @cogs.error
    async def cog_error(self, ctx, args):
        pass

    @commands.command()
    @commands.is_owner()
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"my current connection latency to discord is: `{self.bot.latency*1000:,.0f}` ms.")

    @ping.error
    async def ping_error(self, ctx: commands.Context, args):
        pass

    @commands.command()
    @commands.is_owner()
    async def restart(self, ctx):
        raise KeyboardInterrupt('force restart') from self.__class__

    @commands.command(name='reload-module', aliases=['reloadm', 'rm', 'rmodule'])
    @commands.is_owner()
    async def reloadm(self, ctx, module: str, *, cog: str = None, delete_msg: bool = False):
        if cog is None:
            messages = ''
            try:
                ctx.bot._reload_module(module)
            except Exception as exc:
                messages += f'❌ Failed to reload module `{module}` in Main-File: ```py\n{exc}\n```'
            else:
                messages += f'✅ Module `{module}` has been successful reloaded in Main-File.\n'
            for cog in ctx.bot.cogs.values():
                try:
                    cog._reload_module(module)
                except Exception as exc:
                    messages += f'❌ Failed to reload module `{module}` in Cog `{cog.__class__.__name__}`:```py\n{exc}\n```'
                else:
                    messages += f'✅ Module `{module}` has been successful reloaded in Cog `{cog.__class__.__name__}`\n'
            await ctx.reply(messages,
                            allowed_mentions=discord.AllowedMentions(replied_user=False, users=False),
                            delete_after=10 if delete_msg else None)
        else:
            if cog == 'Main':
                cog = ctx.bot
            else:
                cog = ctx.bot.get_cog(cog)
            try:
                cog._reload_module(module)
            except Exception as exc:
                await ctx.reply(
                    f'❌ Failed to reload module `{module}` in {f"Cog `{cog.__class__.__name__}`" if cog is not ctx.bot else "Main-File"}:```py\n{exc}\n```',
                    delete_after=10 if delete_msg else None)
            else:
                await ctx.reply(f'✅ Module `{module}` has been successful reloaded in {f"Cog `{cog.__class__.__name__}`" if cog is not ctx.bot else "Main-File"}',
                                allowed_mentions=discord.AllowedMentions(replied_user=False, users=False),
                                delete_after=5 if delete_msg else None)
        if delete_msg:
            await ctx.message.delete(delay=5)

    @commands.command(aliases=['socr', 'sync on cog-reload'])
    @commands.is_owner()
    async def sync_on_cog_reload(self, ctx: commands.Context, value: bool):
        self.bot.slash.sync_on_cog_reload = value
        await ctx.reply('Slash commands will now be {_value} when reloading a Cog.'.format(_value={True: "synced", False: "not synced"}.get(value)), delete_after=4)
        await ctx.message.delete(delay=4)

    def _reload_module(self, module: str):
        import importlib
        m: types.ModuleType = globals().get(module, locals().get(module, None))
        if m:
            return importlib.reload(m)
        else:
            raise ModuleNotFoundError(f'there is no Module {module} loaded')

    @commands.command(aliases=['all slash cmds'])
    @commands.is_owner()
    async def slash_commands_as_dict(self, ctx):
        from pprint import pprint
        with open('all_slash_commands.json', 'w') as fp:
            pprint((await self.bot.slash.to_dict()), fp)
        await ctx.send(file=discord.File('all_slash_commands.json'))

    @commands.command()
    @commands.is_owner()
    async def guilds(self, ctx, owner: typing.Union[discord.User, int] = None):
        if isinstance(owner, discord.User):
            owner_id = owner.id
        else:
            owner_id = owner
        to_send = []
        guilds = [f'**Name:** `{g.name}`, **Owner:** [{g.owner}](https://discord.com/users/{g.owner.id}), **ID:** `{g.id}`\n**Joined at:** <t:{int(g.me.joined_at.timestamp())}:R>, **Members:** `{g.member_count}`\n' for g in sorted(self.bot.guilds, key=lambda guild: guild.me.joined_at) if ((g.owner_id == owner_id) if owner_id is not None else True)]
        if not guilds:
            await ctx.author.send(embed=discord.Embed(description=f'<@{owner_id}> owns no guild where i\'m in',
                                                      color=discord.Color.red()))
        else:
            to_send.append(discord.Embed(title=f'Guilds: {len(guilds)}',
                                         description=guilds.pop(0),
                                         timestamp=datetime.utcnow(),
                                         color=discord.Color.green()))
            max_len = 4096
            for guild in guilds:
                if len(to_send) >= 10:
                    break
                if not ((len(to_send[-1].description) + len(guild)) > max_len):
                    to_send[-1].description += guild
                else:
                    to_send.append(discord.Embed(title=f'Part {len(to_send) + 1}',
                                                 description=guild,
                                                 color=discord.Color.green()))

            try:
                await ctx.author.send(embeds=to_send)
            except discord.HTTPException:
                for e in to_send:
                    await ctx.author.send(embed=e)
                    await asyncio.sleep(2)
        if (not isinstance(ctx.channel, discord.DMChannel)) and ctx.channel.permissions_for(ctx.me).manage_messages:
            await ctx.message.delete()

    #@commands.command()
    @commands.is_owner()
    async def guild(self, ctx: commands.Context):
        to_send = []
        guilds = [f'**Name:** `{g.name}`, **Owner:** [{g.owner}](https://discord.com/user/{g.owner.id}), **ID:** `{g.id}`, **Joined at:** <t:{int(g.me.joined_at.timestamp())}:R>, **Members:** `{g.member_count}`\n' for g in self.bot.guilds]
        max_len = 4096
        pos = 0
        while (pos <= len(guilds)) and len(to_send) < 10:
            embed = discord.Embed(title=f'{f"Guilds: {len(self.bot.guilds)}" if len(to_send) == 0 else f"Part {len(to_send) + 1}"}',
                                  description=guilds.pop(pos),
                                  timestamp=datetime.utcnow() if len(to_send) == 0 else discord.Embed.Empty,
                                  color=discord.Color.green())
            pos += 1
            try:
                while ((pos) <= len(guilds)) and (len(embed.description) + len(p := guilds.pop(pos)) <= max_len):
                    embed.description += p
                    if ((pos + 1) <= len(guilds)) and (len(embed.description) + len(guilds[pos]) <= max_len):
                        pos += 1
            except IndexError:
                to_send.append(embed.to_dict())
                break
            guilds.append(p)
            to_send.append(embed.to_dict())
            pos += 1
        from pprint import pp
        to_send = [discord.Embed.from_dict(e) for e in to_send]
        pp([e.to_dict() for e in to_send])
        await ctx.author.send(embeds=to_send)
        if (not isinstance(ctx.channel, discord.DMChannel)) and ctx.channel.permissions_for(ctx.me).manage_messages:
            await ctx.message.delete()

    async def on_command_error(self, ctx: commands.Context, exc: Exception):
        if isinstance(exc, commands.NotOwner):
            await ctx.reply(embed=discord.Embed(title='You are not allowed to use this command!',
                                                description='Only the owner of this Bot, <@693088765333471284> could use this.\n'
                                                            'All commands you could use are available as [`/-commands`](https://blog.discord.com/slash-commands-are-here-8db0a385d9e6).\n'
                                                            'Enter `/` in the chat, select me and there is a list of all commands you could use 😃',
                                                color=discord.Color.red()),
                            allowed_mentions=discord.AllowedMentions(replied_user=False, users=False))
        else:
            raise exc


def setup(bot):
    cog = RestartCommand(bot)
    bot.on_command_error = cog.on_command_error
    bot.add_cog(cog)
