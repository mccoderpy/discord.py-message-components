# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2021-present mccoderpy

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
from __future__ import annotations

from .enums import ComponentType, ButtonStyle, TextInputStyle
from .emoji import Emoji
from .partial_emoji import PartialEmoji
from .errors import InvalidArgument, URLAndCustomIDNotAlowed

from typing import (
    Any,
    Union,
    List,
    Dict,
    Optional,
    Callable
)
from typing_extensions import Literal

__all__ = (
    'Button',
    'SelectMenu',
    'TextInputStyle',
    'ActionRow',
    'SelectOption'
)


class Button:

    """
    Represents an `Discord-Button <https://discord.com/developers/docs/interactions/message-components#button-object>`_

    Parameters
    ----------
    label: Optional[:class:`str`] = None
        text that appears on the button, max 80 characters
    custom_id: Optional[Union[:class:`str`, :class:`int`]] = None
        a developer-defined identifier for the button, max 100 characters
    style: Optional[Union[:class:`ButtonStyle`, :class:`int`]] = ButtonStyle.grey
        The Style the Button should have
    emoji: Optional[Union[:class:`discord.PartialEmoji`, :class:`discord.Emoji`, :class:`str`]] = None
        The Emoji that will be displayed on the left side of the Button.
    url: Optional[:class:`str`]
        a url for link-style buttons
    disabled: Optional[:class:`bool`] = False
        whether the button is disabled (default False)

    """

    def __init__(self,
                 label: str = None,
                 custom_id: Union[str, int] = None,
                 style: Union[ButtonStyle, int] = ButtonStyle.grey,
                 emoji: Union[PartialEmoji, Emoji, str] = None,
                 url: str = None,
                 disabled: bool = False):
        if url and not url.startswith(('http://', 'https://', 'discord://')):
            raise ValueError(f'"{url}" is not a valid protocol. Only http(s) or discord protocol is supported')
        self.url: Optional[str] = url
        if isinstance(style, int):
            style = ButtonStyle.from_value(style)
        if not isinstance(style, ButtonStyle):
            raise InvalidArgument("The Style of an discord.Button have to be an Object of discord.ButtonStyle, discord.ButtonColor or usually an Integer between 1 and 5")
        self.style = style
        if self.style == ButtonStyle.url and not self.url:
            raise InvalidArgument('You must also pass a URL if the ButtonStyle is a link.')
        if self.url and int(self.style) != 5:
            self.style = ButtonStyle.Link_Button
        if custom_id and len(custom_id) > 100:
            raise InvalidArgument(
                'The maximum length of Button-custom_id\'s are 100; your one is %s long. (%s Characters to long)' % (len(custom_id), len(custom_id) - 100))
        if isinstance(custom_id, str) and custom_id.isdigit():
            self.custom_id = int(custom_id)
        else:
            self.custom_id = custom_id
        if self.custom_id is not None and self.url:
            raise URLAndCustomIDNotAlowed(self.custom_id)
        if label and len(label) > 80:
            raise InvalidArgument('The maximum length of Button-Labels\'s are 80; your one is %s long. (%s Characters to long)' % (len(label), len(label) - 80))
        self.label = label
        if isinstance(emoji, Emoji):
            self.emoji = PartialEmoji(name=emoji.name, animated=emoji.animated, id=emoji.id)
        elif isinstance(emoji, PartialEmoji):
            self.emoji = emoji
        elif isinstance(emoji, str):
            if emoji[0] == '<':
                self.emoji = PartialEmoji.from_string(emoji)
            else:
                self.emoji = PartialEmoji(name=emoji)
        else:
            self.emoji = None
        self.disabled = disabled

    def __repr__(self) -> str:
        return f'<Button {", ".join(["%s=%s" % (k, str(v)) for k, v in self.__dict__.items()])}>'

    def __len__(self):
        if self.label:
            return len(self.label)
        return len(self.emoji)

    def set_label(self, label: str):
        """
        Sets the Label of the :class:`Button`

        label: :class`str`
            The label to replace th old one with.

        Returns
        -------
        :class:`~discord.Button`
            The updated instance
        """
        if len(label) > 80:
            raise InvalidArgument('The maximum length of Button-Labels\'s are 80; your one is %s long. (%s Characters to long)' % (len(label), len(label) - 80))
        self.label = label
        return self

    def set_url(self, url: str):
        """
        Sets the url of the :class:`Button`

        url: :class:`str`
            The url to replace the old one with

        Returns
        -------
        :class:`~discord.Button`
            The updated instance
        """
        if not url.startswith(('http://', 'https://', 'discord://')):
            raise ValueError(f'"{url}" is not a valid protocol. Only http(s) or discord protocol is supported')
        self.url = url
        return self

    def update(self, **kwargs):
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.__dict__.keys())
        return self

    def set_custom_id(self, custom_id: Union[str, int]):
        """
        Sets the custom_id of the :class:`Button`

        custom_id: Union[:class:`str`, :class:`int`]
            The custom_id to replace the old one with

        Returns
        --------
        :class:`~discord.Button`
            The updated instance
        """
        if self.url:
            raise URLAndCustomIDNotAlowed(custom_id)
        if len(custom_id) > 100:
            raise InvalidArgument(
                'The maximum length of Button-custom_id\'s are 100; your one is %s long. (%s Characters to long)' % (len(custom_id), len(custom_id) - 100))
        if isinstance(custom_id, str) and custom_id.isdigit():
            self.custom_id = int(custom_id)
        else:
            self.custom_id = custom_id
        return self

    def disable_if(self, check: Union[bool, Callable], *args):
        """
        Disables the :class:`~discord.Button` if the passed :attr:`check` returns ``True``.

        Parameters
        ----------
        check: Union[:class:`bool`, :class:`typing.Callable`]
            The check could be an :class:`bool` or usually any :class:`Callable` that returns an :class:`bool`.
        \*args: Any
            Arguments that should be passed in to the :attr:`check` if it is an :class:`Callable`.

        Returns
        -------
        :class:`~discord.Button`
            The updated instance
         """
        try:
            check = check(*args)
        except TypeError:
            pass
        if check is True:
            self.disabled = True
        return self

    def set_style_if(self, check: Union[bool, Callable], style: ButtonStyle, *args):
        """
        Sets the style of the :class:`Button` to the specified one if the specified check returns True.

        Parameters
        ----------
        check: Union[:class:`bool`, :class:`typing.Callable`]
            The check could be an :class:`bool` or usually any :class:`Callable` that returns an :class:`bool`
        style: discord.ButtonStyle
            The style the :class:`Button` should have when the :attr:`check` returns True
        *args: Any
            Arguments that should be passed in to the :attr:`check` if it is an :class:`Callable`.

        Returns
        -------
        :class:`~discord.Button`
            The updated instance

        """
        try:
            check = check(*args)
        except TypeError:
            pass
        if check is True:
            self.style = style
        return self

    def to_dict(self):
        base = {'type': 2, 'label': self.label, 'style': int(self.style), 'disabled': self.disabled}
        if self.custom_id is not None:
            base['custom_id'] = str(self.custom_id)
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
    A class that creates an option for a :class:`SelectMenu`
    and represents it in a :class:`SelectMenu` in the components of a :class:`discord.Message`.

    Parameters
    ----------
    label: :class:`str`
        the user-facing name of the option, max 25 characters
    value: :class:`str`
        the dev-define value of the option, max 100 characters
    description: Optional[:class:`str`] = None
        an additional description of the option, max 50 characters
    emoji: Union[:class:`PartialEmoji`, :class:`Emoji`, :class:`str`] = None
        an Emoji that will be shown on the left side of the option.
    default: Optional[:class:`bool`] = False
        will render this option as selected by default

    """
    def __init__(self, label: str,
                 value: str,
                 description: str = None,
                 emoji: Union[PartialEmoji, Emoji, str] = None,
                 default: bool = False):
        if len(label) > 100:
            raise AttributeError('The maximum length of the label is 100 characters.')
        self.label = label
        if len(value) > 100:
            raise AttributeError('The maximum length of the value is 100 characters.')
        self.value = value
        if description and len(description) > 100:
            raise AttributeError('The maximum length of the description is 100 characters.')
        self.description = description
        if isinstance(emoji, PartialEmoji):
            self.emoji = emoji
        elif isinstance(emoji, Emoji):
            self.emoji = PartialEmoji(name=emoji.name, animated=emoji.animated, id=emoji.id)
        elif isinstance(emoji, str):
            if emoji[0] == '<':
                self.emoji = PartialEmoji.from_string(emoji)
            else:
                self.emoji = PartialEmoji(name=emoji)
        else:
            self.emoji = None
        self.default = default

    def __repr__(self):
        return f'<SelectOption {", ".join(["%s=%s" % (k, v) for (k, v) in self.__dict__.items()])}>'

    def set_default(self, value: bool):
        self.default = value
        return self

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
        if emoji:
            emoji = PartialEmoji.from_dict(emoji)
        return cls(label=data.pop('label'),
                   value=data.pop('value'),
                   description=data.pop('description', None),
                   emoji=emoji,
                   default=data.pop('default', False))


class SelectMenu:

    """
    Represents a `Select-Menu <https://discord.com/developers/docs/interactions/message-components#select-menus>`_

    Parameters
    ----------
    custom_id: str or int
        A developer-defined identifier for the :class:`SelectMenu`, max. 100 characters.
    options: List[:class:`SelectOption`]
        A :class:`list` of choices(:class:`SelectOption`) the :class:`SelectMenu` should have, max. 25.
    placeholder: Optional[:class:`str`] = None
        Custom placeholder text if nothing is selected, max. 100 characters.
    min_values: Optional[:class:`int`] = 1
        The minimum number of items that must be chosen; default 1, min. 0, max. 25.
    max_values: Optional[:class:`int`] = 1
        The maximum number of items that can be chosen; default 1, max. 25.
    disabled: Optional[:class:`bool`] ) = False
        disable the SelectMenu, default False
    """

    def __init__(self, custom_id: Union[str, int],
                 options: List[SelectOption],
                 placeholder: str = None,
                 min_values: int = 1,
                 max_values: int = 1,
                 disabled: bool = False):
        if not any([isinstance(obj, SelectOption) for obj in options]):
            raise InvalidArgument("SelectMenu.options must be a list of discord.SelectOption")
        if len(options) > 25:
            raise InvalidArgument('The maximum number of options in a SelectMenu is 25.')
        self.options = options
        if len(custom_id) > 100:
            raise ValueError('The maximum length of a custom_id is 100 characters; your one is %s long (%s to long).' % (len(custom_id), len(custom_id) - 100))
        if isinstance(custom_id, str) and custom_id.isdigit():
            self.custom_id = int(custom_id)
        else:
            self.custom_id = custom_id
        if placeholder and len(placeholder) > 150:
            raise AttributeError('The maximum length of a the placeholder is 100 characters; your one is %s long (%s to long).' % (len(placeholder), len(placeholder) - 100))
        self.placeholder = placeholder
        if 25 < min_values < 0:
            raise ValueError('The minimum number of elements to be selected must be between 1 and 25.')
        self.min_values = min_values
        if 25 < max_values <= 0:
            raise ValueError('The maximum number of elements to be selected must be between 0 and 25.')
        self.max_values = max_values
        self.disabled = disabled
        self._values = None

    def __repr__(self):
        return f'<SelectMenu {", ".join(["%s=%s" % (k, v) for k, v in self.__dict__.items()])}>'

    @property
    def all_option_values(self):
        """
        All values of the :attr:`options`

        If the value is a number it is returned as an integer, otherwise as string

        .. note::
            This is equal to

            .. code-block:: python3

                for option in self.options:
                    if option.value.isdigit():
                        yield int(option.value)
                    else:
                        yield option.value
        """
        for option in self.options:
            if option.value.isdigit():
                yield int(option.value)
            else:
                yield option.value

    def to_dict(self) -> dict:
        base = {
            'type': 3,
            'custom_id': str(self.custom_id),
            'options': [o.to_dict() for o in self.options if isinstance(o, SelectOption)],
            'placeholder': self.placeholder,
            'min_values': self.min_values,
            'max_values': self.max_values
        }
        if self.disabled is True:
            base['disabled'] = True
        return base

    @property
    def values(self):
        """
        The options that were selected

        .. note::
            This only exists if the :class:`SelectMenu` is passed as a parameter in an interaction.

        .. important::
            If the value is a number it is returned as an integer, otherwise as string

        Returns
        --------
        List[Union[:class:`int`, :class:`str`]]
            A list of selected options
        """
        values = []
        _values = getattr(self, '_values', [])
        for value in _values:
            if value.isdigit():
                values.append(int(value))
            else:
                values.append(value)
        return values

    @property
    def not_selected(self):
        """
        The options that were **not** selected

        .. note::
            This only exists if the :class:`SelectMenu` is passed as a parameter in an interaction.

        .. important::
            If the value is a number it is returned as an integer, otherwise as string

        Returns
        --------
        List[Union[:class:`int`, :class:`str`]]
            A list of **not** selected options
        """
        _not_selected = []
        values = self.values
        for value in self.all_option_values:
            if value not in values:
                _not_selected.append(value)
        return _not_selected

    def update(self, **kwargs):
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.__dict__.keys())
        return self

    def set_custom_id(self, custom_id: Union[str, int]):
        """
        Set the custom_id of the :class:`SelectMenu`

        Parameters
        ----------

        custom_id: Union[:class:`str`, :class:`int`]
            The custom_id to replace the old one with

        Returns
        -------
        :class:`~discord.SelectMenu`
            The updated instance
        """
        if len(custom_id) > 100:
            raise InvalidArgument(
                'The maximum length of SelectMenu-custom_id\'s are 100; your one is %s long. (%s Characters to long)' % (len(custom_id), len(custom_id) - 100))
        if isinstance(custom_id, str) and custom_id.isdigit():
            self.custom_id = int(custom_id)
        else:
            self.custom_id = custom_id
        return self

    def disable_if(self, check: Union[bool, Callable], *args):
        """
        Disables the :class:`discord.SelectMenu` if the passed :attr:`check` returns ``True``.


        Parameters
        ----------
        check: Union[:class:`bool`, :class:`typing.Callable`]
            The check could be an :class:`bool` or usually any :obj:`Callable` that returns an :class:`bool`.
        \*args: Any
            Arguments that should be passed in to the :attr:`check` if it is an :class:`Callable`.

        Returns
        -------
        :class:`~discord.SelectMenu`
            The updated instance
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


