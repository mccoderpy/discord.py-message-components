# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Implementing of the Discord-Message-components made by mccoderpy (Discord-User mccuber04#2960)

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import typing
from .enums import ComponentType, ButtonStyle
from .emoji import Emoji
from typing import Union
from .partial_emoji import PartialEmoji
from .errors import InvalidArgument, InvalidButtonUrl, URLAndCustomIDNotAlowed, EmptyActionRow

__all__ = ('Button', 'SelectMenu', 'ActionRow', 'SelectOption', 'select_option')


class Button:

    """
    :class:`Button`

    Represents an ``Discord-Button``

    .. note ::
        For more information Discord-Button's visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#buttons>`_.
    
    """

    def __init__(self, label: str = None, custom_id: str = None,
                 style: Union[ButtonStyle, int] = ButtonStyle.grey,
                 emoji: Union[PartialEmoji, Emoji, str] = None, url: str = None, disabled: bool = False):
        if url and not url.startswith('http'):
            raise InvalidButtonUrl(url)
        self.url = url
        if isinstance(style, int):
            style = ButtonStyle.from_value(style)
        if not isinstance(style, ButtonStyle):
            raise InvalidArgument("The Style of an discord.Button have to be an Object of discord.ButtonStyle, discord.ButtonColor or usually an Integer between 1 and 5")
        self.style = style
        if int(self.style) == 5 and not self.url:
            raise InvalidArgument('You must also pass a URL if the ButtonStyle is a link.')
        if self.url and int(self.style) != 5:
            self.style = ButtonStyle.Link_Button
        if custom_id and len(custom_id) > 100:
            raise InvalidArgument(
                'The maximum length of Button-custom_id\'s are 100; your one is %s long. (%s Characters to long)' % (len(custom_id), len(custom_id) - 100))
        self.custom_id = custom_id
        if self.custom_id and self.url:
            raise URLAndCustomIDNotAlowed(self.custom_id)
        if label and len(label) > 80:
            raise InvalidArgument('The maximum length of Button-Labels\'s are 80; your one is %s long. (%s Characters to long)' % (len(label), len(label) - 80))
        self.label = label
        if isinstance(emoji, Emoji):
            self.emoji = PartialEmoji(name=emoji.name, animated=emoji.animated, id=emoji.id)
        elif isinstance(emoji, PartialEmoji):
            self.emoji = emoji
        elif isinstance(emoji, str):
            try:
                self.emoji = PartialEmoji.from_string(emoji)
            except ValueError:
                self.emoji = PartialEmoji(name=emoji)
        else:
            self.emoji = None
        self.disabled = disabled

    def __repr__(self) -> str:
        return f'<Button {", ".join(["%s=%s" % (k, str(v)) for k, v in self.__dict__.items()])}'

    def __len__(self):
        if self.label:
            return len(self.label)
        return len(self.emoji)

    def set_label(self, label: str):
        if len(label) > 80:
            raise InvalidArgument('The maximum length of Button-Labels\'s are 80; your one is %s long. (%s Characters to long)' % (len(label), len(label) - 80))
        self.label = label
        return self

    def set_url(self, url: str):
        if not url.startswith('http'):
            raise InvalidButtonUrl(url)
        self.url = url
        return self

    def update(self, **kwargs):
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.__dict__.keys())
        return self

    def set_custom_id(self, custom_id: str):
        if len(custom_id) > 100:
            raise InvalidArgument(
                'The maximum length of Button-custom_id\'s are 100; your one is %s long. (%s Characters to long)' % (len(custom_id), len(custom_id) - 100))
        if self.custom_id and self.url:
            raise URLAndCustomIDNotAlowed(self.custom_id)
        self.custom_id = custom_id
        return self

    def disable_if(self, check: typing.Union[bool, typing.Callable], *args):
        """
        Disable the :class:`discord.Button` if the passed :attr:`check` returns :bool:`True`.

        Parameters
        __________
        check: Union[:class:`bool`, Callable]
            The check could be an :class:`bool` or usually any :obj:`Callable` that returns an :class:`bool`.
        *args: Any
            Arguments that should passed in to the :attr:`check` if it is an :obj:`Callable`.

        :return: :class:`discord.Button`
         """
        try:
            check = check(*args)
        except TypeError:
            pass
        if check is True:
            self.disabled = True
        return self

    def set_color_if(self, check: Union[bool, typing.Callable], color: ButtonStyle, *args):

        try:
            check = check(*args)
        except TypeError:
            pass
        if check is True:
            self.style = color
        return self

    def to_dict(self):
        base = {'type': 2, 'label': self.label, 'style': int(self.style), 'disabled': self.disabled}
        if self.custom_id:
            base['custom_id'] = self.custom_id
        elif self.url:
            base['url'] = self.url
        if self.emoji:
            base['emoji'] = self.emoji.to_dict()
        return base

    @classmethod
    def from_dict(cls, data: dict):
        style = data.get('style', None)
        label = data.get('label', None)
        emoji = data.get('emoji')
        custom_id = data.get('custom_id', None)
        url = data.get('url', None)
        disabled = data.get('disabled', None)

        if emoji and isinstance(emoji, dict):
            emoji = PartialEmoji.from_dict(emoji)

        return cls(style=style, label=label, emoji=emoji, custom_id=custom_id, url=url, disabled=disabled)


