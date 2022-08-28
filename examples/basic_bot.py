from pathlib import Path
import discord
from discord.ext import commands

TOKEN = "TOKEN"
cog_directory = "cogs"  # directory containing the extensions (cogs)


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'),
    intents=discord.Intents.all(),
    case_insensitive=True,
    sync_commands=True
)


@bot.event
async def on_ready():
    print("======")
    print(f"{bot.user.name}")
    print("======")


@bot.command()
async def ping(ctx):
    ctx.send("Pong!")

if __name__ == "__main__":
    _cogs = [p.stem for p in Path(cog_directory).glob('*.py')]
    [(bot.load_extension(f'.{ext}', package=cog_directory), print(f'{ext} was loaded successfully')) for ext in _cogs]
    bot.run(TOKEN)
