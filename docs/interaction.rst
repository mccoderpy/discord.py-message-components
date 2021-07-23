Interaction
===========

.. _respond: ./interaction.html#Interaction.respond
.. _defer:  ./interaction.html#Interaction.defer
.. _edit:  ./interaction.html#Interaction.edit

.. class:: InteractionCallbackType

   This is located in discord.enums but i place it here.

   InteractionCallbackType to react to an :class:`Interaction`

   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+
   | NAME                                    | VALUE | DESCRIPTION                                      | USAGE                       | EXAMPLE                                    |
   +=========================================+=======+==================================================+=============================+============================================+
   | .. attribute:: pong                     |   1   | ACK a ``Ping``                                   | ACK a Ping to Discord       |                     ~                      |
   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+
   | .. attribute:: msg_with_source          |   4   | respond to an interaction with a message         | :class:`Interaction.respond`| .. toggle-header::                         |
   |                                         |       |                                                  |                             |    :header: **Click for example**          |
   |                                         |       |                                                  |                             |                                            |
   |                                         |       |                                                  |                             |    .. image:: imgs/ict4example.gif         |
   |                                         |       |                                                  |                             |       :alt: Example for msg_with_source    |
   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+
   |                                         |       |                                                  |                             | .. toggle-header::                         |
   | .. attribute:: deferred_msg_with_source |   5   | ACK an interaction and edit a response later,    | Possible                    |    :header: **Click for example**          |
   |                                         |       | the user sees a loading state                    | :attr:`response_type`       |                                            |
   |                                         |       |                                                  | for defer_                  |    .. image:: imgs/ict5example.gif         |
   |                                         |       |                                                  |                             |       :alt: Example for                    |
   |                                         |       |                                                  |                             |             deferred_msg_with_source       |
   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+
   | .. attribute:: deferred_update_msg      |   6   | for components, ACK an interaction and edit      | Possible                    | .. toggle-header::                         |
   |                                         |       | the original message later;                      | :attr:`response_type`       |    :header: **Click for example**          |
   |                                         |       | the user does not see a loading state            | for defer_                  |                                            |
   |                                         |       |                                                  |                             |    .. image:: imgs/ict6example.gif         |
   |                                         |       |                                                  |                             |       :alt: Example for deferred_update_msg|
   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+
   | .. attribute:: update_msg               |   7   | for components,                                  | :class:`Interaction.edit`   | .. toggle-header::                         |
   |                                         |       | edit the message the component was attached to   |                             |    :header: **Click for example**          |
   |                                         |       |                                                  |                             |                                            |
   |                                         |       |                                                  |                             |    .. image:: imgs/ict7example.gif         |
   |                                         |       |                                                  |                             |       :alt: Example for update_msg         |
   +-----------------------------------------+-------+--------------------------------------------------+-----------------------------+--------------------------------------------+