class SelectOption:

    """
    A class that creates an Option for a :class:`SelectMenu` and represents them one in an :class:`discord.Message`

    Parameters
    ----------
    label: :class:`str`
        the user-facing name of the option, max 25 characters
    value: :class:`str`
        the dev-define value of the option, max 100 characters
    description: Optional[:class:`str`] = None
        an additional description of the option, max 50 characters
    emoji: Union[:class:`PartialEmoji`, :class:`Emoji`, :class:`str`] = None
        an Emoji that will shown on the left side of the option.
    default: Optional[:class:`bool`] = False
        will render this option as selected by default
    """
    def __init__(self, label: str,
                 value: str,
                 description: str = None,
                 emoji: Union[PartialEmoji, Emoji, str] = None,
                 default: bool = False):

        if len(label) > 25:
            raise AttributeError('The maximum length of the label is 25 characters.')
        self.label = label
        if len(value) > 100:
            raise AttributeError('The maximum length of the value is 100 characters.')
        self.value = value
        if description and len(description) > 50:
            raise AttributeError('The maximum length of the description is 50 characters.')
        self.description = description
        if isinstance(emoji, PartialEmoji):
            self.emoji = emoji
        if isinstance(emoji, Emoji):
            self.emoji = PartialEmoji(name=emoji.name, animated=emoji.animated, id=emoji.id)
        elif isinstance(emoji, str):
            try:
                self.emoji = PartialEmoji.from_string(emoji)
            except ValueError:
                self.emoji = PartialEmoji(name=emoji)
        else:
            self.emoji = None
        self.default = default

    def __repr__(self):
        return f'<SelectOption {", ".join(["%s=%s" % (k, v) for (k, v) in self.__dict__.items()])}>'

    def to_dict(self):
        base = {'label': str(self.label),
                'value': str(self.value),
                'default': bool(self.default)}
        if self.description:
            base['description'] = str(self.description)
        if self.emoji:
            base['emoji'] = self.emoji.to_dict()
        return base

    @classmethod
    def from_dict(cls, data):
        emoji = data.pop('emoji', None)
        if emoji is not None:
            emoji = PartialEmoji.from_dict(emoji)
        return cls(label=data.pop('label'),
                   value=data.pop('value'),
                   description=data.pop('description', None),
                   emoji=emoji,
                   default=data.pop('default', False))


def select_option(label: str, value: str, emoji: Union[PartialEmoji, Emoji, str] = None, description: str = None, default: bool = False) -> dict:
    if isinstance(emoji, PartialEmoji):
        emoji = emoji
    if isinstance(emoji, Emoji):
        emoji = PartialEmoji(name=emoji.name, animated=emoji.animated, id=emoji.id)
    elif isinstance(emoji, str):
        emoji = PartialEmoji(name=emoji)
    else:
        emoji = None
    base = {'label': str(label),
            'value': str(value),
            'default': bool(default)}
    if description:
        base['description'] = str(description)
    if emoji:
        base['emoji'] = emoji.to_dict()
    return base


