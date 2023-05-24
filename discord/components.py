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

from . import utils, abc
from .enums import try_enum, ComponentType, ButtonStyle, TextInputStyle, ChannelType
from .emoji import Emoji
from .partial_emoji import PartialEmoji
from .errors import InvalidArgument, URLAndCustomIDNotAlowed

from typing import (
    overload,
    Any,
    Iterator,
    Union,
    Type,
    Tuple,
    List,
    Dict,
    Optional,
    Callable,
    TypeVar,
    TYPE_CHECKING,
)

from typing_extensions import Literal, Self

if TYPE_CHECKING:
    from typing_extensions import ParamSpec
    from .types.message import (
        MessageComponent as Component,
        ActionRow as ActionRowPayload,
        Button as ButtonPayload,
        SelectMenu as SelectMenuPayload,
        SelectOption as SelectOptionPayload,
        TextInput as TextInputPayload,
        Modal as ModalPayload
    )
    from .role import Role
    from .user import User
    from .member import Member
    from .abc import GuildChannel, Messageable
    from .interactions import ComponentInteraction
    
    P = ParamSpec('P')


__all__ = (
    'ActionRow',
    'Button',
    'SelectMenu',
    'SelectOption',
    'TextInput',
    'UserSelect',
    'RoleSelect',
    'MentionableSelect',
    'ChannelSelect',
    'Modal'
)

T = TypeVar('T')

class BaseComponent:
    """
    The base class for all components.
    """
    _custom_id: Union[str, int]
    _disabled: bool

    def __init__(
            self,
            custom_id: Union[str, int] = None,
            disabled: bool = False
    ) -> None:
        self.custom_id = int(custom_id) if custom_id and custom_id.isdigit() else custom_id
        self.disabled = disabled

    @property
    def type(self) -> ComponentType:
        """:class:`~discord.ComponentType`: The type this component is of"""
        raise NotImplementedError()

    @property
    def custom_id(self) -> Union[str, int]:
        """
        Union[:class:`str`, :class:`int`] (depending on whether it is completely numeric or not):

        A developer defined ID for this component. **This must be unique per** :class:`~discord.Message`/:class:`~discord.Modal`
        Max. 100 characters long.

        .. note::
            The custom ID is a good place to store any additional data.
            For example if you want to make a check in the callback whether the author is a specific user just store the user-id in the custom_id like

            .. code-block:: python3

                # The custom_id
                custom_id=f'some-prefix:{ctx.author.id}'

                # Now you can extract this information again in the callback by splitting it at the separator.
                _, author_id = custom_id.split(':')  # Note that the author_id is still a string here, not an integer!

            Of course, you can store any and as much data in it as you want. (As long as it does not exceed the max. length)
        """
        return self._custom_id

    @custom_id.setter
    def custom_id(self, value: Union[str, int]):
        length = len(str(value))
        if 1 > length > 100:
            raise ValueError(
                f'The custom_id must be between 1 and 100 in length; got {length}'
            )
        self._custom_id = value

    @property
    def disabled(self) -> bool:
        """:class:`bool`: Whether this component can be used or not. If :obj:`True` it is greyed out in the client."""
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool):
        self._disabled = value

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BaseComponent:
        raise NotImplementedError()