.. class:: Interaction

   .. warning::
      Do not initiate this Class manually

   Represents an interaction created in discord like click an :class:`Button` or select an option of :class:`SelectMenu`

   .. note::
      For general information's about Interactions visit the `Discord-API-Documentation <https://discord.com/developers/docs/interactions/slash-commands#interaction-object>`_ of the discord-api.

   .. attribute:: author

         A :class:`Member` that invoked the interaction. If :attr:`channel` is a
         private channel or the user has left the guild, then it is a :class:`User` instead.

   .. attribute:: message

         The message the component was attached to.
         This will be equal to ``None`` if the :attr:`component_type` is ``None`` or the message the component is attached to is ``ephemeral``.

         .. note::
            In this version, this parameter should always be an object of type :class:`discord.Message`
            (or ``None`` if the message is ephemeral) because it only gets initiated when the interaction_type is higher than 2.

   .. attribute:: channel

      The Channel the interaction was created in this is aiter an object of :class:`discord.TextChannel` if it's
      inside a guild else it's an object of type :class:`discord.DMChannel`.

   .. attribute:: guild

      The guild associated with the interaction; aiter an object of type :class:`discord.Guild`,
      except the interaction was inside an dm-channel then this would be equal to ``None``

   .. attribute:: component

      The component that invoked this interaction:
      Aiter an object of type :class:`Button` or :class:`SelectMenu` if the message is **not** ephemeral
      else type :class:`ButtonClick` or :class:`SelectionSelect`

      .. note::
         If this is passed in an ``[on_][raw_]button_click`` or ``[on_][raw_]selection_select`` Event there would be a second parameter that includes this attribute.

   .. method:: defer(response_type: any([InteractionCallbackType.deferred_msg_with_source, InteractionCallbackType.deferred_update_msg, int]) = InteractionCallbackType.deferred_update_msg, hidden=False)

      `|coro| <./index.html#coro>`_

      'Defers' the response.

      If :attr:`response_type` is `InteractionCallbackType.deferred_msg_with_source` it shows a loading state to the user.

      :param response_type: any([InteractionCallbackType.deferred_msg_with_source, InteractionCallbackType.deferred_update_msg, int])
         The type to response with, aiter :class:`InteractionCallbackType.deferred_msg_with_source` or :class:`InteractionCallbackType.deferred_update_msg` (e.g. 5 or 6)

      :param hidden: Optional[bool] = False
          Whether to defer ephemerally(only the :attr:`author` of the interaction can see the message)

          .. note::
              Only for :class:`InteractionCallbackType.deferred_msg_with_source`.

      .. important::
         If you doesn't respond with an message using :meth:`respond`
         or edit the original message using :meth:`edit` within less than 3 seconds,
         discord will indicates that the interaction failed and the interaction-token will be invalidated.
         To provide this us this method

      .. note::
         A Token will be Valid for 15 Minutes so you could edit the original :attr:`message` with :meth:`edit`, :meth:`respond` or doing anything other with this interaction for 15 minutes.
         after that time you have to edit the original message with the Methode :meth:`edit` of the :attr:`message` and sending new messages with the :meth:`send` Methode of :attr:`channel`
         (you could not do this hidden as it isn't an respond anymore)

   .. method:: edit(**fields)

      `|coro| <./index.html#coro>`_

      Edit the :class:`Message` the component is attached to, if the interaction is not deferred it will defer automatic.

      .. note::
         If you have not yet defered or defered with type :class:`InteractionCallbackType.deferred_update_msg`, edit the message to which the component is attached, otherwise edit the callback message.

      :param \**fields: The fields of the original message to replace. You could pass the same Parameters as using :meth:`discord.Message.edit`

   .. method:: respond(**kwargs)

      `|coro| <./index.html#coro>`_

      You could pass the same Parameters as using :meth:`discord.Messageable.send` but there are one more optional:
      Responds to an interaction by sending a message that can be made visible only to the person who invoked the interaction by setting the :attr:`hidden` to ``True``.

      :param hidden: Optional[:class:`bool`]
         If set to ``True``, the message will be only visible(e.g. ephemeral) for the :attr:`author` of the Interaction and will disappears
         if the :attr:`author` click on ``delete this message``, the message go out of his view or he reloads the client.

         .. note::
            If you send an ``hidden`` (ephemeral)-respond, discord don't returns any data like an message you could edit,
            **but** you could receive Interactions when the Author interact with an component in the message.

      :return:  Union[:class:`discord.Message`, :class:`discord.EphemeralMessage`]

________________________________________

.. class:: ButtonClick

   The object that contains a :class:`Interaction.component`
   if it is of type 2 and the message is ephemeral.

   .. attribute:: custom_id

      Union[:class:`str`, :class:`int`]

      The :attr:`custom_id` of the :class:`Button`.
      If the :attr:`custom_id` is a number it is returned as an integer, otherwise a string.

__________________________________________

.. class:: SelectionSelect

   The object containing a :class:`Interaction.component` contains, if it is of type 3 and the message is ephemeral.

   .. attribute:: custom_id

      Union[:class:`str`, :class:`int`]

      The :attr:`custom_id` of the :class:`SelectMenu`.
      If the :attr:`custom_id` is a number it is returned as an integer, otherwise a string.


   .. attribute:: values

      List[Union[:class:`str`, :class:`int`]]
      A list of the options that have been selected.
      If the :attr:`value` is a number it is returned as an integer, otherwise a string

________________________________________

.. class:: EphemeralMessage

    Since Discord doesn't return anything when we send a ephemeral message,
    this class has no attributes and you can't do anything with it.

.. toctree:: 
   :maxdepth: 2
   :caption: Contents: 

Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