class Modal:
    """
    Represents a `Modal <https://discord.com/developers/docs/interactions/receiving-and-responding#interaction-response-object-modal>`_

    Parameters
    ----------
    custom_id: :class:`str`
        A developer-defined identifier for the component, max 100 characters
    title: :class:`str`
        The title of the popup modal, max 45 characters
    components: List[Union[ActionRow, List[TextInput], TextInput]]
        Between 1 and 5 (inclusive) components that make up the modal.
    """
    def __init__(self,
                 title: str,
                 custom_id: str,
                 components: List[Union['ActionRow', List['TextInput']]]) -> None:
        # TODO: Add Error handling
        self.title = title
        self.custom_id = custom_id
        self.components: List[ActionRow] = []
        for c in components:
            if isinstance(c, list):
                c = ActionRow(*c)
            elif not isinstance(c, ActionRow):
                c = ActionRow(c)
            self.components.append(c)

    def to_dict(self):
        components = []
        for a in self.components:
            components.extend(a.to_dict())
        return {
            'custom_id': self.custom_id,
            'title': self.title,
            'components': components
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            custom_id=data['custom_id'],
            title=data['title'],
            components=_component_factory(data['components']))


class TextInput:
    """
    Represents a `TextInput <https://discord.com/developers/docs/interactions/message-components#text-inputs>`_


    Parameters
    ----------
    custom_id: Optional[Union[:class:`str`, :class:`int`]]
        A developer-defined identifier for the input, max 100 characters
    style: Optional[Union[:class:`TextInputStyle`, :class:`int`]] = TextInputStyle.short
        The Style of the TextInput; so single- or multi-line
    label: :class:`str`
        The label for this component, max 45 characters
    min_length: Optional[:class:`int`]
        The minimum input length for a text input, min 0, max 4000
    max_length: Optional[:class:`int`]
        The maximum input length for a text input, min 1, max 4000
    required: Optional[:class:`bool`] = True
        Whether this component is required to be filled, default True
    value: Optional[:class:`str`]
        A pre-filled value for this component, max 4000 characters
    placeholder: Optional[:class:`str`]
        Custom placeholder text if the input is empty, max 100 characters
    """
    def __init__(self,
                 label: str,
                 custom_id: str,
                 style: Union[TextInputStyle, Literal[1, 2]] = 1,
                 min_length: Optional[int] = None,
                 max_length: Optional[int] = None,
                 required: Optional[bool] = True,
                 value: Optional[str] = None,
                 placeholder: Optional[str] = None) -> None:
        self.label: Optional[str] = label
        self.custom_id: Optional[str] = custom_id
        self.style: Union[TextInputStyle, Literal[1, 2]] = style
        self.min_length: Optional[int] = min_length
        self.max_length: Optional[int] = max_length
        self.required: bool = required
        self.value: Optional[str] = value
        self.placeholder: Optional[str] = placeholder

    def to_dict(self) -> dict:
        return {
            'type': 4,
            'label': self.label,
            'custom_id': self.custom_id,
            'style': int(self.style),
            'min_length': self.min_length,
            'max_length': self.max_length,
            'required': self.required,
            'value': self.value,
            'placeholder': self.placeholder
        }

    @classmethod
    def from_dict(cls, data):
        new = cls.__new__(cls)
        for attr in ('type', 'label', 'custom_id', 'style', 'min_length', 'max_length', 'required', 'value', 'placeholder'):
            try:
                new.__setattr__(attr, data[attr])
            except KeyError:
                continue
        return new


