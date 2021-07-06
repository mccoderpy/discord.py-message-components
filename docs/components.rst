.. discord.py-message-components documentation master file, created by
   sphinx-quickstart on Sat Jun 26 14:55:47 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Components
==========

.. _buttoncolor:

:class:`discord.ButtonColor`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    * ``blurple`` = 1
    * ``grey`` = 2
    * ``green`` = 3
    * ``red`` = 4
    * ``grey_url`` (navigates to an URL) = 5

___________________________________________

.. _actionrow:

:class:`discord.ActionRow(*args, **kwargs)`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Represents an ``ActionRow``-Part for the components of a :class:`discord.Message`

.. note::

    You could use a :class:`list` instead of this but you dont have the functions and parameters of this class then.

.. _actionrow-parameters:

Parameters
-----------

    * :attr:`*args`: Union[[:class:`Button`], :class:`SelectMenu`]
        An array of :class:`Button`/s and/or :class:`SelectnMenu`/s.

    .. _actionrow-force:

    * :attr:`force`: Optional[Bool]
        When set to ``True`` an Empty :class:`ActionRow` will be ignored

    .. note::
        For more information about ActionRow's visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#actionrow>`_.

.. _actionrow-methods:

Methods
--------
    .. _actionrow-sendable:

    :meth:`sendable` -> Dict
        Makes the :class:`ActionRow` sendable to discord.

    .. _actionrow-disable_all_buttons:

    :meth:`disable_all_buttons()`
        Disable all objects's of type :class:`discord.Button` in this :class:`ActionRow`.
        
        :return: :class:`discord.ActionRow`
    
    .. _actionrow-disable_all_buttons_if:

    :meth:`disable_all_buttons_if(check: Union[Bool, Callable], **kwargs)`
        Disable all :class:`discord.Button` in this :class:`ActionRow` if the passed :attr:`check` ``True``.

        **Parameters**

            * :attr:`check`: Union[Bool, Callable]
                could be a :class:`bool` or usually any :obj:`Callable` that returns a :class:`bool`
            
            * :attr:`**kwargs`
                :obj:`kwargs` that should passed in to the :attr:`check` if it is a :obj:`Callable`

        :return: :class:`ActionRow`

________________________________________

.. _button:

:class:`discord.Button(**kwargs)`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Represents a ``Discord-Button``

.. note::
    For more information Discord-Button's visit the `Documentation <https://discord.com/developers/docs/interactions/message-components#buttons>`_ of the discord-api.

.. _button-parameters:

Parameters
-----------

    .. _button-label:

    :attr:`label`: :class:`str`
        The Text displayed in discord on the Button. Maximal lenght is 80 Chars.
    
    .. _button-custom_id:

    :attr:`custom_id`: Union[:class:`str`, :class:`int`]
        The custom_id discord send us when a User press the Button. The max. lenght of this is 100.
    
    .. _button-style:

    :attr:`style`: Union[:class:`ButtonColor`, :class:`ButtonStyle`, Any[1, 2, 3, 4, 5]]
        The Style of the Button.

        .. note::
            To get more infos about the styles wisit
            `the Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#buttons-button-styles>`_.

    .. _button-emoji:

    :attr:`emoji`: Optional[Union[:class:`discord.PartialEmoji`, :class:`discord.Emoji`, :class:`str`]]
        The Emoji that will be displayed on the left side of the Button.

    .. _button-url:

    :attr:`url`: Optional[:class:`str`]
        The URL the Button links too.

        .. note::
            If you set this, the :attr:`style` will automaticly set to :class:`ButtonStyle.Link_Button`

        .. warning::
            
            You can't pass a :attr:`custom_id` and a :attr:`url` beacuse discord dont send anything when clicking on an ``URL-Button`` so it dont accept both; :attr:`url`/ButtonStyle.Link_Button and :attr:`custom_id`!
    
    .. _button-disabled:

    :attr:`disabled`: :class:`Bool`
        Whether the Button is disabled; defauld False.

.. _button-methods:

Methods
--------

    .. _button-disable_if:

    :meth:`disable_if`
    
    Disable the :class:`Button` if the passed :attr:`check` returns ``True``.
        * :attr:`check`: typing.Union[bool, typing.Callable]
            Could be a :class:`bool` or usually any :class:`Callable` that returns a :class:`bool`
        * :attr:`**kwargs`: Any[SupportsIndex]
            Arguments that should passed in to the :attr:`check` if it is a :class:`Callable`

        :return: :class:`discord.Button`
    
    .. _button-set_color_if:

    :meth:`set_color_if`

    Sets the Color(Style) of a :class:`discord.Button` to the provided :attr:`color` if the passed :attr:`check` returns ``True``.
        
        * :attr:`check`: could be a :class:`bool` or usally any :obj:`Callable` that returns a :class:`bool`
        
        * :attr:`color`: the Color(Style) that should set if the :attr:`check` returns ``True``
    
        * :attr:`**kwargs`: ``kwargs`` that should passed in to the :attr:`check` if it is a :class:`Callable`

        :return: :class:`discord.Button`

________________________________________

.. _select_option:

:func:`select_option`
~~~~~~~~~~~~~~~~~~~~~
Builds you a dict which can be used as an option for a :class:`SelectMenu`

.. _select-option-parameters:

Paramerts
----------

    :attr:`label`: str
        The user-facing name of the option, max 25 characters
    
    :attr:`value`: str
        The dev-define value of the option, max 100 characters

    :attr:`description`: Optional[str]
    	An additional description of the option, max 50 characters
    
    :attr:`emoji`: Optional[int]
        The minimum number of items that must be chosen; default 1, min 0, max 25
    
    :attr:`max_values`: Optional[int]
        The maximum number of items that can be chosen; default 1, max 25

:return: :class:`dict`
    
________________________________________

.. _select-menu:

:class:`SelectMenu(custom_id, options, placeholder, min_values, ...)`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Represents a ``Discord-Select-Menu``

.. note::
    For more information about Select-Menus wisit the `Discord-API-Documentation <https://discord.com/developers/docs/interactions/message-components#select-menus>`_.

.. _select-menu-parameters:

Parameters
-----------

    .. _select-menu-custom_id:

    :attr:`custom_id`: str
        A developer-defined identifier for the :class:`SelectMenu`, max. 100 characters
    
    .. _select-menu-options:

    :attr:`options`: List[Dict]
        A :class:`list` of choices the :class:`SelectMenu` should have, max. 25

        use `select_option` to create an option
    
    .. _select-menu-placeholder:

    :attr:`placeholder`: Optional[str]
        Custom placeholder text if nothing is selected, max. 100 characters

    .. _select-menu-min_values:

    :attr:`min_values`: Optional[int]
        The minimum number of items that must be chosen; default 1, min. 0, max. 25.
    
    .. _select-menu-max_values:

    :attr:`max_values`: Optional[int]
        The maximum number of items that can be chosen; default 1, max. 25.
    
    .. _select-menu-disabled:

    :attr:`disabled`: Optional[Bool]
        Whether the SelectMenu is disabled or not. ``False`` by default.


________________________________________

.. toctree::   
   :maxdepth: 2
   :caption: Contents: 

Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
