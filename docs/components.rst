.. discord.py-message-components documentation master file, created by
   sphinx-quickstart on Sat Jun 26 14:55:47 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Components
==========

.. class:: ButtonStyle

   This is located in discord.enums but i place it here.

   The possible styles for a :class:`Button`

   +------------------------+-------+----------------+--------------------------------+
   | NAME                   | VALUE | ALIASES        | EXAMPLE                        |
   +========================+=======+================+================================+
   | .. attribute:: blurple |   1   |                | .. image:: imgs/blurple.png    |
   |                        |       | ``Primary``    |    :alt: Blurple Button Picture|
   |                        |       |                |                                |
   +------------------------+-------+----------------+--------------------------------+
   | .. attribute:: grey    |   2   | ``gray``,      | .. image:: imgs/grey.png       |
   |                        |       | ``Secondary``  |    :alt: Grey Button Picture   |
   |                        |       |                |                                |
   +------------------------+-------+----------------+--------------------------------+
   | .. attribute:: green   |   3   | ``Success``    | .. image:: imgs/green.png      |
   |                        |       |                |    :alt: Green Button Picture  |
   |                        |       |                |                                |
   +------------------------+-------+----------------+--------------------------------+
   | .. attribute:: red     |   4   | ``Danger``     | .. image:: imgs/red.png        |
   |                        |       |                |    :alt: Red Button Picture    |
   |                        |       |                |                                |
   +------------------------+-------+----------------+--------------------------------+
   | .. attribute:: url     |   5   | ``link``,      | .. image:: imgs/url.png        |
   |                        |       | ``grey_url``,  |    :alt: URL Button Picture    |
   |                        |       | ``Link_Button``|                                |
   +------------------------+-------+----------------+--------------------------------+

___________________________________________


.. class:: ActionRow(*components)

   Represents an :class:`ActionRow`-Part for the components of a :class:`discord.Message`.

   .. note::
      For general information about ActionRow's visit the `Discord-APIMethodes Documentation <https://discord.com/developers/docs/interactions/message-components#actionrow>`_.

   .. note::
       You could use a :class:`list` instead of this but you don't have the functions and parameters of this class then.

   .. _actionrow-parameters:

   :param components: Union[:class:`Button`, :class:`SelectMenu`]
      The components the :class:`ActionRow` should have. It could contain at least 5 :class:`Button` or 1 :class:`SelectMenu`.

   .. classmethod:: from_dict(data)

      Converts a dict (e.g. created with :meth:`to_dict`) into an ActionRow, provided it is in the format Discord expects.

      You can read about this format in the `official Discord documentation <https://discord.com/developers/docs/interactions/message-components#action-rows>`_.

      :param dict: :class:`dict`
         The dictionary to convert into an ActionRow.

      :return: :class:`ActionRow`

   .. method:: to_dict()

      Convert this :class:`ActionRow` in to a dict.

      :return: :class:`dict`

   .. method:: disable_all_buttons()

      Disable all object's of type :class:`Button` in this :class:`ActionRow`.
        
      :return: :class:`ActionRow`

   .. method:: disable_all_buttons_if(check, *args)

      Disable all :class:`Button` (s) in this :class:`ActionRow` if the passed :attr:`check` returns ``True``.

      :param check: Union[Bool, Callable]
         Could be a :class:`bool` or usually any :obj:`Callable` that returns a :class:`bool`
            
      :param \*args: Any
         Arguments that should passed in to the :attr:`check` if it is a :obj:`Callable`.

      :return: :class:`ActionRow`


   .. method:: disable_all_select_menus_if(check, *args)

      Disables all :class:`SelectMenu` (s) in this :class:`ActionRow` if the passed :attr:`check` returns ``True``.

      :param check: Union[:class:`bool`, Callable]
         Could be a :class:`bool` or usually any :obj:`Callable` that returns a :class:`bool`.

      :param \*args: Any
         Arguments that should passed in to the :attr:`check` if it is a :obj:`Callable`.

      :return: :class:`ActionRow`

   .. method:: add_component(component)

      Adds a component to the :class:`ActionRow`.

      This function returns the class instance to allow for fluent-style
      chaining.


      :param component: Union[:class:`Button`, :class:`SelectMenu`, :class:`dict`]
         The component to add to the :class:`ActionRow`.

      :return: :class:`ActionRow`

   .. method:: add_components(*components)

      Add multiple components to the :class:`ActionRow`.

      This function returns the class instance to allow for fluent-style
      chaining.


      :param \*components: \*Union[:class:`Button`, :class:`SelectMenu`, :class:`dict`]
         The components to add to the :class:`ActionRow`.

      :return: :class:`ActionRow`

   .. method:: insert_component_at(index, component)

      Inserts a component before a specified index to the :class:`ActionRow`.

      :param index: :class:`int`
         The index of where to insert the component.
      :param component: Union[:class:`Button`, :class:`SelectMenu`, :class:`dict`]
         The component to insert at the specified index of the :class:`ActionRow`.

      :return: :class:`ActionRow`

   .. method:: set_component_at(index, component)

      Modifies a component to the ActionRow object.

      The index **must** point to a valid pre-existing component.

      This function returns the class instance to allow for fluent-style
      chaining.

      :param index: :class:`int`
         The index of the component to modify.
      :param component: Union[:class:`Button`, :class:`SelectMenu`, :class:`dict`]
         The component to replace the old one with.

      :raise IndexError: An invalid index was provided.

      :return: :class:`ActionRow`