class ActionRow:

    """
    Represents an ActionRow-Part for the components of an :class:`discord.Message`.

    .. note ::

        For more information about ActionRow's visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#actionrow>`_.

    Parameters
    -----------
    \*components: \*Union[:class:`Button`, :class:`SelectMenu`]
        The components the :class:`ActionRow` should have. It could contain at least 5 :class:`Button`, or 1 :class:`SelectMenu`.
    """

    def __init__(self, *components):
        self.components = []
        for component in components:
            if isinstance(component, (Button, SelectMenu, TextInput)):
                self.components.append(component)
            elif isinstance(component, self.__class__):
                raise InvalidArgument('An ActionRow could not contain another ActionRow')
            elif isinstance(component, dict):
                if not component.get('type', None) in [2, 3, 4]:
                    raise InvalidArgument('If you use a Dict instead of Button, SelectMenu or TextInput you have to provide the type')
                self.components.append({2: Button, 3: SelectMenu, 4: TextInput}.get(component.get('type')).from_dict(component))
    
    def __repr__(self):
        return f'<ActionRow components={self.components}>'

    def __iter__(self):
        for component in self.components:
            yield component

    def to_dict(self) -> List[Dict[str, Union[int, List[Dict[str, Any]]]]]:
        base = [{'type': 1, 'components': [obj.to_dict() for obj in self.components[five:5:]]} for five in range(0, len(self.components), 5)]
        base_length = len(base)

        if base_length > 5:
            raise InvalidArgument('A message could only contain up to 5 ActionRows')            
        elif 25 < sum([len(ar['components']) for ar in base]) < 1:
            raise InvalidArgument('The max. sum of the components of all ActionRows of a message is 25 and an ActionRow cannot be empty.')
        
        max_rows_reached = base_length == 5

        for row_index, row in enumerate(base):
            components = row['components']
            row_components_count = len(components)
            for c_index, c in enumerate(components):
                t = c['type']
                if t == 1:
                    raise ValueError('An ActionRow can not contain another ActionRow')
                elif t > 2 and row_components_count > 1:
                    if max_rows_reached:
                        raise ValueError('An ActionRow containing a %s cannot contain other components', ComponentType(t).name)
                    base.insert(row_index + 1, {'type': 1, 'components': [base[row_index]['components'].pop(c_index)]})
                    row_components_count -= 1
                    max_rows_reached = len(base)

        return base

    def __len__(self):
        return len(self.components)

    def __invert__(self):
        return self.components

    def __getitem__(self, item) -> Union[Button, SelectMenu, TextInput]:
        return self.components[item]

    def __setitem__(self, index, component):
        return self.set_component_at(index, component)

    def add_component(self, component: Union[Button, SelectMenu]):
        """
        Adds a component to the :class:`ActionRow` and returns the action row.

        Parameters
        ----------
        component: Union[:class:`Button`, :class:`SelectMenu`]
            The component to add to the ActionRow.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        self.components.append(component)
        return self

    def insert_component_at(self, index, component: Union[Button, SelectMenu]):
        """
        Inserts a component before a specified index to the :class:`ActionRow` and returns the action row.

        Parameters
        -----------
        index: :class:`int`
            The index of where to insert the component.
        component: Union[:class:`Button`, :class:`SelectMenu`]
            The component to insert.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        self.components.insert(index, component)
        return self

    def set_component_at(self, index, component: Union[Button, SelectMenu]):
        """
        Modifies a component to the :class:`ActionRow`. and returns the action row.

        .. note::
            The index must point to a valid pre-existing component.

        Parameters
        ----------
        index: :class:`int`
            The index of the component to modify.
        component: Union[:class:`Button`, :class:`SelectMenu`]
            The component to replace the old one with.

        Raises
        -------
        IndexError
            An invalid index was provided.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        try:
            self.components[index]
        except IndexError:
            raise IndexError('component index %s out of range' % index)
        self.components[index] = component
        return self

    def disable_component_at(self, index):
        """
        Disables the component at the specified position and returns the action row.

        Parameters
        ----------
        index: :class:`int`
            The position of the component to be deactivated in the ActionRow.

        Raises
        ------
        :exc:`IndexError`
            The specified index is outside the length of the actionRow.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        try:
            component = self.components[index]
        except IndexError:
            raise IndexError('component index %s out of range' % index)
        component.disabled = True
        return self

    def add_components(self, *components: Union[Button, SelectMenu]):
        """
        Adds multiple components to the :class:`ActionRow`.

        Parameters
        ----------
        \*components: \*Union[:class:`Button`, :class:`SelectMenu`]
            The components to add to the ActionRow.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        self.components.extend(*components)
        return self

    def disable_all_components(self):
        """
        Disables all component's in this :class:`ActionRow` and returns the action row.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        [obj.__setattr__('disabled', True) for obj in self.components]
        return self

    def disable_all_components_if(self, check: Union[bool, Callable], *args: Any):
        """
        Disables all :attr:`components` in this :class:`ActionRow` if the passed :attr:`check` returns ``True``. It returns the action row.

        Parameters
        -----------
        check: Union[:class:`bool`, :class:`typing.Callable`]
            Could be a bool or usually any Callable that returns a bool.
        *args: Any
            Arguments that should be passed in to the check if it is a Callable.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        if not isinstance(check, (bool, Callable)):
            raise AttributeError(
                'The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check))
        try:
            check = check(*args)
        except TypeError:
            pass
        if check is True:
            [obj.__setattr__('disabled', True) for obj in self.components]
        return self

    def disable_all_buttons(self):
        """
        Disables all ::class:`~discord.Button`'s in this :class:`ActionRow` and returns the action row.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, Button)]
        return self

    def disable_all_buttons_if(self, check: Union[bool, Callable], *args: Any):
        """
        Disables all :class:`~discord.Button`'s in this :class:`ActionRow` if the passed :attr:`check` returns ``True``.
        It returns the action row.
    
        Parameters
        -----------
        check: Union[:class:`bool`, :class:`typing.Callable`]
            Could be a bool or usually any Callable that returns a bool.
        *args: Any
            Arguments that should be passed in to the check if it is a Callable.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        if not isinstance(check, (bool, Callable)):
            raise AttributeError('The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check))
        try:
            check = check(*args)
        except TypeError:
            pass
        if check is True:
            [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, Button)]
        return self

    def disable_all_select_menus(self):
        """
        Disables all :class:`discord.SelectMenu`'s in this :class:`ActionRow` and returns the action row.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, SelectMenu)]
        return self

    def disable_all_select_menus_if(self, check: Union[bool, Callable], *args: Any):
        """
        Disables all :class:`SelectMenu`'s in this :class:`ActionRow` if the passed :attr:`check` returns ``True``.
        It returns the action row.

        Parameters
        ----------
        check: Union[:class:`bool`, :class:`typing.Callable`]
            could be an :class:`bool` or usually any :class:`Callable` that returns a :class:`bool`
        *args: Any
            Arguments that should be passed in to the :attr:`check` if it is a :class:`Callable`.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        if not isinstance(check, (bool, Callable)):
            raise AttributeError('The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check))
        try:
            check = check(*args)
        except TypeError:
            pass
        if check is True:
            [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, SelectMenu)]
        return self

    @classmethod
    def from_dict(cls, data: dict):
        """
        Internal method to create a :class:`discord.ActionRow` from the data given by discord.

        Parameters
        ----------
        data: dict
            The raw data from the api.

        Returns
        -------
        :class:`~discord.ActionRow`
            The ActionRow created.
        """
        if data.get('type', None) != 1:
            return InvalidArgument("%s could not be interpreted as an ActionRow" % data)
        else:
            components = [_component_factory(component) for component in data.get('components', [])]
            return cls(*components)


def _component_factory(data):
    component_type = data.get('type', None)
    if component_type == ComponentType.ActionRow:
        return ActionRow.from_dict(data)
    elif component_type == ComponentType.Button:
        return Button.from_dict(data)
    elif component_type in {3, 5, 6, 7, 8}:
        return SelectMenu.from_dict(data)
    elif component_type == ComponentType.TextInput:
        return TextInput.from_dict(data)
    else:
        return None
