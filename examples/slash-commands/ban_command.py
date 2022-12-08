import discord
from discord import (
    SlashCommandOption as Option,
    ApplicationCommandInteraction as APPCI
)
from discord.ext import commands
from typing import Optional


class BanCommand(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.slash_command(
        description='Ban a member',
        options=[
            Option(
                name='user',
                description='The user which should be banned',
                option_type=discord.Member,
                required=True
            ),
            Option(
                name='reason',
                description='The reason why the user should be banned',
                option_type=str,
                required=False
            )
        ]
    )
    async def ban(self, ctx: APPCI, user: discord.Member, reason: Optional[str] = None):

        if reason is None:
            reason = "No reason"

        await user.ban(reason=reason)

        embed = discord.Embed(
            title="User banned",
            description=f"{user.mention} got banned for {reason}"
        )
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(BanCommand(bot))