________________________________________

.. class:: Button(label, custom_id, style, emoji, url, disabled)

   Represents a ``Discord-Button``

   .. note::
       For general information about Discord-Button's visit the `Documentation <https://discord.com/developers/docs/interactions/message-components#buttons>`_ of the discord-api.

   .. _button-parameters:

   :param label: :class:`str`
      The Text displayed in discord on the Button. Maximal length is 80 Chars.
   :param custom_id: Union[:class:`str`, :class:`int`]
        The custom_id discord send us when a User press the Button. The max. length of this is 100.
   :param style: :class:`ButtonStyle`
        The Style the Button should have.

        .. note::
            To get more infos about the styles visit
            `the Discord-APIMethodes Documentation <https://discord.com/developers/docs/interactions/message-components#buttons-button-styles>`_.

   :param emoji: Optional[Union[:class:`discord.PartialEmoji`, :class:`discord.Emoji`, :class:`str`]]
        The Emoji that will be displayed on the left side of the Button.
   :param url: Optional[:class:`str`]
      The URL the Button links too.

      .. note::
         If you set this, the :attr:`style` will automatic set to :class:`ButtonStyle.url`

      .. warning::
         You can't pass a :attr:`custom_id` and a :attr:`url` because discord don't send anything when clicking on an ``URL-Button`` so it don't accept both; :attr:`url`/:class:`ButtonStyle.url` and :attr:`custom_id`!

   :param disabled: :class:`bool`
      Whether the Button is disabled; default False.

   .. _button-methods:

   .. method:: disable_if(check, *args)
    
      Disable the :class:`Button` if the passed :attr:`check` returns ``True``.

      :param check: typing.Union[:class:`bool`, Callable]
         Could be a :class:`bool` or usually any :class:`Callable` that returns a :class:`bool`.
      :param \*args: Any
         Arguments that should passed in to the :attr:`check` if it is a :class:`Callable`

      :return: :class:`Button`

   .. method:: set_style_if(check, style, *args)

      Sets the style of the :class:`Button` to the specified one if the specified check returns True.

      :param check: Union[:class:`bool`, :obj:`typing.Callable`]
            The check could be an :class:`bool` or usually any :obj:`Callable` that returns an :class:`bool`
      :param style: discord.ButtonStyle
            The style the :class:`Button` should have when the :attr:`check` returns True
      :param \*args: Any
            Arguments that should passed in to the :attr:`check` if it is an :obj:`Callable`.

      :return: :class:`Button`

________________________________________

.. class:: SelectOption(label, value, description, emoji, default)

   Represents a option for a :class:`SelectMenu`.

   .. _select-option-parameters:

   :param label: :class:`str`
      The user-facing name of the option, max 25 characters.
    
   :param value: :class:`str`
      The dev-define value of the option, max 100 characters.

   :param description: Optional[:class:`str`]
      An additional description of the option, max 50 characters.
    
   :param emoji: Optional[Union[:class:`PartialEmoji`, :class:`Emoji`, :class:`str`]]
      An Emoji that will be displayed on the left side of the option.
    
   :param default: Optional[:class:`bool`]
       Whether this option is selected by default.

________________________________________

.. class:: SelectMenu(custom_id, options, placeholder, min_values, max_values, disabled)


   Represents a ``Discord-Select-Menu``

   .. note::
       For general information about Select-Menus visit the `Discord-APIMethodes-Documentation <https://discord.com/developers/docs/interactions/message-components#select-menus>`_.

   .. _select-menu-parameters:

   :param custom_id: Union[:class:`str`, :class:`int`]
      A developer-defined identifier for the :class:`SelectMenu`, max. 100 characters.

   :param options: List[:class:`SelectOption`]
      A :class:`list` of choices(:class:`SelectOption`) the :class:`SelectMenu` should have, max. 25.

   :param placeholder: Optional[:class:`str`]
        Custom placeholder text if nothing is selected, max. 100 characters.

   :param min_values: Optional[::class:`int`]
        The minimum number of items that must be chosen; default 1, min. 0, max. 25.

   :param max_values: Optional[:class:`int`]
        The maximum number of items that can be chosen; default 1, max. 25.

   :param disabled: Optional[:class:`bool`]
        Whether the SelectMenu is disabled or not. ``False`` by default.

   :attr:`all_option_values`: Generator[Union[:class:`str`, :class:`int`]]
      Returns a generator with all `values` of the `options` of the :class:`SelectMenu`.

      If the value is a number it is returned as an integer, otherwise a string

      .. note::
         This is equal to

         .. code-block:: python

           for option in select.options:
               if option.value.isdigit():
                   yield int(option.value)
               else:
                   yield option.value

      :yield: Union[:class:`str`, :class:`int`]

   .. method:: disable_if(check, *args)

      Disables the :class:`SelectMenu` if the passed :attr:`check` returns ``True``.

      :param check: Union[:class:`bool`, Callable]
         The check could be an :class:`bool` or usually any :obj:`Callable` that returns an :class:`bool`.
      :param \*args: Any
         Arguments that should passed in to the :attr:`check` if it is an :obj:`Callable`.

      :return: :class:`SelectMenu`

   .. method:: set_custom_id(custom_id)

      Set the custom_id of the :class:`SelectMenu`

      :param custom_id: Union[:class:`str`, :class:`int`]
         The custom_id to replace the old one with

      :return: :class:`SelectMenu`

________________________________________

.. toctree::   
   :maxdepth: 3
   :caption: Contents:


Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
