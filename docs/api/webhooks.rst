.. currentmodule:: discord

Webhook Support
------------------

discord.py-message-components offers support for creating, editing, and executing webhooks through the :class:`Webhook` class.

Webhook
~~~~~~~~~

.. attributetable:: Webhook

.. autoclass:: Webhook
    :members:

WebhookMessage
~~~~~~~~~~~~~~~~

.. attributetable:: WebhookMessage

.. autoclass:: WebhookMessage
    :members:

Adapters
~~~~~~~~~

Adapters allow you to change how the request should be handled. They all build on a single
interface, :meth:`WebhookAdapter.request`.

.. autoclass:: WebhookAdapter
    :members:

.. autoclass:: AsyncWebhookAdapter
    :members:

.. autoclass:: RequestsWebhookAdapter
    :members:
