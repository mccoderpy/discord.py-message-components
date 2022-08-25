import re
import typing
import discord
import asyncio
from discord import Button
from discord.ext import commands


components = [
    [
        Button(label='C', custom_id='cancel', style=discord.ButtonStyle.red),
        Button(label='(', custom_id='calculator:(', style=discord.ButtonStyle.green, disabled=True),  # soon™
        Button(label=')', custom_id='calculator:)', style=discord.ButtonStyle.green, disabled=True),  # soon™
        Button(label='/', custom_id='calculator:/', style=discord.ButtonStyle.green)
    ],
    [
        Button(label='7', custom_id='calculator:7', style=discord.ButtonStyle.blurple),
        Button(label='8', custom_id='calculator:8', style=discord.ButtonStyle.blurple),
        Button(label='9', custom_id='calculator:9', style=discord.ButtonStyle.blurple),
        Button(label='x', custom_id='calculator:*', style=discord.ButtonStyle.green)
    ],
    [
        Button(label='4', custom_id='calculator:4', style=discord.ButtonStyle.blurple),
        Button(label='5', custom_id='calculator:5', style=discord.ButtonStyle.blurple),
        Button(label='6', custom_id='calculator:6', style=discord.ButtonStyle.blurple),
        Button(label='-', custom_id='calculator:-', style=discord.ButtonStyle.green)
    ],
    [
        Button(label='1', custom_id='calculator:1', style=discord.ButtonStyle.blurple),
        Button(label='2', custom_id='calculator:2', style=discord.ButtonStyle.blurple),
        Button(label='3', custom_id='calculator:3', style=discord.ButtonStyle.blurple),
        Button(label='+', custom_id='calculator:+', style=discord.ButtonStyle.green)
    ],
    [
        Button(label='+/-', custom_id='calculator:+/-', style=discord.ButtonStyle.blurple),
        Button(label='0', custom_id='calculator:0', style=discord.ButtonStyle.blurple),
        Button(label=',', custom_id='calculator:,', style=discord.ButtonStyle.blurple),
        Button(label='=', custom_id='calculator:=', style=discord.ButtonStyle.green)
    ]
]


def is_author(func) -> typing.Coroutine:
    """
    Just a small decorator that checks if the author is allowed to interact with the calculator instance
    """
    actual = typing.Final = func

    async def func(self, interaction: discord.BaseInteraction, button):
        calc = self.get_calculator(interaction.message, interaction.author)
        if calc:
            await actual(self, interaction, button, calc)

    func.__name__ = actual.__name__
    return func


class CalculatorUnit:
    def __init__(self, msg: discord.Message, author: discord.User, color: discord.Color = discord.Color.random()) -> None:
        self.author: discord.User = author
        self.msg: discord.Message = msg
        self.color = color
        self._a: typing.Optional[str] = None
        self._b: typing.Optional[str] = None
        self._method: typing.Optional[str] = None
        self._result: int = 0

    @property
    def a(self) -> str:
        return self._a

    @a.setter
    def a(self, amount) -> None:
        if not self.a:
            self._a = ''
        if amount == '.':
            self._a = self._a.replace('.', '')
            self._a += str(amount)
        elif amount != '.':
            self._a += str(amount)

    @property
    def b(self) -> str:
        return self._b

    @b.setter
    def b(self, amount) -> None:
        if not self.b:
            self._b = ''
        if amount == '.':
            self._b = self._b.replace('.', '')
            self._b += str(amount)
        elif amount != '.':
            self._b += str(amount)

    @property
    def method(self) -> str:
        return self._method

    @method.setter
    def method(self, _type) -> None:
        self._method = _type

    async def calculate(self, interaction: discord.BaseInteraction, new_method: typing.Optional[str] = None) -> None:
        self._result = str(eval(f'{float(self._a)} {self.method} {float(self._b)}'))
        if self._result[-2:] == '.0':
            self._result = self._a = self._result[:-2]
        else:
            self._a = self._result
        self._b = None
        self._method = new_method
        await self.update_display(interaction)

    async def delete(self) -> None:
        await self.msg.delete()
        del self

    async def reset(self, interaction: typing.Optional[discord.BaseInteraction] = None) -> None:
        self._a = None
        self._b = None
        self._method = None
        self._result = 0
        embed = discord.Embed(description="```py\n                                      0```", color=self.color)
        if interaction:
            await interaction.edit(embed=embed, components=components)
        else:
            await self.msg.edit(embed=embed, components=components)

    async def update_display(self, interaction: discord.BaseInteraction = None):
        if self.a and not self.b:
            output = self.a
        elif self.b:
            output = self.b
        else:
            output = '0'
        spaces = '                                       '[len(output) + len(f'{" |  " if self.method else ""}'):]
        method = f"{self.method}".replace('**', '^')
        embed = discord.Embed(description=f'```py\n{spaces}{output}{f" | {method}" if self.method else ""}\n```',
                              color=self.color)
        if interaction:
            await interaction.edit(embed=embed)
        else:
            await self.msg.edit(embed=embed, components=components)


class Calculator(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot
        self.calculators = {}

    def get_calculator(self, message: discord.Message, author) -> typing.Optional[CalculatorUnit]:
        try:
            calc = self.calculators[message.id]
        except KeyError:
            c_author = message.mentions[0]
            self.calculators[message.id] = calc = CalculatorUnit(message, c_author, message.embeds[0].color)
            description = message.embeds[0].description.split('|')
            calc.a = description.pop(0).strip('\n```py ')
            if description:
                calc._method = description.pop(0).strip('\n``` ')
        return calc if calc.author == author else None

    def add_calculator(self, calculator: CalculatorUnit) -> CalculatorUnit:
        self.calculators[calculator.msg.id] = calculator
        return calculator

    def remove_calculator(self, calculator: CalculatorUnit) -> typing.Optional[CalculatorUnit]:
        return self.calculators.pop(calculator.msg.id, None)

    @commands.Cog.slash_command(name="calculator", description="open an calculator")
    async def calculator(self, ctx: discord.ApplicationCommandInteraction) -> None:
        embed = discord.Embed(color=discord.Color.random(),
                              description="```py\n                                      \u001b[34m0\n```")
        calc = self.add_calculator(
            CalculatorUnit(await ctx.respond(ctx.author.mention, embed=embed, components=components), ctx.author, embed.color))

        def _check(i, _) -> bool:
            return i.author == ctx.author and i.author == ctx.author

        while True:  # This is just to let the calculator "timeout" after a specific time without any input
            try:
                await self.bot.wait_for('button_click', timeout=300.0, check=_check)
            except asyncio.TimeoutError:
                break
        await calc.delete()

    @commands.Cog.on_click()
    @is_author
    async def cancel(self, interaction: discord.ComponentInteraction, button, calc):
        await calc.reset(interaction)

    @commands.Cog.on_click(r'^calculator:\d+$')
    @is_author
    async def number_press(self, interaction: discord.ComponentInteraction, button: Button, calc):
        if not calc.method and not calc.b:
            if calc.a == '0':
                return await interaction.defer()
            calc.a = button.custom_id.replace('calculator:', '')
        elif calc.a and calc.method:
            if calc.b == '0':
                return await interaction.defer()
            calc.b = button.custom_id.replace('calculator:', '')
        await calc.update_display(interaction)

    @commands.Cog.on_click(r'^calculator:\+$')
    @is_author
    async def add(self, interaction, button, calc):
        if calc.method and calc.a and calc.b:
            await calc.calculate(interaction, '+')
        else:
            calc.method = '+'
            await calc.update_display(interaction)

    @commands.Cog.on_click(r'^calculator:-$')
    @is_author
    async def subtract(self, interaction, button, calc):
        if calc.method and calc.a and calc.b:
            await calc.calculate(interaction, '-')
        else:
            calc.method = '-'
            await calc.update_display(interaction)

    @commands.Cog.on_click(r'^calculator:/$')
    @is_author
    async def divide(self, interaction, button, calc):
        if calc.method and calc.a and calc.b:
            await calc.calculate(interaction, '/')
        else:
            if calc.method == '/':
                calc.method += '/'
            else:
                calc.method = '/'
            await calc.update_display(interaction)

    @commands.Cog.on_click(r'^calculator:\*$')
    @is_author
    async def multiply(self, interaction, button, calc):
        if calc.method and calc.a and calc.b:
            await calc.calculate(interaction, '*')
        else:
            if calc.method == '*':
                calc.method += '*'
            else:
                calc.method = '*'
            await calc.update_display(interaction)

    @commands.Cog.on_click(r'^calculator:=$')
    @is_author
    async def calculate(self, interaction, button, calc):
        if calc.a and calc.method and calc.b:
            await calc.calculate(interaction)

    @commands.Cog.on_click(r'^calculator:[,]$')
    @is_author
    async def point(self, interaction, button, calc):
        if calc.a and not calc.method:
            if calc._a[-1] == '.':
                calc._a = calc._a.strip('.')
            else:
                calc.a = '.'
        elif calc.method and calc.b:
            if calc._b[-1] == '.':
                calc._b = calc._b.strip('.')
            else:
                calc.b = '.'
        await calc.update_display(interaction)

    @commands.Cog.on_click(r'^calculator:\+/\-$')
    @is_author
    async def toggle_negative(self, interaction, button, calc):
        if calc.a and not calc.method:
            if calc.a[0].isdigit():
                calc._a = '-' + calc.a
            else:
                calc._a = calc.a.strip('-')

        elif calc.method and calc.b:
            if calc.b[0].isdigit():
                calc._b = '-' + calc.b
            else:
                calc._b = calc.b.strip('-')
        await calc.update_display(interaction)


def setup(bot):
    bot.add_cog(Calculator(bot))
