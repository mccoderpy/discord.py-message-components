.. discord.py-message-components documentation master file, created by
   sphinx-quickstart on Sat Jun 26 14:55:47 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to discord\.py-message-components' documentation!
=========================================================

.. figure:: https://cdn.discordapp.com/attachments/852872100073963532/854711446767796286/discord.py-message-components.png
   :name: discord.py-message-components
   :align: center
   :alt: Name of the Project (discord.py-message-components)

   ..
   .. image:: https://discord.com/api/guilds/852871920411475968/embed.png
      :target: https://discord.gg/sb69muSqsg
      :alt: Discord Server Invite

   .. image:: https://img.shields.io/pypi/v/discord.py-message-components.svg
      :target: https://pypi.python.org/pypi/discord.py-message-components
      :alt: PyPI version info

   .. image:: https://img.shields.io/pypi/pyversions/discord.py-message-components.svg
      :target: https://pypi.python.org/pypi/discord.py-message-components
      :alt: PyPI supported Python versions

   .. image:: https://static.pepy.tech/personalized-badge/discord-py-message-components?period=total&units=international_system&left_color=grey&right_color=green&left_text=Downloads
      :target: https://pepy.tech/project/discord.py-message-components
      :alt: Total downloads for the project

   .. image:: https://readthedocs.org/projects/discordpy-message-components/badge/?version=latest
      :target: https://discordpy-message-components.readthedocs.io/en/latest/
      :alt: Documentation Status

   The Original `discord.py <https://pypi.org/project/discord.py/1.7.3>`_ Library made by `Rapptz <https://github.com/Rapptz>`_ with implementation of the `Discord-Message-Components <https://discord.com/developers/docs/interactions/message-components>`_ by `mccoderpy <https://github.com/mccoderpy/>`_

.. |PyPI| image:: https://cdn.discordapp.com/emojis/854380926548967444.png?v=1
   :alt: PyPI Logo
   :width: 30px
   :target: https://discordpy-message-components.readthedocs.io/en/latest/

.. centered::
   **Visit on** |PyPI| **PyPI** `here <https://pypi.org/project/discord.py-message-components>`_

You need help? Or have ideas/feedback?
______________________________________

Open a Issue/Pull request on `GitHub <https://github.com/mccoderpy/discord.py-message-components/pulls>`_, join the `support-Server <https://discord.gg/sb69muSqsg>`_ or send me a direct-message on `Discord <https://discord.com/channels/@me>`_: ``mccuber04#2960``


Installing:
___________

**Python 3.5.3 or higher is required**

This Library overwrite the original discord.py Library so to be sure all will work fine
first uninstall the original `discord.py <https://pypi.org/project/discord.py/1.7.3>`_ Library if it is installed:

.. code:: sh

    # Linux/macOS
    python3 -m pip uninstall discord.py

    # Windows
    py -3 -m pip uninstall discord.py

Then install `this Library <https://pypi.org/project/discord.py-message-components>`_ using:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U discord.py-message-components

    # Windows
    py -3 -m pip install -U discord.py-message-components

________________________________________

quickstart
__________

Sending-buttons
~~~~~~~~~~~~~~~~

.. code-block:: python

   import discord
   from discord.ext import commands
   from discord import Button, ButtonStyle


   client = commands.Bot(command_prefix=commands.when_mentioned_or('!'))


   @client.command()
   async def buttons(ctx):
      await ctx.send('Hey here are some Buttons', components=[[
         Button(label="Hey i\'m a red Button",
                  custom_id="this is an custom_id",
                  style=ButtonStyle.red),
         Button(label="Hey i\'m a green Button",
                  custom_id="this is an custom_id",
                  style=ButtonStyle.green),
         Button(label="Hey i\'m a blue Button",
                  custom_id="this is an custom_id",
                  style=ButtonStyle.blurple),
         Button(label="Hey i\'m a grey Button",
                  custom_id="this is an custom_id",
                  style=ButtonStyle.grey),
         Button(label="Hey i\'m a URL Button",
                  url="https://pypi.org/project/discord.py-message-components",
                  style=ButtonStyle.url)
      ]])

   client.run('Your Bot-Token')

________________________________________

Interact when a button was pressed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         
.. code-block:: python

   import discord
   from discord.ext import commands
   from discord import Button, ButtonStyle


   client = commands.Bot(command_prefix=commands.when_mentioned_or('!'))


   @client.command()
   async def buttons(ctx):
      msg_with_buttons = await ctx.send('Hey here are some Buttons', components=[[
          Button(label="Hey i\'m a red Button",
                 custom_id="red",
                 style=ButtonStyle.red),
          Button(label="Hey i\'m a green Button",
                 custom_id="green",
                 style=ButtonStyle.green),
          Button(label="Hey i\'m a blue Button",
                 custom_id="blue",
                 style=ButtonStyle.blurple),
          Button(label="Hey i\'m a grey Button",
                 custom_id="grey",
                 style=ButtonStyle.grey)
      ]])
      
      def check_button(i: discord.Interaction, button):
          return i.author == ctx.author and i.message == msg_with_buttons
      
      interaction, button = await client.wait_for('button_click', check=check_button)

      embed = discord.Embed(title='You pressed an Button',
      description=f'You pressed a {button.custom_id} button.',
      color=discord.Color.random()) 
      await interaction.respond(embed=embed)
      
   client.run('Your Bot-Token')

.. note:: 

   You could set the parameter :attr:`hidden` in the response to ``True`` to make the message ephemeral.
   See `discord.Interaction.respond <./interaction.html#Interaction.respond`_ for more information about :meth:`respond()`.

________________________________________

Sending-SelectMenu's and respond to them
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import discord
   from discord.ext import commands
   from discord import Button, SelectMenu, SelectOption


   client = commands.Bot(command_prefix=commands.when_mentioned_or('!'))


   @client.command()
   async def select(ctx):
      msg_with_selects = await ctx.send('Hey here is an nice Select-Menu', components=[
         [
               SelectMenu(custom_id='_select_it', options=[
                  SelectOption(emoji='1️⃣', label='Option Nr° 1', value='1', description='The first option'),
                  SelectOption(emoji='2️⃣', label='Option Nr° 2', value='2', description='The second option'),
                  SelectOption(emoji='3️⃣', label='Option Nr° 3', value='3', description='The third option'),
                  SelectOption(emoji='4️⃣', label='Option Nr° 4', value='4', description='The fourth option')],
                        placeholder='Select some Options', max_values=3)
            ]])

      def check_selection(i: discord.Interaction, select_menu):
         return i.author == ctx.author and i.message == msg_with_selects

      interaction, select_menu = await client.wait_for('selection_select', check=check_selection)

      embed = discord.Embed(title='You have chosen:',
                           description=f"You have chosen "+'\n'.join([f'\nOption Nr° {o}' for o in select_menu.values]),
                           color=discord.Color.random())
      await interaction.respond(embed=embed)

   client.run('Your Bot-Token')

________________________________________

coro
~~~~

A `coroutine <https://docs.python.org/3/library/asyncio-task.html#coroutine>`_ is a function that must be invoked with ``await`` or ``yield from``.
When Python encounters an ``await`` it stops the function’s execution at that point and works on other things until it comes back to that point and finishes off its work.
This allows for your program to be doing multiple things at the same time without using threads or complicated multiprocessing.

**If you forget to await a coroutine then the coroutine will not run. Never forget to await a coroutine.**


.. toctree:: 
   :maxdepth: 3
   :caption: Contents: 

   additions.rst
   components.rst
   interaction.rst


Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
