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

import re
import typing
from .emoji import Emoji
from typing import Union, Tuple, Optional, Callable
from .partial_emoji import PartialEmoji
from .errors import InvalidArgument, InvalidButtonUrl, URLAndCustomIDNotAlowed, InvalidData, EmptyActionRow
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"


class ButtonStyle:
    """
    :class:`ButtonS
    Represents the Style for an :class:`discord.Button`

    .. note ::
        For more information about the Button-Styles visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#buttons-button-styles>`_.
    """
    Primary = 1
    Secondary = 2
    Success = 3
    Danger = 4
    Link_Button = 5

    __repr__ = [Primary, Secondary, Success, Danger, Link_Button]


class ButtonColor:
    """
    :class:`ButtonColor`

    .. note ::
        This is just an Aliase to :class:`ButtonStyle`
    """
    blurple = ButtonStyle.Primary
    grey = ButtonStyle.Secondary
    green = ButtonStyle.Success
    red = ButtonStyle.Danger
    grey_url = ButtonStyle.Link_Button


class Button(object):
    """
    :class:`Button`

    Represents an ``Discord-Button``

    .. note ::
        For more information Discord-Button's visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#buttons>`_.
    """

    def __init__(self, **kwargs):
        self._style = kwargs.get('style', kwargs.get('color', ButtonStyle.Secondary))
        self._url: str = kwargs.get('url', None)
        if self._url and not re.match(URL_REGEX, self.url):
            raise InvalidButtonUrl(self.url)
        if self._style not in [1, 2, 3, 4, 5]:
            raise InvalidArgument(
                "The Style of an discord.Button have to be an Object of discord.ButtonStyle, discord.ButtonColor or usually an Integer between 1 and 5")
        if self._style == ButtonStyle.Link_Button and not self.url:
            raise MissingRequiredArgument(
                'You must also pass a URL if the ButtonStyle is a link.')
        if self._url and self._style != ButtonStyle.Link_Button:
            self._style = ButtonStyle.Link_Button
        self._custom_id: str = kwargs.get('custom_id', None)
        if self._custom_id and len(self.custom_id) > 100:
            raise InvalidArgument(
                'The maximum length of Button-custom_id\'s are 100; your one is %s long. (%s Characters to long)' % (len(self.custom_id), len(self.custom_id) - 100))
        if self._custom_id and self.url:
            raise URLAndCustomIDNotAlowed(self.custom_id)
        self._label: str = kwargs.get('label', kwargs.get('name', ''))
        if self._label and len(self._label) > 80:
            raise InvalidArgument(f'The maximum length of Button-Labels\'s are 80; your one is {len(self.label)} long. ({len(self.label) - 100} Characters to long)')
        self._emoji = kwargs.get('emoji', None)
        if isinstance(self._emoji, Emoji):
            self._emoji = PartialEmoji(name=self._emoji.name, animated=self._emoji.animated, id=self._emoji.id)
        elif isinstance(self._emoji, str):
            self._emoji = PartialEmoji(name=self._emoji)
        else:
            self._emoji = None
        self._disabled: bool = kwargs.get('disabled', False)

    def __repr__(self):
        return f'<discord.Button {" ".join([k+"="+v for k, v in self.__dict__.items()])}'

    @property
    def style(self) -> int:
        return self._style

    @property
    def label(self) -> Union[str, None]:
        return self._label

    def set_label(self, label: str):
        if len(label) > 80:
            raise InvalidArgument(f'The maximum length of Button-Labels\'s are 80; your one is {len(label)} long. ({len(label) - 100} Characters to long)')
        self._label = label
        return self

    @property
    def url(self) -> Union[str, None]:
        return self._url

    def set_url(self, url: str):
        if not url.startswith('http'):
            raise InvalidButtonUrl(url)
        self._url = url
        return self

    @property
    def custom_id(self) -> str:
        return self._custom_id

    def update(self, **kwargs):
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.__dict__.keys())
        return self

    def set_custom_id(self, custom_id: str):
        if len(custom_id) > 100:
            raise InvalidArgument(
                'The maximum length of Button-custom_id\'s are 100; your one is %s long. (%s Characters to long)' % (len(custom_id), len(custom_id) - 100))
        if self._custom_id and self.url:
            raise URLAndCustomIDNotAlowed(self.custom_id)
        self._custom_id = custom_id
        return self

    @property
    def emoji(self) -> Union[PartialEmoji, None]:
        return self._emoji

    @property
    def disabled(self) -> bool:
        return self._disabled

    def disable_if(self, check: typing.Union[bool, typing.Callable], **kwargs):
        """
        Disable the :class:`discord.Button` if the passed ``check`` returns :bool:`True`.

        ______________

        ``Parameters:``
            - ``check:`` could be an :class:`bool` or usually any :obj:`Callable` that returns an :class:`bool`
            - ``**kwargs:`` :obj:`kwargs` that should passed in to the :pram:`check` if it is an :obj:`Callable`

        :return: :class:`discord.Button`
         """
        if isinstance(check, typing.Callable):
            if check(**kwargs) is True:
                self._disabled = True
        else:
            if check is True:
                self._disabled = True
        return self

    def set_color_if(self, check: Union[bool, typing.Callable], color: any(ButtonStyle.__repr__), **kwargs):
        """
        Sets the Color(Style) of an :class:`discord.Button` to the provided ``color`` if the passed ``check`` returns :bool:`True`.

        ______________

        ``Parameters:``
            - ``check:`` could be an :class:`bool` or usaly any :obj:`Callable` that returns an :class:`bool`
            - ``color:`` the Color(Style) that should set if the :param:`check` returns :bool:`True`
            - ``**kwargs:`` :obj:`kwargs` that should passed in to the :pram:`check` if it is an :obj:`Callable`

        :return: :class:`discord.Button`
        """
        if isinstance(check, typing.Callable):
            if check(**kwargs) is True:
                self._style = color
        else:
            if check is True:
                self._style = color
        return self

    def to_dict(self):
        base = {'type': 2, 'label': self._label, 'style': self._style, 'disabled': self._disabled}
        if self._url:
            base.__setitem__('url', self._url)
        if self._custom_id:
            base.__setitem__('custom_id', self._custom_id)
        if self._emoji:
            base.__setitem__('emoji', self._emoji.to_dict())
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