class SelectMenu:

    """
    Represents an ``Discord-Select-Menu``

    .. note::
        For more information about Select-Menus visit the `Discord-API-Documentation <https://discord.com/developers/docs/interactions/message-components#select-menus>`_.

    """

    __slots__ = ('custom_id', 'options', 'placeholder', 'min_values', 'max_values', 'disabled')

    def __init__(self, custom_id: str,
                 options: typing.List[typing.Union[dict, SelectOption]],
                 placeholder: str = None,
                 min_values: int = 1,
                 max_values: int = 1,
                 disabled: bool = False):
        if not any([isinstance(obj, (SelectOption, dict)) for obj in options]):
            raise InvalidArgument(
                "SelectMenu.options must be a list of SelectOption or dict's like `{'label': 'what to display in Discord',"
                " 'value': 'what the Discord API sends to your application when the option is selected'}`; you can easily create"
                " it with the :function:`discord.components.create_option`.")
        elif len(options) > 25:
            raise InvalidArgument('The maximum number of options in a select menu is 25.')
        self.options = options
        if len(custom_id) > 100:
            raise ValueError('The maximum length of a custom_id is 100 characters; your one is %s long (%s to long).' % (len(custom_id), len(custom_id) - 100))
        self.custom_id = custom_id
        if placeholder and len(placeholder) > 100:
            raise AttributeError('The maximum length of a the placeholder is 100 characters; your one is %s long (%s to long).' % (len(placeholder), len(placeholder) - 100))
        self.placeholder = placeholder
        if min_values > 25 or min_values < 0:
            raise ValueError('The minimum number of elements to be selected must be between 0 and 25.')
        self.min_values = min_values
        if max_values > 25 or max_values <= 0:
            raise ValueError('The maximum number of elements to be selected must be between 0 and 25.')
        self.max_values = max_values
        self.disabled = disabled

    def __repr__(self):
        return f'<SelectMenu {", ".join(["%s=%s" % (k, str(getattr(self, k))) for k in self.__slots__])}>'

    def to_dict(self) -> dict:
        base = {
            'type': 3,
            'custom_id': self.custom_id,
            'options': [o.to_dict() for o in self.options if isinstance(o, SelectOption)],
            'placeholder': self.placeholder,
            'min_values': self.min_values,
            'max_values': self.max_values
        }
        if self.disabled is True:
            base['disabled'] = True
        return base

    def update(self, **kwargs):
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.__slots__)
        return self

    def set_custom_id(self, custom_id: str):
        if len(custom_id) > 100:
            raise InvalidArgument(
                'The maximum length of SelectMenu-custom_id\'s are 100; your one is %s long. (%s Characters to long)' % (len(custom_id), len(custom_id) - 100))
        self.custom_id = custom_id
        return self

    def disable_if(self, check: typing.Union[bool, typing.Callable], *args):
        """
        Disable the :class:`discord.SelectMenu` if the passed :param:`check` returns :bool:`True`.

        Parameters
        ----------
        check: Union[:class:`bool`, Callable]
            The check could be an :class:`bool` or usually any :obj:`Callable` that returns an :class:`bool`.
        *args: Any
            Arguments that should passed in to the :param:`check` if it is an :obj:`Callable`.

        :return: :class:`discord.Button`
         """
        try:
            check = check(*args)
        except TypeError:
            pass
        if check is True:
            self.disabled = True
        return self

    @classmethod
    def from_dict(cls, data: dict):
        return cls(custom_id=data.pop('custom_id'),
                   options=[SelectOption.from_dict(o) for o in data.pop('options')],
                   placeholder=data.pop('placeholder', None),
                   min_values=data.pop('min_values', 1),
                   max_values=data.pop('max_values', 1))


