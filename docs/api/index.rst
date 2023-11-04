.. currentmodule:: discord

API Reference
===============

The following section outlines the API of discord.py-message-components.

.. note::

    This module uses the Python :mod:`logging` to log diagnostic and errors
    in an output independent way.
    By default the logs will be printed in :attr:`sys.stdout` (aka the console).
    See :ref:`logging_setup` for
    more information on how to use the logging module with
    discord.py-message-components.

Version Related Info
---------------------

There are two main ways to query version information about the library. For guarantees, check :ref:`version_guarantees`.

.. data:: version_info

    A named tuple that is similar to :obj:`py:sys.version_info`.

    Just like :obj:`py:sys.version_info` the valid values for ``releaselevel`` are
    'alpha', 'beta', 'candidate' and 'final'.

.. data:: __version__

    A string representation of the version. e.g. ``'1.0.0rc1'``. This is based
    off of :pep:`440`.


The rest of the API documentation is split in to their respective sections, which are:

.. toctree::
    :maxdepth: 1

    Clients <clients.rst>
    Application Info <application-info.rst>
    Monetization <monetization.rst>
    Audit Logs <audit-logs.rst>
    Enum Types <enums.rst>
    Constants <constants.rst>
    Voice <voice.rst>
    Event Reference <events.rst>
    Exceptions <exceptions.rst>
    Utility Functions <utils.rst>
    Webhooks <webhooks.rst>
    API Models <models.rst>
    ABCs <abcs.rst>
    Async Iterator <async-iterator.rst>
    Data Classes <data-classes.rst>
