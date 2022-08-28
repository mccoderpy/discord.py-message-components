import discord
from discord.ext import commands

bot = commands.Bot(command_prefix=commands.when_mentioned_or('.!'), intents=discord.Intents.all(), case_insensitive=True)

TOKEN = "TOKEN"

@bot.event
async def on_ready():
    print("======")
    print(f"{bot.user.name}")
    print("======")

@bot.command()
async def ping(ctx):
    ctx.send("Pong!")

bot.run(TOKEN)