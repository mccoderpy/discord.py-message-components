.. currentmodule:: discord

.. _intro:

Introduction
==============

This is the documentation for discord.py-message-components, a library for Python to aid
in creating applications that utilise the Discord API.

Prerequisites
---------------

discord.py-message-components works with Python 3.5.3 or higher. Support for earlier versions of Python
is not provided. Python 2.7 or lower is not supported. Python 3.4 or lower is not supported
due to one of the dependencies (:doc:`aiohttp <aio:index>`) not supporting Python 3.4.


.. _installing:

Installing
-----------

To install the library from PyPI using ``pip``:

.. tab:: Linux/macOS

    .. code-block:: shell

        python3 -m pip install -U discord.py-message-components

.. tab:: Windows

    .. code-block:: shell

        py -m pip install -U discord.py-message-components

Voice support (e.g. playing audio in voice channels) is not enabled by default and can be enabled by installing ``discord.py-message-components[voice]`` instead of ``discord.py-message-components``.:

.. tab:: Linux/macOS

    .. code-block:: shell

        python3 -m pip install -U discord.py-message-components[voice]

    .. note::
        On Linux environments, installing voice requires getting the following dependencies using your favourite package manager (e.g. ``apt``, ``yum``):

        - `libffi <https://github.com/libffi/libffi>`_
        - `libnacl <https://github.com/saltstack/libnacl>`_
        - `python3-dev <https://packages.debian.org/python3-dev>`_

        For a Debian-based system, the following command will get these dependencies:

        .. code-block:: shell

            $ apt install libffi-dev libnacl-dev python3-dev

        **Remember to check your permissions!**

.. tab:: Windows

    .. code-block:: shell

        py -m pip install -U discord.py-message-components[voice]

    .. note::
        On Windows, you need to install the `FFmpeg <https://www.ffmpeg.org/>`_ binary yourself.
        You can download it `here <https://www.ffmpeg.org/download.html/>`_.

        Save/extract the files somewhere where you won't accidentally delete them, e.g. ``C:\\ffmpeg`` or ``C:\\Program Files\ffmpeg``.

        You then need to add the directory containing the binary(s) (should be a folder named ``bin``)
        to your system's ``PATH`` environment variable.

        The procedure for doing this varies depending on which version of Windows you are using.

        .. tab:: Windows 10/11

            1. Open the Start Menu.
            2. Search for ``environment``.
            3. Click :key:`Edit the system environment variables`
            4. Click the :key:`Environment Variables...` button.
            5. Select the `Path` variable under **System variables**.
            6. Click the :key:`Edit...` button.
            7. Click the :key:`New` button.
            8. Paste the path to the directory containing the FFmpeg binary.
            9. Click :key:`OK` to close all the windows you have opened.

        .. tab:: Windows 7

            1. Open the Start Menu.
            2. Right-click "Computer".
            3. Click "Properties".
            4. Click "Advanced system settings".
            5. Click the "Environment Variables..." button.
            6. Select the "Path" variable under "System variables".
            7. Click the "Edit..." button.
            8. Click the "New" button.
            9. Paste the path to the directory containing the FFmpeg binary.
            10. Click "OK" to close all the windows you have opened.

Installing the developer version
---------------------------------

You can install the developer (alpha/beta) version from the `developer-branch <https://github.com/mccoderpy/discord.py-message-components/tree/developer>`_
from GitHub. This version is not guaranteed to be stable and may have bugs. But it may have a lot of new features already implemented.

.. warning::
    In order to "clone" and install the repository of this library from GitHub you need to have git installed on your system.
    If you need help with this take a look **→** `here <https://github.com/git-guides/install-git>`_ **←**

.. tab:: Linux/macOS

    .. code-block:: shell

        python3 -m pip install -U git+https://github.com/mccoderpy/discord.py-message-components.git@developer

.. tab:: Windows

    .. code-block:: shell

        py -m pip install -U git+https://github.com/mccoderpy/discord.py-message-components.git@developer

Virtual Environments
~~~~~~~~~~~~~~~~~~~~~

Sometimes you want to keep libraries from polluting system installs or use a different version of
libraries than the ones installed on the system. You might also not have permissions to install libraries system-wide.
For this purpose, the standard library as of Python 3.3 comes with a concept called "Virtual Environment"s to
help maintain these separate versions.

A more in-depth tutorial is found on :doc:`py:tutorial/venv`.

However, for the quick and dirty:

1. Go to your project's working directory:

    .. code-block:: shell

        $ cd your-bot-source
        $ python3 -m venv bot-env

2. Activate the virtual environment:

    .. code-block:: shell

        $ source bot-env/bin/activate

    On Windows you activate it with:

    .. code-block:: shell

        $ bot-env\Scripts\activate.bat

3. Use pip like usual:

    .. code-block:: shell

        $ pip install -U discord.py-message-components

Congratulations. You now have a virtual environment all set up.

Basic Concepts
---------------

discord.py-message-components revolves around the concept of :ref:`events <discord-api-events>`.
An event is something you listen to and then respond to. For example, when a message
happens, you will receive an event about it that you can respond to.

A quick example to showcase how events work:

.. code-block:: python3

    import discord

    class MyClient(discord.Client):
        async def on_ready(self):
            print('Logged on as {0}!'.format(self.user))

        async def on_message(self, message):
            print('Message from {0.author}: {0.content}'.format(message))

    client = MyClient()
    client.run('my token goes here')