class Button(BaseComponent):
    """Represents a `Discord-Button <https://discord.com/developers/docs/interactions/message-components#button-object>`_"""
    __slots__ = ('_label', '_custom_id', '_style', '_url', '_disabled')

    def __init__(
            self,
            label: Optional[str] = None,
            custom_id: Optional[Union[str, int]] = None,
            style: Union[ButtonStyle, int] = ButtonStyle.grey,
            emoji: Union[PartialEmoji, Emoji, str] = None,
            url: Optional[str] = None,
            disabled: bool = False
    ) -> None:
        """
        Represents a `Discord-Button <https://discord.com/developers/docs/interactions/message-components#button-object>`_

        Parameters
        ----------
        label: Optional[:class:`str`]:
            Text that appears on the button, max 80 characters
        custom_id: Optional[Union[:class:`str`, :class:`int`]
            See :attr:`BaseComponent.custom_id`
        style: Optional[Union[:class:`ButtonStyle`, :class:`int`]]
            The :class:`~discord.ButtonStyle` the button should have, defaults to :attr:`~discord.ButtonStyle.grey`
        emoji: Optional[Union[:class:`~discord.PartialEmoji`, :class:`~discord.Emoji`, :class:`str`]]:
            An emoji that will be displayed on the left side of the button.
        url: Optional[:class:`str`]
            An URL for the button if it is of type :attr:`ButtonStyle.url`
        """
        super().__init__(custom_id=custom_id, disabled=disabled)
        self.style: ButtonStyle = try_enum(ButtonStyle, style)
        if not emoji and not label:
            raise InvalidArgument('A button must have at least one of label or emoji set')
        elif self.style.url and not url:
            raise InvalidArgument('An url is required for url buttons')
        elif url and not self.style.url:
            self.style = ButtonStyle.url
        if url and custom_id:
            raise URLAndCustomIDNotAlowed(self.custom_id)
        elif not url and custom_id is None:
            raise InvalidArgument('A custom_id must be specified for non-url buttons')
        self.url: Optional[str] = url
        self.label: str = label
        self.emoji = emoji

    def __repr__(self) -> str:
        return f'<Button {", ".join([f"{k}={str(v)}" for k, v in self.__dict__.items()])}>'

    def __len__(self):
        return len(self.label) if self.label else len(self.emoji)

    @property
    def type(self) -> ComponentType:
        return ComponentType.Button

    @property
    def style(self) -> ButtonStyle:
        """Optional[Union[:class:`~discord.ButtonStyle`, :class:`int`]]: The :class:`~discord.ButtonStyle` the button should have, defaults to :attr:`~discord.ButtonStyle.grey`"""
        return self._style

    @style.setter
    def style(self, value: Union[int, ButtonStyle]):
        if isinstance(value, int):
            value = ButtonStyle(value)
        self._style = value

    @property
    def label(self) -> Optional[str]:
        """Optional[:class:`str`]: Text that appears on the button, max 80 characters"""
        return self._label

    @label.setter
    def label(self, value: Optional[str]):
        if value and len(value) > 80:
            raise InvalidArgument(f'The max. length of Button labels is 80, got {value}')
        self._label = value

    @property
    def emoji(self) -> Optional[PartialEmoji]:
        """
        Optional[Union[:class:`~discord.PartialEmoji`, :class:`~discord.Emoji`, :class:`str`]]: An emoji that will be displayed on the left side of the button.
        """
        return getattr(self, '_emoji', None)

    @emoji.setter
    def emoji(self, value: Optional[Union[PartialEmoji, Emoji, str]]):
        if isinstance(value, Emoji):
            self._emoji = PartialEmoji(name=value.name, animated=value.animated, id=value.id)
        elif isinstance(value, PartialEmoji):
            self._emoji = value
        elif isinstance(value, str):
            if value[0] == '<':
                self._emoji = PartialEmoji.from_string(value)
            else:
                self._emoji = PartialEmoji(name=value)

    @property
    def url(self) -> Optional[str]:
        """Optional[:class:`str`]: An URL for the button if it is of type :attr:`ButtonStyle.url`"""
        return getattr(self, '_url', None)

    @url.setter
    def url(self, value: Optional[str]):
        if value and not value.startswith(('http://', 'https://', 'discord://')):
            raise ValueError(f'"{value}" is not a valid protocol. Only http(s) or discord protocol is supported')
        self._url = value

    @utils.deprecated('label setter')
    def set_label(self, label: str):
        """
        Sets the Label of the :class:`Button`

        label: :class:`str`
            The label to replace th old one with.

        Returns
        -------
        :class:`~discord.Button`
            The updated instance
        """
        self.label = label
        return self

    @utils.deprecated('url setter')
    def set_url(self, url: Optional[str]) -> Button:
        """
        Sets the url of the :class:`Button`

        url: Optional[:class:`str`]
            The url to replace the old one with

        Returns
        -------
        :class:`~discord.Button`
            The updated instance
        """
        self.url = url
        return self

    def update(self, **kwargs):
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.__dict__.keys())
        return self

    @utils.deprecated('custom_id setter')
    def set_custom_id(self: Self, custom_id: Union[str, int]) -> Self:
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

    def disable_if(self: Self, check: Union[bool, Callable[[P, ...], bool]], *args: P.args, **kwargs: P.kwargs) -> Self:
        """
        Disables the :class:`~discord.Button` if the passed ``check`` returns :obj:`True` and return itself.

        Parameters
        ----------
        check: Union[:class:`bool`, Callable[[Any, ...], :class:`bool` ]]
            Could be an :class:`bool` or usually any :obj:`~typing.Callable` that returns a :class:`bool`
        *args: Any
            Positional arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`
        **kwargs: Any
            Keyword-only arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`

        Returns
        -------
        :class:`~discord.Button`
            The updated instance
         """
        if callable(check):
            check = check(*args, **kwargs)

        if not isinstance(check, bool):
            raise AttributeError(
                'The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check)
            )

        if check is True:
            self.disabled = True
        return self

    def set_style_if(self: Self, check: Union[bool, Callable[P, bool]], style: ButtonStyle, *args: P.args, **kwargs: P.kwargs) -> Self:
        """
        Sets the style of the :class:`~discord.Button` to the specified one if the specified ``check`` returns :obj:`True`.

        Parameters
        ----------
        check: Union[:class:`bool`, Callable[[Any, ...], :class:`bool`]]
            Could be an :class:`bool` or usually any :obj:`~typing.Callable` that returns a :class:`bool`
        style: discord.ButtonStyle
            The style the :class:`Button` should have when the ``check`` returns True
        *args: Any
            Positional arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`
        **kwargs: Any
            Keyword-only arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`

        Returns
        -------
        :class:`~discord.Button`
            The updated instance
        """
        if callable(check):
            check = check(*args, **kwargs)

        if not isinstance(check, bool):
            raise AttributeError(
                'The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check)
            )

        if check is True:
            self.style = style
        return self

    def to_dict(self) -> ButtonPayload:
        base = {
            'type': 2,
            'label': self.label,
            'style': int(self.style),
            'disabled': self.disabled
        }
        if self.custom_id is not None:
            base['custom_id'] = str(self.custom_id)
        elif self.url:
            base['url'] = self.url
        if self.emoji:
            base['emoji'] = self.emoji.to_dict()
        return base
    
    @classmethod
    def from_dict(cls, data: ButtonPayload) -> Button:
        emoji = data.pop('emoji', None)
        if emoji and isinstance(emoji, dict):
            emoji = PartialEmoji.from_dict(emoji)
        return cls(
            emoji=emoji,
            label=data.get('label'),
            custom_id=data.get('custom_id'),
            style=data['style'],
            url=data.get('url'),
            disabled=data.get('disabled', False)
        )


