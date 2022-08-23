import asyncio
from datetime import datetime
from typing import Optional, List

import discord
from discord import SlashCommandOption as Option, Localizations, Permissions, ApplicationCommandInteraction as APPCI
from discord.ext import commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.slash_command(name="help", description="Shows you the Help Menu", guild_ids=[977326610334228502])
    async def help(self, ctx: APPCI):
        embed = discord.Embed(title=f"Help Menu for {ctx.bot.user}")
        embed.add_field(name="/<yourcommand>", value="Description 1", inline=True)
        embed.add_field(name="/<yourcommand2>", value="Description 2", inline=True)
        embed.add_field(name="/<yourcommand3>", value="Description 3", inline=True)
        embed.add_field(name="/<yourcommand4>", value="Description 4", inline=True)
        embed.add_field(name="/<yourcommand5>", value="Description 5", inline=True)
        await APPCI.respond(embed=embed)




def setup(bot):
    bot.add_cog(HelpCommand(bot))