def create_option(label: str, value: str):
    return {'label': label, 'value': value}


class DropdownMenue:
    """
    Represents an Discord-dropdown-Menue
     .. note ::
        This Feature is ``not`` released jet!
    """
    __slots__ = ['__custom_id', '__options']

    def __init__(self, **kwargs):
        self.__options: list = kwargs.get('options', [])
        if not [type(obj) == dict for obj in self._options]:
            raise InvalidData("DropdownMenue-Options have to bee an Dict like `{'label': 'that what should show up in Discord', 'value': 'that what the Discord-API sends to your Application if the option is chosen'}`, or usually an :function:`discord.components.create_option`.")
        self.__custom_id: str = kwargs.get('custom_id', 'no_custom_id_set')

    def to_dict(self) -> dict:
        return {'type': 3, 'custom_id': self.__custom_id, 'options': self.__options}

    def update(self, **kwargs):
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.__dict__.keys())
        return self

    @classmethod
    def from_dict(cls, data: dict):
        _custom_id = data.get('custom_id', None)
        _options = data.get('options', None)
        return cls(custom_id=__custom_id, options=_options)

    @property
    def options(self):
        return self.__options

    @property
    def custom_id(self):
        return self.__custom_id


class ActionRow:
    def __init__(self, *args, **kwargs):
        """Represents an ActionRow-Part for the components of an :class:`discord.Message`

        .. note ::
            For more information about ActionRow's visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#actionrow>`_.
        """
        self.components = []
        self.force = kwargs.get('force', False)
        for obj in args:
            if isinstance(obj, Button):
                self.components.append(obj)
            elif isinstance(obj, DropdownMenue):
                self.components.append(obj)
            elif isinstance(obj, dict):
                if not obj.get('type', None) in [2, 3]:
                    raise InvalidData('if you use an Dict instead of Button, DropdownMenue you have to pass an type betwean 2 or 3')
                self.components.append({1: Button.from_dict(obj), 2: DropdownMenue.from_dict(obj)}.get(obj.get('type')))

    def sendable(self) -> Union[dict, EmptyActionRow]:
        base = []
        base.extend([{'type': 1, 'components': [obj.to_dict() for obj in self.components[five:5:]]} for five in range(0, len(self.components), 5)])
        objects = len([i['components'] for i in base])
        if any(len(ar['components']) < 1 for ar in base) and self.force is False:
            raise EmptyActionRow()
        elif len(base) > 5 or objects > 5*5 :
            raise InvalidArgument(f"The maximum number of ActionRow's per message is 5 and they can only contain 5 buttons each; you have {len(base)} ActionRow's passed with {objects} objects")
        return base

    def edit_obj(self, index: int, **kwargs):
        obj: Union[Button, DropdownMenue] = self.components.pop(index)
        self.components.pop(index)
        self.components.insert(index, obj.update(**kwargs))
        return self

    def disable_all_buttons(self):
        [obj.__setattr__('_disabled', True) for obj in self.components if isinstance(obj, Button)]
        return self

    @property
    def raw(self) -> dict:
        yield (o for o in self.components)

    @classmethod
    def from_dict(cls, data):
        if data.get('type') != 1:
            return InvalidData("%s could not be implemented as an ActionRow" % data)
        else:
            return cls(data.get('components'), force=True)


class DecodeInteractionCreateResponse:
    def __init__(self, data: dict):
        self._type = data['t']
        if self._type != 'INTERACTION_CREATE':
            return
        self._version = data['d'].get('version', None)
        self._type = data['d'].get('type', None)
        self._token = data['d'].get('token')
        self._message = data.get('message')
        self._data = data.get('data', None)
        self._member = Member(data.get('member'))
        self._id = data.get('id', 0)
        self._guild_id = data.get('guild_id', 0)
        self._channel_id = data.get('channel_id', 0)
        self.application_id = data.get('application_id', 0)

    @property
    def button(self):
        return ClickEvent(self._data)

    @property
    def token(self):
        return self._token

    @property
    def message(self):
        return self._message


class ClickEvent:
    def __init__(self, data: dict):
        self._custom_id = data.get('custom_id', None)
        self._component_type = data.get('component_type')

    @property
    def custom_id(self):
        return self._custom_id

    @property
    def component_type(self):
        return self._component_type


class DecodeMessageComponents:
    def __init__(self, value):
        self._action_rows = []
        self._other_elements = []
        for obj in value:
            try:
                self._other_elements.append(ActionRow.from_dict(obj))
            except InvalidData:
                self._other_elements.append(obj)
        if self._other_elements:
            raise InvalidArgument(f"Invalid Type(s): {[o for o in self._other_elements]} are/is of type(s) {[type(o) for o in self._other_elements]} but has to bee an discord.ActionRow.")

    @property
    def action_rows(self):
        return self._action_rows

    @property
    def other_elements(self):
        return self._other_elements