class ActionRow:
    def __init__(self, *components):
        """
        Represents an ActionRow-Part for the components of an :class:`discord.Message`.

        Parameters
        ----------

        components: Array[Union[:class:`Button, :class:`SelectMenu`]]
            The components the :class:`ActionRow` should have. It could contain at least 5 :class:`Button`or 1 :class:`SelectMenu`.

        .. note ::
            For more information about ActionRow's visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#actionrow>`_.
        """
        self.components = []
        for obj in components:
            if isinstance(obj, Button):
                self.components.append(obj)
            elif isinstance(obj, SelectMenu):
                self.components.append(obj)
            elif isinstance(obj, dict):
                if not obj.get('type', None) in [2, 3]:
                    raise InvalidArgument('If you use an Dict instead of Button or SelectMenu you have to pass an type between 2 or 3')
                self.components.append({2: Button.from_dict(obj), 3: SelectMenu.from_dict(obj)}.get(obj.get('type')))
    
    def __repr__(self):
        return f'<ActionRow components={self.components}>'

    def sendable(self) -> Union[list, EmptyActionRow]:
        base = []
        base.extend([{'type': 1, 'components': [obj.to_dict() for obj in self.components[five:5:]]} for five in range(0, len(self.components), 5)])
        objects = len([i['components'] for i in base])
        if any([any([part['type'] == 2]) and any([part['type'] == 3]) for part in base]):
            raise InvalidArgument('An Action Row containing a select menu cannot also contain buttons')
        elif any([any([part['type'] == 3]) and len(part) > 1 for part in base]):
            raise InvalidArgument('An Action Row can contain only one Select Menu')
        if any([len(ar['components']) < 1 for ar in base]):
            raise EmptyActionRow()
        elif len(base) > 5 or objects > 25:
            raise InvalidArgument(f"The maximum number of ActionRow's per message is 5 and they can only contain 5 Buttons or 1 Select-Menu each; you have {len(base)} ActionRow's passed with {objects} objects")
        return base

    def __len__(self):
        return len(self.components)

    def __invert__(self):
        return self.components

    def __add__(self, other):
        return self.add_components(other)

    def add_component(self, component: Union[Button, SelectMenu, dict]):
        """Adds a component to the :class:`ActionRow`.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 1.7.5.1

        Parameters
        -----------
        component: Union[:class:`Button`, :class:`SelectMenu`, :class`dict`]
            The component to add to the ActionRow.
        """
        self.components.append(component)
        return self

    def insert_component_at(self, index, component: Union[Button, SelectMenu, dict]):
        """Inserts a component before a specified index to the :class:`ActionRow`.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 1.7.5.1

        Parameters
        -----------
        index: :class:`int`
            The index of where to insert the component.
        component: Union[:class:`Button`, :class:`SelectMenu`, :class`dict`]
            The component to insert.
        """
        self.components.insert(index, component)
        return self

    def set_component_at(self, index, component: Union[Button, SelectMenu, dict]):
        """Modifies a component to the ActionRow object.

        The index must point to a valid pre-existing field.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 1.7.5.1

        Parameters
        ----------
        index: :class:`int`
            The index of the component to modify.
        component: Union[:class:`Button`, :class:`SelectMenu`, :class:`dict`]
            The component to replace the old one with.

        Raises
        -------
        IndexError
            An invalid index was provided.
        """
        try:
            _component = self.components[index]
        except IndexError:
            raise IndexError('component index out of range')
        _component = component
        return self

    def add_components(self, *components: Union[Button, SelectMenu, dict]):
        """Adds an array of components to the :class:`ActionRow` object.

        Parameters
        ----------
        components: *Union[:class:`Button`, :class:`SelectMenu`, :class:`dict`]
            The components to add to the ActionRow.

        Returns
        -------
            ActionRow
        """
        self.components.extend(*components)
        return self

    def disable_all_buttons(self):
        """Disable all :type:`object`'s of type :class:`discord.Button` in this :class:`ActionRow`.

        :return: :class`discord.ActionRow`
        """
        [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, Button)]
        return self

    def disable_all_buttons_if(self, check: Union[bool, typing.Callable], *args: typing.Any):
        """Disable all :class:`discord.Button` in this :class:`ActionRow` if the passed :attr:`check` returns :bool:`True`.
    
        Parameters
        -----------
        check: Union[:class:`bool`, :class:`typing.Callable`]
            Could be an bool or usually any Callable that returns a bool.
        args: typing.Any
            Arguments that should passed in to the check if it is a Callable.

        :return: :class:`discord.ActionRow`
        """
        if not isinstance(check, (bool, typing.Callable)):
            raise AttributeError('The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check))
        try:
            check = check(*args)
        except TypeError:
            pass
        if check is True:
            [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, Button)]
        return self

    def disable_all_selectmenus(self):
        """Disable all :type:`object`'s of type :class:`discord.SelectMenu` in this :class:`ActionRow`.

        :return: :class`discord.ActionRow`
        """
        [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, SelectMenu)]
        return self

    def disable_all_selectmenus_if(self, check: Union[bool, typing.Callable], *args: typing.Any):
        """Disable all :class:`SelectMenu` in this :class:`ActionRow` if the passed :param:`check` returns :bool:`True`.

        Parameters
        ----------
        check: Union[:class:`bool`, :class:`typing.Callable`]
            could be an :class:`bool` or usually any :obj:`Callable` that returns a :class:`bool`
        args: Any
            Arguments that should passed in to the :param:`check` if it is a :obj:`Callable`.

        :return: :class:`discord.ActionRow`
        """
        if not isinstance(check, (bool, typing.Callable)):
            raise AttributeError('The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check))
        try:
            check = check(*args)
        except TypeError:
            pass
        if check is True:
            [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, SelectMenu)]
        return self

    @property
    def raw(self) -> dict:
        for c in self.components:
            yield c

    @classmethod
    def from_dict(cls, data):
        if data.get('type', None) != 1:
            return InvalidArgument("%s could not be implemented as an ActionRow" % data)
        else:
            components = [_component_factory(component) for component in data.get('components', [])]
            return cls(*components)


class DecodeMessageComponents:
    def __init__(self, value):
        self.action_rows = []
        self.other_elements = []
        for obj in value:
            try:
                self.action_rows.append(ActionRow.from_dict(obj))
            except InvalidArgument:
                self.other_elements.append(obj)
        if self.other_elements:
            raise InvalidArgument(f"Invalid Type(s): {[o for o in self.other_elements]} is/are of type(s) {[type(o) for o in self.other_elements]} but has to bee an discord.ActionRow.")


def _component_factory(data):
    component_type = data.get('type', None)
    if component_type == ComponentType.ActionRow:
        return ActionRow.from_dict(data)
    elif component_type == ComponentType.Button:
        return Button.from_dict(data)
    elif component_type == ComponentType.SelectMenu:
        return SelectMenu.from_dict(data)
    else:
        return None
