.. currentmodule:: discord

Exceptions
------------

The following exceptions are thrown by the library.

.. autoexception:: DiscordException

.. autoexception:: ClientException

.. autoexception:: LoginFailure

.. autoexception:: NoMoreItems

.. autoexception:: HTTPException
    :members:

.. autoexception:: Unauthorized

.. autoexception:: Forbidden

.. autoexception:: NotFound

.. autoexception:: DiscordServerError

.. autoexception:: InvalidData

.. autoexception:: InvalidArgument

.. autoexception:: GatewayNotFound

.. autoexception:: ConnectionClosed

.. autoexception:: PrivilegedIntentsRequired

.. autoexception:: AlreadyResponded

.. autoexception:: discord.opus.OpusError

.. autoexception:: discord.opus.OpusNotLoaded

.. autoexception:: DiscordWarning

.. autoexception:: UnknownInteraction

Exception Hierarchy
~~~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`Exception`
        - :exc:`DiscordException`
            - :exc:`ClientException`
                - :exc:`InvalidData`
                - :exc:`InvalidArgument`
                - :exc:`LoginFailure`
                - :exc:`ConnectionClosed`
                - :exc:`PrivilegedIntentsRequired`
            - :exc:`NoMoreItems`
            - :exc:`GatewayNotFound`
            - :exc:`HTTPException`
                - :exc:`Unauthorized`
                - :exc:`Forbidden`
                - :exc:`NotFound`
                - :exc:`DiscordServerError`
            - :exc:`AlreadyResponded`
    - :exc:`Warning`
        - :exc:`DiscordWarning`
            - :exc:`UnknownInteraction`