class SelectOption:
    """
    A class that represents an option for a :class:`SelectMenu`

    Attributes
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
    
    Raises
    ------
    :exc:`ValueError`
        One of ``label``, ``value`` or ``description`` is too long.
    """
    def __init__(
            self,
            label: str,
            value: str,
            description: Optional[str] = None,
            emoji: Union[PartialEmoji, Emoji, str] = None,
            default: bool = False
    ) -> None:
        if len(label) > 100:
            raise ValueError('The maximum length of the label is 100 characters.')
        self.label: str = label
        if len(value) > 100:
            raise ValueError('The maximum length of the value is 100 characters.')
        self.value: str = value
        if description and len(description) > 100:
            raise ValueError('The maximum length of the description is 100 characters.')
        self.description: Optional[str] = description
        if isinstance(emoji, PartialEmoji):
            self.emoji = emoji
        elif isinstance(emoji, Emoji):
            self.emoji: Optional[PartialEmoji] = PartialEmoji(name=emoji.name, animated=emoji.animated, id=emoji.id)
        elif isinstance(emoji, str):
            if emoji[0] == '<':
                self.emoji: Optional[PartialEmoji] = PartialEmoji.from_string(emoji)
            else:
                self.emoji: Optional[PartialEmoji] = PartialEmoji(name=emoji)
        else:
            self.emoji = None
        self.default: bool = default

    def __repr__(self):
        return f'<SelectOption {", ".join([f"{k}={v}" for k, v in self.__dict__.items()])}>'

    def set_default(self, value: bool):
        self.default = value
        return self

    def to_dict(self) -> SelectOptionPayload:
        base = {
            'label': str(self.label),
            'value': str(self.value),
            'default': bool(self.default)
        }
        if self.description:
            base['description'] = str(self.description)
        if self.emoji:
            base['emoji'] = self.emoji.to_dict()
        return base

    @classmethod
    def from_dict(cls, data: SelectOptionPayload) -> SelectOption:
        emoji = data.pop('emoji', None)
        if emoji:
            emoji = PartialEmoji.from_dict(emoji)
        return cls(
            label=data['label'],
            value=data['value'],
            description=data.get('description'),
            emoji=emoji,
            default=data.get('default', False)
        )


