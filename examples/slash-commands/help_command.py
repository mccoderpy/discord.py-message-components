from typing import (
    Optional,
    Union,
    List
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
        self.latest_command_list = []

    def fill_command_list(self) -> List[Union[discord.SlashCommand, discord.SubCommand]]:
        self.latest_command_list = command_list = []
        for cmd in self.bot.global_application_commands:
            if isinstance(cmd, discord.SlashCommand):
                if cmd.has_subcommands:
                    for sub_cmd_or_group in cmd.sub_commands:
                        if isinstance(sub_cmd_or_group, discord.SubCommandGroup):
                            for sub_cmd in sub_cmd_or_group.sub_commands:
                                command_list.append(sub_cmd)
                        else:
                            command_list.append(sub_cmd_or_group)
                else:
                    command_list.append(cmd)
        return command_list

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
        if not self.latest_command_list:
            self.fill_command_list()
        if command is None:
            description = ''
            for cmd in self.latest_command_list:
                description += f'{cmd.mention} - {cmd.description}\n'
            embed = discord.Embed(
                title=f'Help menu for {self.bot.user.name}',
                description=description,
                color=discord.Color.blurple()
            )
        else:
            _command: Union[discord.SlashCommand, discord.SubCommand] = discord.utils.get(
                self.latest_command_list,
                qualified_name=command
            )
            if not _command:
                return await ctx.respond(
                    f'The command `{command}` is not a valid command. Please select one from the suggested ones',
                    hidden=True
                )
            else:
                command = _command
            embed = discord.Embed(
                title=f'Info for command {command.qualified_name}',
                description=f'**Usage of {command.mention}:**\n{command.description}',
                color=discord.Color.blurple()
            )
            if command.options:
                embed.description += f'\n\n' \
                                     f'**Usage:**\n' \
                                     f'`<>` means the option is required, `[]` that it is optional\n\n' \
                                     f'`/{command.qualified_name} '
                for option in command.options:
                    if option.required:
                        embed.description += f'<{option.name}> '
                    else:
                        embed.description += f'[{option.name}] '
                    embed.add_field(
                        name=option.name + (' (optional)' if not option.required else ''),
                        value=option.description,
                        inline=False
                    )
                embed.description += '`'
        await ctx.respond(embed=embed)

    @help.autocomplete_callback
    async def help_autocomplete(self, ctx: discord.AutocompleteInteraction, command: discord.option_str):
        command_list = self.fill_command_list()
        if not command:
            await ctx.send_choices(
                [
                    discord.SlashCommandOptionChoice(name=cmd.qualified_name) for cmd in command_list[:25]
                ]
            )
        else:
            await ctx.send_choices(
                [
                    discord.SlashCommandOptionChoice(name=cmd.qualified_name) for cmd in command_list if command in cmd.qualified_name
                ][:25]
            )


def setup(bot):
    bot.add_cog(HelpCommand(bot))
