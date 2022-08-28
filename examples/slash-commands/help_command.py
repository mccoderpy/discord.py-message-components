from typing import (
    Optional,
    Union
)

import discord
from discord import (
    SlashCommandOption as Option,
    ApplicationCommandInteraction as APPCI
)
from discord.ext import commands


class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.slash_command(
        description='Shows you the help menu',
        options=[
            Option(
                name='command',
                description='The command to show extra information for',
                option_type=str,
                autocomplete=True,
                required=False
            )
        ]
    )
    async def help(self, ctx: APPCI, command: Optional[str] = None):
        if command is None:
            description = ''
            for cmd in self.bot.global_application_commands:
                description += f'{cmd.mention} - {cmd.description}\n'
            embed = discord.Embed(
                title=f'Help menu for {self.bot.user.name}',
                description=description,
                color=discord.Color.blurple()
            )
        else:
            command: Union[discord.SlashCommand, discord.SubCommand] = discord.utils.get(
                self.bot.global_application_commands,
                qualified_name=command
            )
            embed = discord.Embed(
                title=f'Info for command {command.name}',
                description=f'**Usage of {command.mention}:**\n{command.description}',
                color=discord.Color.blurple()
            )
            if command.options:
                embed.description += f'\n\n' \
                                     f'**Usage:**\n' \
                                     f'`<>` means the option is required, `[]` that it is optional\n' \
                                     f'**/{command.qualified_name}** '
                for option in command.options:
                    if option.required:
                        embed.description += f'<`{option.name}`> '
                    else:
                        embed.description += f'[`{option.name}`] '
                    embed.add_field(
                        name=option.name + ' (optional)' if not option.required else '',
                        value=option.description,
                        inline=False
                    )
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(HelpCommand(bot))