class BaseSelect(BaseComponent):
    __slots__ = ('_custom_id', '_placeholder', '_min_values', '_max_values', '_disabled', '_values', '_interaction')
    _interaction: Optional[ComponentInteraction]

    def __init__(
            self,
            custom_id: Union[str, int],
            placeholder: Optional[str] = None,
            min_values: int = 1,
            max_values: int = 1,
            disabled: bool = False,
    ) -> None:
        super().__init__(custom_id=custom_id, disabled=disabled)
        self.placeholder: Optional[str] = placeholder
        self.min_values: int = min_values
        self.max_values: int = max_values

    @property
    def placeholder(self) -> Optional[str]:
        """Optional[:class:`str`]: Custom placeholder text if nothing is selected, max. 100 characters."""
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: str):
        if value and len(value) > 150:
            raise AttributeError(
                'The maximum length of a the placeholder is 100 characters; your one is %d long (%d to long).' % (len(value), len(value) - 100)
            )
        self._placeholder = value

    @property
    def min_values(self) -> int:
        """:class:`int`: The minimum number of items that must be chosen; default 1, min. 0, max. 25."""
        return self._min_values

    @min_values.setter
    def min_values(self, value: int):
        if 25 < value < 0:
            raise ValueError('The minimum number of elements to be selected must be between 1 and 25.')
        self._min_values = value

    @property
    def max_values(self) -> int:
        """:class:`int`: The maximum number of items that can be chosen; default 1, max. 25."""
        return self._max_values

    @max_values.setter
    def max_values(self, value: int):
        if 25 < value <= 0:
            raise ValueError('The maximum number of elements to be selected must be between 0 and 25.')
        self._max_values = value

    @utils.cached_property
    def values(self) -> Optional[List[Any]]:
        if not hasattr(self, '_values'):
            return None
        values = []
        interaction = self._interaction
        resolved = interaction.data.resolved
        getter = None
        if self.type.UserSelect:
            if interaction.guild:
                def getter(v):
                    return interaction.guild.get_member(v) or resolved.members[v] or resolved.users[v]
            else:
                def getter(v):
                    return resolved.users[v]
        elif self.type.RoleSelect:
            def getter(v):
                return resolved.roles.get(v)
        elif self.type.MentionableSelect:
            def getter(v):
                try:
                    return resolved.roles[v]
                except KeyError:
                    return interaction.guild.get_member(v) or resolved.members[v] or resolved.users[v]
        elif self.type.ChannelSelect:
            def getter(v):
                return interaction.guild.get_channel(v) or resolved.channels[v] or interaction._state.get_channel(v)

        for _id in self._values:
            values.append(getter(int(_id)))
        return values

    def update(self: Self, **kwargs) -> Self:
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.__dict__.keys())
        return self

    @utils.deprecated('custom_id setter')
    def set_custom_id(self: Self, custom_id: Union[str, int]) -> Self:
        """
        Set the custom_id of the Select

        Parameters
        ----------
        custom_id: Union[:class:`str`, :class:`int`]
            The custom_id to replace the old one with

        Returns
        -------
        Union[:class:`.SelectMenu`, :class:`.UserSelect`, :class:`.RoleSelect`, :class:`.MentionableSelect`, :class:`.ChannelSelect`]
            The instance with the updated custom_id
        """
        self.custom_id = custom_id
        return self

    def disable_if(self: Self, check: Union[bool, Callable[[P, ...], bool]], *args: P.args, **kwargs: P.kwargs) -> Self:
        """
        Disables the Select if the passed ``check`` returns :obj:`True` and returns itself.


        Parameters
        ----------
        check: Union[:class:`bool`, Callable[[Any, ...], :class:`bool` ]]
            Could be an :class:`bool` or usually any :obj:`~typing.Callable` that returns a :class:`bool`
        *args: Any
            Positional arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`
        **kwargs: Any
            Keyword-only arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`

        Returns
        -------
        Union[:class:`SelectMenu`, :class:`UserSelect`, :class:`RoleSelect`, :class:`MentionableSelect`, :class:`ChannelSelect`]
            The updated instance
        """
        if callable(check):
            check = check(*args, **kwargs)

        if not isinstance(check, bool):
            raise AttributeError(
                'The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check)
            )

        if check is True:
            self.disabled = True
        return self

    def to_dict(self) -> SelectMenuPayload:
        return {
            'type': self.type.value,
            'custom_id': str(self.custom_id),
            'min_values': self.min_values,
            'max_values': self.max_values,
            'placeholder': self.placeholder,
            'disabled': self.disabled
        }

    @classmethod
    def from_dict(cls: Type[T], data: SelectMenuPayload) -> T:
        return cls(
            custom_id=data['custom_id'],
            placeholder=data.get('placeholder'),
            min_values=data.get('min_values', 1),
            max_values=data.get('max_values', 1),
            disabled=data.get('disabled', False)
        )


