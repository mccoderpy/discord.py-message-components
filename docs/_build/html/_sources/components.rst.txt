.. discord.py-message-components documentation master file, created by
   sphinx-quickstart on Sat Jun 26 14:55:47 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Components
==========

:class:`discord.ActionRow(*args, **kwargs)`
___________________________________________

Represents an ``ActionRow``-Part for the components of an :class:`discord.Message`

Attributes
----------

* :attr:`*args`: [Union[:class:`Button`, :class:`SelectionMenu`]]
    An array of :class:`Button`/s and/or :class:`SelectionMenu`/s.

* :attr:`force`: Optional[Bool]
    When set to ``True`` an Empty :class:`ActionRow` will be ignored

.. note::
    For more information about ActionRow's visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#actionrow>`_.

Methodes
--------

:meth:`sendable`: Dict
    Makes the :class:`ActionRow` sendable to discord.

:meth:`disable_all_buttons()`
    Disable all objects's of type :class:`discord.Button` in this :class:`ActionRow`.
    
    :return: :class:`discord.ActionRow`

:meth:`disable_all_buttons_if(check: Union[Bool, Callable], **kwargs)`
    Disable all :class:`discord.Button` in this :class:`ActionRow` if the passed :attr:`check` ``True``.

    **Parameters**

        * :attr:`check`: Union[Bool, Callable]
            could be an :class:`bool` or usually any :obj:`Callable` that returns an :class:`bool`
        
        * :attr:`**kwargs`
            :obj:`kwargs` that should passed in to the :attr:`check` if it is an :obj:`Callable`

    :return: :class:`ActionRow`

:class:`discord.Button(**kwargs)`
_________________________________

Represents an ``Discord-Button``

.. note::
    For more information Discord-Button's visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#buttons>`_.
    
Attributes
----------

:attr:`label`: :class:`str`
    The Text displayed in discord on the Button. Maximal lenght is 80 Chars.
:attr:`custom_id`: Union[:class:`str`, :class:`int`]
    The custom_id discord send us when a User press the Button. The max. lenght of this is 100.
:attr:`style`: Union[:class:`ButtonColor`, :class:`ButtonStyle`, Any[1, 2, 3, 4, 5]]
    The Style of the Button.

    .. note::
        To get more infos about the styles wisit
        `the Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#buttons-button-styles>`_.

:attr:`emoji`: Optional[Union[:class:`discord.PartialEmoji`, :class:`discord.Emoji`, :class:`str`]]
    The Emoji that will be displayed on the left side of the Button.
:attr:`url`: Optional[:class:`str`]
    The url the Button includes

    .. note::
        if you set this, the :attr:`style` will automaticly set to :class:`ButtonStyle.Link_Button`

    .. warning::
        
        You cant pass an :attr:`custom_id` and a :attr:`url` beacuse discord dont send anything when clicking on an ``URL-Button`` so it dont accept both; :attr:`url`/ButtonStyle.Link_Button and :attr:`custom_id`!

:attr:`disabled`: :class:`Bool`
    Whether the Button is disabled; defauld False.


Methodes
--------

:meth:`disable_if`
Disable the :class:`Button` if the passed :attr:`check` returns ``True``.

    * :attr:`check`: typing.Union[bool, typing.Callable]
        Could be an :class:`bool` or usually any :class:`Callable` that returns an :class:`bool`

    * :attr:`**kwargs`: Any[SupportsIndex]
        Arguments that should passed in to the :attr:`check` if it is an :class:`Callable`

    :return: :class:`discord.Button`

:meth:`set_color_if`
Sets the Color(Style) of an :class:`discord.Button` to the provided :attr:`color` if the passed :attr:`check` returns ``True``.
    
    * :attr:`check`: could be an :class:`bool` or usaly any :obj:`Callable` that returns an :class:`bool`
    
    * :attr:`color`: the Color(Style) that should set if the :attr:`check` returns ``True``
   
    * :attr:`**kwargs`: ``kwargs`` that should passed in to the :attr:`check` if it is an :class:`Callable`

    :return: :class:`discord.Button`

.. toctree::   
   :maxdepth: 3
   :caption: Contents: 

Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
