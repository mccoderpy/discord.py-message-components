.. discord.py-message-components documentation master file, created by
   sphinx-quickstart on Sat Jun 26 14:55:47 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Interaction
===========

:class:`discord.Interaction`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Represents an interaction createt in discord like click an :class:`discord.Button` or select an option of :class:`discord.SelectMenu`
   
.. note::
   For more informations about Interactions visit the `Documentation <https://discord.com/developers/docs/interactions/slash-commands#interaction-object>`_ of the discord-api.
   
.. warning::
   Do not initiate this Class manually
   
Attributes
----------

   .. _interaction-author:

   :attr:`author`: :class:`discord.abc.User`
      A :class:`Member` that invoked the interaction. If :attr:`channel` is a
      private channel or the user has left the guild, then it is a :class:`User` instead.
   
   .. _interaction-message:

   :attr:`message`: :class:`discord.Message`
      The message the component was attachet to.
      This will be equal to ``None`` if the :attr:`component_type` is ``None`` or the message the component is attached to is ``emphemberal``.

      .. note::
         In this version, this parameter should alwasys be an object of type :class:`discord.Message`
         (or ``None`` if the message is emphemberal) beacuse it only gets initiatet when the interaction_type is highter than 2

   .. _interaction-channel:

   :attr:`channel`: Union[:class:`discord.TextChannel`, :class:`discord.DMChannel`]
      The Channel the interaction was createt in this is aiter an object of :class:`discord.TextChannel` if it's
      inside a guild else it's an object of type :class:`discord.DMChannel`.
   
   .. _interaction-guild:

   :attr:`guild`: Union[:class:`discord.Guild`, :class:`None`]
      The guild asotiatet with the interaction; aiter an object of type :class:`discord.Guild`,
      except the interaction was inside an dm-channel then this would be equal to ``None``
   
   .. _interaction-component:
   
   :attr:`component`: Union[:class:`ButtonClick`, :class:`SelectionSelect`]
      The component that invoked this interaction: Aiter an object of type :class:`ButtonClick` or :class:`SelectionSelect`
         
      .. note::
         If this is passed in an ``[on_]button_click`` or ``[on_]selection_select`` Event there wuild be a second parameter that includes this attribute.

Methods
--------

   .. _interaction-defer:

   :meth:`defer`: None
      'Defers' the response, showing a loading state to the use.

      .. important::
         If you doesn't respond with an message using :meth:`respond` 
         or edit the original message using :meth:`edit` within less than 3 seconds,
         discord will indicates that the interaction failed and the interaction-token will be invalidated.
         To provide this us this method

      .. note::
         A Token will be Valid for 15 Minutes so you could edit the original :attr:`message` with :meth:`edit`, :meth:`respond` or doing anything other with this interaction for 15 minutes.
         After that time you have to edit the original message with the Methode :meth:`edit` of the :attr:`message` and sending new messages with the :meth:`send` Methode of :attr:`channel`
         (you could not do this hidden as it isn't an respond anymore and also you could not pass more than one :class:`Embed`)
   
   .. _interaction-respond:

   :meth:`respond`: Union[:class:`discord.Message`, :class:`discord.EphemeralMessage`] 
      You could pass the same Paramerts as using :meth:`discord.Messageable.send` but there are two more optional:
            
      * :attr:`embeds` Optional[List[discord.Embed]]
         An :class:`list` containing up to 10 Embeds that should send with the respond.
            
      * :attr:`hidden` Optional[Bool]
         If set to ``True``, the message will be only vible for the :attr:`author` of the Interaction and will disapears  if the :attr:`author` click on ``delete this message`` or reloads the client.
               
         .. note::
            If you send an ``hidden`` (emphemberal)-respond, discord dont returns any data like an message you could edit,
            **but** you could resive Interactions when the Author interact with an component

      Responds to an interaction by sending a message that can be made visible only to the person who invoked the interaction by setting the :attr:`hidden` to ``True``.

________________________________________

.. _button-click:

:class:`ButtonClick`
~~~~~~~~~~~~~~~~~~~~
   The object that contains a discord.Interaction.component
   if it is of type 2.

   :attr:`custom_id`: str
      The ``custom_id`` that was set when the button was send and therefore its identifier. 

__________________________________________

.. _selection-select:

:class:`SelectionSelect`
~~~~~~~~~~~~~~~~~~~~~~~~
   The object containing a discord.Interaction.component contains, if it is of type 3.

   :attr:`custom_id`: str
      The ``custom_id`` of the Select Menu. 
   
   :attr:`values`: List[str]
      A list of the options that have been selected.

________________________________________

.. toctree:: 
   :maxdepth: 2
   :caption: Contents: 

Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