class SelectMenu(BaseSelect):
    __slots__ = ('_custom_id', '_options', '_placeholder', '_min_values', '_max_values', '_disabled', '_values', '_interaction')

    def __init__(
            self,
            custom_id: Union[str, int],
            options: List[SelectOption],
            placeholder: Optional[str] = None,
            min_values: int = 1,
            max_values: int = 1,
            disabled: bool = False
    ) -> None:
        """
        Represents a `Select-Menu <https://discord.com/developers/docs/interactions/message-components#select-menus>`_

        Parameters
        ----------
        custom_id: Union[:class:`str`, :class:`int`]
            A developer-defined identifier for the :class:`SelectMenu`, max. 100 characters
        options: List[:class:`SelectOption`]
            A :class:`list` of options to choose from, max. 25
        placeholder: Optional[:class:`str`]
            Custom placeholder text if nothing is selected, max. 100 characters
        min_values: Optional[:class:`int`]
            The minimum number of items that must be chosen; default 1, min. 0, max. 25
        max_values: Optional[:class:`int`]
            The maximum number of items that can be chosen; default 1, max. 25
        disabled: Optional[:class:`bool`]
            Disables the SelectMenu, default :obj:`False`
        """
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled
        )
        self.options = options

    def __repr__(self):
        return f'<SelectMenu {", ".join([f"{k}={v}" for k, v in self.__dict__.items()])}>'

    @property
    def type(self) -> ComponentType:
        return ComponentType.StringSelect

    @property
    def options(self) -> List[SelectOption]:
        """
        List[:class:`.SelectOption`]: A :class:`list` of options to choose from, max. 25.

        .. note::
            This must include at least the amount of :attr:`~SelectMenu.min_values`/:attr:`~SelectMenu.max_values`
        """
        return getattr(self, '_options', [])

    @options.setter
    def options(self, options: List[SelectOption]):
        if self.min_values > len(options) > min(self.max_values, 25):
            raise InvalidArgument('At least %d options must be provided and max. amount of options is 25', self.min_values)
        for index, o in enumerate(options):
            if not isinstance(o, SelectOption):
                raise InvalidArgument("At SelectMenu.options[%d]: options must be a list of discord.SelectOption, got %s" % (index, o.__class__.__name__))
        self._options = list(options)

    @utils.cached_property
    def all_option_values(self) -> Iterator[Union[int, str]]:
        """
        All values of the :attr:`options` of the SelectMenu.

        .. warning::
            If the :attr:`~discord.SelectOption.value` is a number it is returned as an :class:`int`, otherwise as :class:`str`!

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

    @utils.cached_property
    def values(self) -> List[Union[int, str]]:
        """
        The values of the :attr:`options` that were selected

        .. note::
            This only exists if the :class:`SelectMenu` is passed as an argument in an interaction.

        .. warning::
            If the :attr:`~discord.SelectOption.value` is a number it is returned as an :class:`int`, otherwise as :class:`str`!

        Raises
        ------
        TypeError
            The SelectMenu was not passed as an argument for an interaction-callback

        Returns
        --------
        List[Union[:class:`int`, :class:`str`]]
            A list containing the values of the selected options
        """
        values = []
        try:
            _values = self._values
        except AttributeError:
            raise TypeError('You only can use this when the SelectMenu was passed as an argument in an interaction-callback')
        for value in _values:
            if value.isdigit():
                values.append(int(value))
            else:
                values.append(value)
        return values

    @utils.cached_property
    def not_selected(self) -> List[Union[int, str]]:
        """
        The options that were **not** selected

        .. note::
            This only exists if the :class:`SelectMenu` is passed as a parameter in an interaction.

        .. warning::
            If the :attr:`~discord.SelectOption.value` is a number it is returned as an :class:`int`, otherwise as :class:`str`!

        Raises
        ------
        TypeError
            The SelectMenu was not passed as an argument for an interaction-callback

        Returns
        --------
        List[Union[:class:`int`, :class:`str`]]
            A list containing the values of all **not** selected options
        """
        values = self.values
        return [value for value in self.all_option_values if value not in values]

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base['options'] = [o.to_dict() for o in self.options]
        return base

    @classmethod
    def from_dict(cls, data:SelectMenuPayload) -> SelectMenu:
        return cls(
            custom_id=data['custom_id'],
            options=[SelectOption.from_dict(o) for o in data.pop('options')],
            min_values=data.pop('min_values', 1),
            max_values=data.pop('max_values', 1),
            disabled=data.pop('disabled', False),
            placeholder=data.get('placeholder'),
        )


class Modal:
    """
    Represents a `Modal <https://discord.com/developers/docs/interactions/receiving-and-responding#interaction-response-object-modal>`_

    Parameters
    ----------
    custom_id: :class:`str`
        A developer-defined identifier for the component, max 100 characters
    title: :class:`str`
        The title of the popup modal, max 45 characters
    components: List[Union[:class:`ActionRow`, List[:class:`TextInput`],:class:` TextInput`]]
        Between 1 and 5 (inclusive) components that make up the modal.
    """
    def __init__(
            self,
            title: str,
            custom_id: str,
            components: List[Union[ActionRow, List[TextInput]]]
    ) -> None:
        # TODO: Add Error handling
        self.title: str = title
        self.custom_id: str = custom_id
        _components = []
        for c in components:
            if isinstance(c, list):
                c = ActionRow(*c)
            elif isinstance(c, TextInput):
                c = ActionRow(c)
            _components.append(c)
        self.components: List[ActionRow] = _components

    def to_dict(self) -> ModalPayload:
        components = []
        for a in self.components:
            components.extend(a.to_dict())
        return {
            'custom_id': self.custom_id,
            'title': self.title,
            'components': components
        }

    @classmethod
    def from_dict(cls, data: ModalPayload) -> Modal:
        return cls(
            custom_id=data['custom_id'],
            title=data['title'],
            components=[
                _component_factory(a) for a in data['components']
            ]
        )


class TextInput(BaseComponent):
    def __init__(
            self,
            label: str,
            custom_id: str,
            style: Union[TextInputStyle, Literal[1, 2]] = 1,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            required: Optional[bool] = True,
            value: Optional[str] = None,
            placeholder: Optional[str] = None
    ) -> None:
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
        super().__init__(custom_id=custom_id)
        self.label: Optional[str] = label
        self.style: Union[TextInputStyle, Literal[1, 2]] = try_enum(TextInputStyle, style)
        self.min_length: Optional[int] = min_length
        self.max_length: Optional[int] = max_length
        self.required: bool = required
        self.value: Optional[str] = value
        self.placeholder: Optional[str] = placeholder
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f'<TextInput {", ".join([f"{k}={str(v)}" for k, v in self.__dict__.items()])}>'
    
    @property
    def type(self) -> ComponentType:
        return ComponentType.TextInput

    def to_dict(self) -> TextInputPayload:
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
    def from_dict(cls, data: TextInputPayload) -> TextInput:
        new = cls.__new__(cls)
        for attr in ('label', 'custom_id', 'style', 'min_length', 'max_length', 'required', 'value', 'placeholder'):
            try:
                setattr(new, attr, data[attr])
            except KeyError:
                continue
        return new


class UserSelect(BaseSelect):
    """
    Very similar to :class:`SelectMenu` but you can select from a list of :class:`~discord.Member`/:class:`~discord.User`

    .. note::
        :attr:`~SelectMenu.options` can't be set for this type
    """
    @property
    def type(self) -> ComponentType:
        return ComponentType.UserSelect

    @utils.cached_property
    def values(self) -> Optional[List[Union[Member, User]]]:
        """
        The members/users that were selected

        .. note::
            This only exists if the :class:`UserSelect` is passed as a parameter in an interaction.

        Returns
        --------
        List[Union[:class:`Member`, :class:`User`]]
            A list of selected members or user if the member is not found
        """
        return super().values


class RoleSelect(BaseSelect):
    """
    Very similar to :class:`SelectMenu` but you can select from a list of :class:`~discord.Role`

    .. note::
        :attr:`~discord.SelectMenu.options` can't be set for this type
    """

    @property
    def type(self) -> ComponentType:
        return ComponentType.RoleSelect

    @utils.cached_property
    def values(self) -> Optional[List[Role]]:
        """
        The roles that were selected

        .. note::
            This only exists if the :class:`RoleSelect` is passed as a parameter in an interaction.

        Returns
        --------
        List[:class:`Role`]
            A list of selected roles
        """
        return super().values


class MentionableSelect(BaseSelect):
    """
    Very similar to :class:`SelectMenu` but you can select from a list of both :class:`~discord.Member`/:class:`~discord.User` and :class:`~discord.Role`

    .. note::
        :attr:`~SelectMenu.options` can't be set for this type
    """
    @property
    def type(self) -> ComponentType:
        return ComponentType.MentionableSelect

    @utils.cached_property
    def values(self) -> Optional[List[Union[Member, User, Role]]]:
        """
        The members/users and roles that were selected

        .. note::
            This only exists if the :class:`MentionableSelect` is passed as a parameter in an interaction.

        Returns
        --------
        List[Union[:class:`Member`, :class:`User`, :class:`Role`]]
            A list of selected members/users and roles
        """
        return super().values


class ChannelSelect(BaseSelect):
    """
    Very similar to :class:`SelectMenu` but you can select from a list of channels.

    For this type there is an additional parameter ``channel_types``
    wich can be a list of :class:`ChannelType` (or the type itself like :class:`TextChannel` or :class:`StageChannel`) that specify
    from what channel types the user could choose.

    .. note::
        :attr:`~SelectMenu.options` can't be set for this type
    """
    __slots__ = ('_custom_id', '_placeholder', '_min_values', '_max_values', '_disabled', '_channel_types', '_values', '_interaction')

    def __init__(
            self,
            custom_id: Union[str, int],
            channel_types: Optional[List[Union[ChannelType, abc.GuildChannel]]] = None,
            placeholder: Optional[str] = None,
            min_values: int = 1,
            max_values: int = 1,
            disabled: bool = False
    ) -> None:
        self.channel_types = channel_types
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled
        )

    @property
    def type(self) -> ComponentType:
        return ComponentType.ChannelSelect

    @property
    def channel_types(self) -> Optional[List[ChannelType]]:
        return getattr(self, '_channel_types', None)

    @channel_types.setter
    def channel_types(self, value: Optional[List[Union[ChannelType, abc.GuildChannel]]]):
        types = None
        if value is not None:
            types = []
            for c in value:
                if not isinstance(c, ChannelType):
                    types.append(ChannelType.from_type(c)[-1])
                else:
                    types.append(c)
        self._channel_types = types

    @utils.cached_property
    def values(self) -> Optional[List[Union[GuildChannel, Messageable]]]:
        """
        The channels that were selected

        .. note::
            This only exists if the :class:`ChannelSelect` is passed as a parameter in an interaction.

        Returns
        --------
        List[Union[:class:`GuildChannel`, :class:`Messageable`]]
            A list of selected channels
        """
        return super().values

    def to_dict(self) -> SelectMenuPayload:
        base = super().to_dict()
        if self.channel_types:
            base['channel_types'] = [int(t) for t in self.channel_types]
        return base


class ActionRow:
    """
    Represents an ActionRow-Part for the components of a :class:`~discord.Message`.

    Attributes
    ----------
    components: List[Union[:class:`Button`, :ref:`Select <select-like-objects>`, :class:`TextInput`]]
        The components the :class:`~discord.ActionRow` holds.
        This could be up to 5 :class:`Button` or one :ref:`Select <select-like-objects>` like object/:class:`TextInput`.
    """

    @overload
    def __init__(self, *components: Button) -> None: ...

    @overload
    def __init__(self, components: BaseSelect) -> None: ...

    @overload
    def __init__(self, components: TextInput) -> None: ...

    def __init__(self, *components: T[Union[Button, BaseSelect, TextInput]]) -> None:
        """
        Represents an ActionRow-Part for the components of a :class:`~discord.Message`.

        .. note ::

            For more information about ActionRows visit the
            `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#actionrow>`_.

        Parameters
        ----------
        *components: Union[:class:`Button`, :class:`SelectMenu`, :class:`UserSelect`, :class:`RoleSelect`, :class:`MentionableSelect`, :class:`ChannelSelect`, :class:`TextInput`]
            The components the :class:`~discord.ActionRow` should hold.
            This could be up to 5 :class:`Button` or one :ref:`Select <select-like-objects>` like object/:class:`TextInput`.
        """
        self.components: List[T] = list(components)

    @overload
    def __class_getitem__(cls, item: Button) -> ActionRow: ...

    @overload
    def __class_getitem__(cls, item: Tuple[Button, ...]) -> ActionRow: ...

    @overload
    def __class_getitem__(cls, item: BaseSelect) -> ActionRow: ...

    @overload
    def __class_getitem__(cls, item: TextInput) -> ActionRow:
        ...

    def __class_getitem__(cls, item: T) -> ActionRow(T):
        return ActionRow(*item) if isinstance(item, tuple) else ActionRow(item)

    def __repr__(self) -> str:
        return f'<ActionRow components={self.components}>'

    def __iter__(self) -> Iterator[Union[Button, BaseSelect, TextInput]]:
        yield from self.components

    @property
    def type(self) -> ComponentType:
        return ComponentType.ActionRow

    def to_dict(self) -> ActionRowPayload:
        actual_row = []
        rows = [actual_row]
        for c in self.components:
            max_rows_reached = len(rows) == 5
            if len(actual_row) >= 5:
                if max_rows_reached:
                    raise InvalidArgument('A message could only contain up to 5 ActionRows')

                if actual_row in rows:
                    rows[rows.index(actual_row)] = actual_row.copy()
                else:
                    rows.append(
                        actual_row.copy()
                    )
                actual_row.clear()
                rows.append(actual_row)
            t = c.type
            if t.ActionRow:
                raise ValueError('An ActionRow can not contain another ActionRow')
            elif t.Button:
                actual_row.append(c.to_dict())
            elif t.value > 2:
                if len(rows) >= 5:
                    raise ValueError(
                        'An ActionRow containing a %s cannot contain other components',
                        t.name
                    )
                if not actual_row:
                    rows[rows.index(actual_row)] = [c.to_dict()]
                    actual_row.clear()
                    rows.append(actual_row)
                else:
                    rows.append([c.to_dict()])

        max_rows_reached = len(rows) == 5
        if actual_row:
            if max_rows_reached:
                raise InvalidArgument('A message could only contain up to 5 ActionRows')
            if actual_row not in rows:
                rows.append(
                    actual_row.copy()
                )
            rows[rows.index(actual_row)] = actual_row.copy()
        return [{'type': 1, 'components': components} for components in rows if len(components)]

    def __len__(self) -> int:
        return len(self.components)

    def __invert__(self) -> List[Union[Button, BaseSelect, TextInput]]:
        return self.components

    def __getitem__(self, item: int) -> Union[Button, BaseSelect, TextInput]:
        return self.components[item]

    def __setitem__(self, index: int, component: Union[Button, BaseSelect, TextInput]) -> None:
        self.set_component_at(index, component)

    def add_component(self: Self, component: Union[Button, BaseSelect, TextInput]) -> Self:
        """
        Adds a component to the :class:`~discord.ActionRow` and returns itself.

        Parameters
        ----------
        component: Union[:class:`Button`, :class:`SelectMenu`, :class:`UserSelect`, :class:`RoleSelect`, :class:`MentionableSelect`, :class:`ChannelSelect`, :class:`TextInput`]
            The component to add to the ActionRow.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        self.components.append(component)
        return self

    def insert_component_at(self: Self, index, component: Union[Button, BaseSelect, TextInput]) -> Self:
        """
        Inserts a component before a specified index to the :class:`~discord.ActionRow` and returns itself.

        Parameters
        -----------
        index: :class:`int`
            The index of where to insert the component.
        component: Union[:class:`Button`, :class:`SelectMenu`, :class:`UserSelect`, :class:`RoleSelect`, :class:`MentionableSelect`, :class:`ChannelSelect`, :class:`TextInput`]
            The component to insert.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        self.components.insert(index, component)
        return self

    def set_component_at(self: Self, index: int, component: Union[Button, SelectMenu]) -> Self:
        """
        Modifies a component to the :class:`~discord.ActionRow` and returns itself.

        .. note::
            The index must point to a valid pre-existing component.

        Parameters
        ----------
        index: :class:`int`
            The index of the component to modify.
        component: Union[:class:`Button`, :class:`SelectMenu`, :class:`UserSelect`, :class:`RoleSelect`, :class:`MentionableSelect`, :class:`ChannelSelect`, :class:`TextInput`]
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
            raise IndexError('component index %d out of range' % index)
        self.components[index] = component
        return self

    def disable_component_at(self: Self, index: int) -> Self:
        """
        Disables the component at the specified position of the :class:`~discord.ActionRow` and returns itself.

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
            raise IndexError(f'component index {index} out of range')
        component.disabled = True
        return self

    @overload
    def add_components(self: Self, *components: Button) -> Self: ...

    @overload
    def add_components(self: Self, components: BaseSelect) -> Self: ...

    @overload
    def add_components(self: Self, components: TextInput) -> Self: ...

    def add_components(self: Self, *components: Union[Button, BaseSelect, TextInput]) -> Self:
        """
        Adds multiple components to the :class:`~discord.ActionRow` and returns itself.

        Parameters
        ----------
        *components: Union[:class:`Button`, :class:`SelectMenu`, :class:`UserSelect`, :class:`RoleSelect`, :class:`MentionableSelect`, :class:`ChannelSelect`, :class:`TextInput`]
            The components to add to the ActionRow.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        self.components.extend(*components)
        return self

    def disable_all_components(self: Self) -> Self:
        """
        Disables all components in this :class:`~discord.ActionRow` and returns itself.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        [obj.__setattr__('disabled', True) for obj in self.components]
        return self

    def disable_all_components_if(self: Self, check: Union[bool, Callable[P, bool]], *args: P.args, **kwargs: P.kwargs) -> Self:
        """
        Disables all :attr:`components` in this :class:`~discord.ActionRow` if the passed ``check`` returns :obj:`True` and returns itself.

        Parameters
        ----------
        check: Union[:class:`bool`, Callable[[Any, ...], :class:`bool` ]]
            Could be an :class:`bool` or usually any :obj:`~typing.Callable` that returns a :class:`bool`
        *args: Any
            Positional arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`
        **kwargs: Any
            Keyword-only arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        if callable(check):
            check = check(*args, **kwargs)

        if not isinstance(check, bool):
            raise AttributeError(
                'The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check)
            )

        if check is True:
            [obj.__setattr__('disabled', True) for obj in self.components]
        return self

    def disable_all_buttons(self: Self) -> Self:
        """
        Disables any :class:`~discord.Button` in this :class:`~discord.ActionRow` and returns itself.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, Button)]
        return self

    def disable_all_buttons_if(self: Self, check: Union[bool, Callable[P, bool]], *args: P.args, **kwargs: P.kwargs) -> Self:
        """
        Disables any :class:`~discord.Button` in this :class:`~discord.ActionRow` if the passed ``check`` returns :obj:`True` and returns itself.

        Parameters
        ----------
        check: Union[:class:`bool`, Callable[[Any, ...], :class:`bool` ]]
            Could be an :class:`bool` or usually any :obj:`~typing.Callable` that returns a :class:`bool`
        *args: Any
            Positional arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`
        **kwargs: Any
            Keyword-only arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        if callable(check):
            check = check(*args, **kwargs)

        if not isinstance(check, bool):
            raise AttributeError(
                'The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check)
            )

        if check is True:
            [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, Button)]
        return self

    def disable_all_select_menus(self: Self) -> Self:
        """
        Disables all :ref:`Select <select-like-objects>` like objects in this :class:`~discord.ActionRow` and returns itself.

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, BaseSelect)]
        return self

    def disable_all_select_menus_if(self: Self, check: Union[bool, Callable[P, bool]], *args: P.args, **kwargs: P.kwargs) -> Self:
        """
        Disables all :ref:`Select <select-like-objects>` like objects in this :class:`~discord.ActionRow`
        if the passed ``check`` returns :obj:`True` and returns itself.

        Parameters
        ----------
        check: Union[:class:`bool`, Callable[[Any, ...], :class:`bool` ]]
            Could be an :class:`bool` or usually any :obj:`~typing.Callable` that returns a :class:`bool`
        *args: Any
            Positional arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`
        **kwargs: Any
            Keyword-only arguments that should be passed in to the ``check`` if it is a :obj:`~typing.Callable`

        Returns
        -------
        :class:`~discord.ActionRow`
            The updated instance
        """
        if callable(check):
            check = check(*args, **kwargs)

        if not isinstance(check, bool):
            raise AttributeError(
                'The check must bee a bool or any callable that returns one. Not {0.__class__.__name__}'.format(check)
            )

        if check is True:
            [obj.__setattr__('disabled', True) for obj in self.components if isinstance(obj, SelectMenu)]
        return self

    @classmethod
    def from_dict(cls, data: ActionRowPayload) -> ActionRow:
        """
        Internal method to create a :class:`~discord.ActionRow` from the data given by discord.

        Parameters
        ----------
        data: :class:`dict`
            The raw data from the api.

        Returns
        -------
        :class:`~discord.ActionRow`
            The ActionRow created.
        """
        components = [_component_factory(component) for component in data.get('components', [])]
        return cls(*components)


def _component_factory(data: Union[ActionRowPayload, Component]) -> Union[ActionRow, BaseComponent]:
    component_type = data.get('type')
    if component_type == 1:
        return ActionRow.from_dict(data)
    elif component_type == 2:
        return Button.from_dict(data)
    elif component_type == 3:
        return SelectMenu.from_dict(data)
    elif component_type == 4:
        return TextInput.from_dict(data)
    elif component_type == 5:
        return UserSelect.from_dict(data)
    elif component_type == 6:
        return RoleSelect.from_dict(data)
    elif component_type == 7:
        return MentionableSelect.from_dict(data)
    elif component_type == 8:
        return ChannelSelect.from_dict(data)
