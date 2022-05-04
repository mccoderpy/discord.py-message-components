# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2022-present mccoderpy

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
import copy
import asyncio
import inspect
import warnings
from .utils import async_all, find, get, snowflake_time
from typing_extensions import Literal
from .abc import User, GuildChannel, Role
from typing import Union, Optional, List, Dict, Any, Awaitable, TYPE_CHECKING
from .enums import Enum, ApplicationCommandType, InteractionType, ChannelType, OptionType, Locale, try_enum
from .permissions import Permissions

if TYPE_CHECKING:
    from .ext.commands import Cog
    from datetime import datetime


__all__ = (
    'Localizations',
    'ApplicationCommand',
    'SlashCommand',
    'GuildOnlySlashCommand',
    'SlashCommandOption',
    'SlashCommandOptionChoice',
    'SubCommandGroup',
    'GuildOnlySubCommandGroup',
    'SubCommand',
    'GuildOnlySubCommand',
    'UserCommand',
    'MessageCommand',
    'generate_options'
)

api_docs = 'https://discord.com/developers/docs'

# TODO: Add a (optional) feature for auto generated name_localizations & description_localizations by a translator
class Localizations:
    __slots__ = tuple([locale_name for locale_name in Locale._enum_member_map_] + ['__languages_dict__'])

    def __init__(self, **kwargs) -> None:
        self.__languages_dict__ = {}
        for locale in self.__slots__:
            try:
                text = kwargs[locale]
            except KeyError:
                continue
            else:
                self.__languages_dict__[Locale[locale].value] = text
                setattr(self, locale, text)

    def __repr__(self) -> str:
        return '<Localizations specified languages: %s>' % ", ".join([Locale.try_value(l) for l in self.__languages_dict__])

    def __getitem__(self, item) -> Optional[str]:
        return self.__languages_dict__.__getitem__(Locale[locale].value)

    def __setitem__(self, key, value):
        self__languages_dict__[Locale[key].value] = value

    def __bool__(self) -> bool:
        return bool(self.__languages_dict__)

    def to_dict(self) -> Dict[str, str]:
        return self.__languages_dict__ if self.__languages_dict__ else None

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Localizations':
        data = data or {}
        return cls(**{try_enum(cls, key): value for key, value in data.items()})

    def update(self, __m: 'Localizations'):
        self.__languages_dict__.update(__m.__languages_dict__)


class ApplicationCommand:
    def __init__(self, type: int, *args, **kwargs):
        self._type = type
        self.name = kwargs.get('name', '')
        self._guild_ids = kwargs.get('guild_ids', None)
        self._guild_id = kwargs.get('guild_id', None)
        self._state_ = kwargs.get('state', None)
        self.func = kwargs.pop('func', None)
        self.cog = kwargs.get('cog', None)
        dp = kwargs.get('default_permission', None)
        if dp is not None:
            warnings.warn('default_permission is deprecated, use default_member_permissions and allow_dm instead.', stacklevel=3, category=DeprecationWarning)
        dmp = kwargs.get('default_member_permissions', None)
        self.default_member_permissions: Optional[Permissions] = (Permissions(int(dmp)) if dmp is not None else None) if not isinstance(dmp, Permissions) else dmp
        self.disabled: bool = False
        self.allow_dm = kwargs.get('allow_dm', True)
        self.name_localizations: Localizations = kwargs.get('name_localizations', Localizations())
        self.description_localizations: Localizations = kwargs.get('description_localizations', Localizations())

    @property
    def _state(self):
        return self._state_

    @_state.setter
    def _state(self, value):
        setattr(self, '_state_', value)

    @property
    def cog(self) -> Optional['Cog']:
        return getattr(self, '_cog', None)

    @cog.setter
    def cog(self, __cog: 'Cog'):
        setattr(self, '_cog', __cog)

    def _set_cog(self, cog: 'Cog', recursive: bool = False):
        self.cog = cog

    def __call__(self, *args, **kwargs):
        return super().__init__(self, *args, **kwargs)

    def __repr__(self):
        return '<%s name=%s, id=%s, disabled=%s>' % (self.__class__.__name__, self.name, self.id, self.disabled)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            other = other.to_dict()
        if isinstance(other, dict):
            def check_options(_options: list, _other: list):
                if not len(_options) and not len(_other):
                    return True
                if len(_options) != len(_other):
                    return False
                for index, option in enumerate(_other):
                    opt = find(lambda o: o['name'] == option['name'], _options)
                    if not opt:
                        return False
                    try:
                        if index != _options.index(opt) and opt['type'] not in (1, 2):
                            return False
                    except IndexError:
                        return False
                for index, option in enumerate(_options):
                    opt = find(lambda o: option['name'] == o['name'], _other)
                    try:
                        if index != _other.index(opt) and opt['type'] not in (1, 2):
                            return False
                    except IndexError:
                        return False
                    if option['type'] in (1, 2):
                        if not check_options(option.get('options', []), opt.get('options', [])):
                            return False
                    for key in ('type', 'name', 'name_localizations', 'description', 'description_localizations',
                                'required', 'choices', 'min_value', 'max_value', 'autocomplete'):
                        current_value = option.get(key, None)
                        if current_value != opt.get(key, None):
                            return False
                    if sorted(opt.get('channel_types', [])) != sorted(option.get('channel_types', [])):
                        return False
                return True
            if hasattr(self, 'options') and self.options:
                options = [o.to_dict() for o in self.options]
            elif hasattr(self, 'sub_commands') and self.sub_commands:
                options = [s.to_dict() for s in self.sub_commands]
            else:
                options = []
            dmp = str(self.default_member_permissions.value) if self.default_member_permissions else None
            return bool(int(self.type) == other.get('type') and self.name == other.get('name', None)
                        and self.name_localizations.to_dict() == other.get('name_localizations', None)
                        and getattr(self, 'description', '') == other.get('description', '')
                        and self.description_localizations.to_dict() == other.get('description_localizations', None)
                        and dmp == other.get('default_member_permissions', None)
                        and self.allow_dm == other.get('dm_permission', True)
                        and check_options(options, other.get('options', [])))
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def _fill_data(self, data):
        self._id = int(data.get('id', 0))
        self.application_id = int(data.get('application_id', 0))
        self._guild_id = int(data.get('guild_id', 0))
        self._permissions = data.get('permissions', {})
        return self

    async def can_run(self, *args, **kwargs):
        check_func = kwargs.pop('__func', self)
        checks = getattr(check_func, '__command_checks__', getattr(self.func, '__command_checks__', None))
        if not checks:
            return True

        return await async_all(check(*args) for check in checks)

    async def invoke(self, interaction, *args, **kwargs):
        if self.cog is not None:
            args = (self.cog, interaction, *args)
        else:
            args = (interaction, *args)
        try:
            if await self.can_run(*args):
                await self.func(*args, **kwargs)
        except Exception as exc:
            if hasattr(self, 'on_error'):
                if self.cog is not None:
                    await self.on_error(self.cog, interaction, exc)
                else:
                    await self.on_error(interaction, exc)
            else:
                self._state.dispatch('application_command_error', self, interaction, exc)

    def error(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler must be a coroutine.')
        self.on_error = coro
        return coro

    def to_dict(self):
        base = {
            'type': int(self.type),
            'name': str(self.name),
            'name_localizations': self.name_localizations.to_dict(),
            'description': getattr(self, 'description', ''),
            'description_localizations': self.description_localizations.to_dict(),
            'default_member_permissions': str(self.default_member_permissions.value) if self.default_member_permissions else None
        }
        if not self.guild_id:
            base['dm_permission'] = self.allow_dm
        if hasattr(self, 'options') and self.options:
            base['options'] = [o.to_dict() for o in self.options]
        elif hasattr(self, 'sub_commands') and self.sub_commands:
            base['options'] = [sc.to_dict() for sc in self.sub_commands]
        return base

    @property
    def id(self):
        return getattr(self, '_id', None)

    @property
    def created_at(self) -> Optional['datetime.datetime']:
        if self.id:
            return snowflake_time(self.id)

    @property
    def type(self) -> ApplicationCommandType:
        return try_enum(ApplicationCommandType, self._type)

    @property
    def guild_id(self):
        return self._guild_id

    @property
    def guild_ids(self):
        return self._guild_ids

    @classmethod
    def _from_type(cls, state, data):
        command_type = data['type']
        if command_type == 1:
            return SlashCommand.from_dict(state, data)
        elif command_type == 2:
            return UserCommand.from_dict(state, data)
        elif command_type == 3:
            return MessageCommand.from_dict(state, data)
        else:
            return None

    @classmethod
    def _sorted_by_type(cls, commands):
        sorted_dict = {'chat_input': [], 'user': [], 'message': []}
        for cmd in commands:
            if cmd['type'] == 1:
                predicate = 'chat_input'
            elif cmd['type'] == 2:
                predicate = 'user'
            elif cmd['type'] == 3:
                predicate = 'message'
            else:
                continue
            sorted_dict[predicate].append(cmd)
        return sorted_dict

    async def delete(self):
        if self.guild_id != 0:
            guild_id = self.guild_id
        else:
            guild_id = None
        await self._state.http.delete_application_command(self.application_id, self.id, guild_id)
        if guild_id:
            self._state._get_client()._remove_application_command(self, from_cache=True)


class SlashCommandOptionChoice:
    def __init__(self, name: str, value: Union[str, int, float] = None, name_localizations: Optional[Localizations] = Localizations()):
        """
        A class representing a choice for a :class:`SelectOption` or :class:`SubCommand`.

        Parameters
        ----------
        name: :class:`str`
            The 1-100 characters long name that will shows in the client.
        value: Union[:class:`str`, :class:`int`, :class:`float`]
            The value that will send as the options value.
            Must be of the type the option is of (:class:`str`, :class:`int` or :class:`float`).
        name_localisations: Dict[:class:`str`, :class:`glas`]
        """
        if 100 < len(name) < 1:
            raise ValueError('The name of a choice must bee between 1 and 100 characters long, got %s.' % len(name))
        self.name = name
        self.value = value if value is not None else name
        self.name_localizations = name_localizations

    def __repr__(self):
        return '<SlashCommandOptionChoice name=%s, value=%s>' % (self.name, self.value)

    def to_dict(self):
        base = {
            'name': str(self.name),
            'value': self.value,
            'name_localizations': self.name_localizations.to_dict()
        }
        return base

    @classmethod
    def from_dict(cls, data):
        return cls(name=data['name'], value=data['value'], name_localizations=Localizations(**data.get('name_localizations', {})))


class SlashCommandOption:
    __slots__ = ('type', 'name', 'name_localizations', 'description', 'description_localizations',
                 'required', 'default', '_choices', 'options', '_autocomplete',
                 '_min_value', '_max_value', '_channel_types')

    def __init__(self,
                 option_type: Union[OptionType, int, type],
                 name: str,
                 description: str,
                 name_localizations: Optional[Localizations] = Localizations(),
                 description_localizations: Optional[Localizations] = Localizations(),
                 required: bool = True,
                 choices: Optional[List[SlashCommandOptionChoice]] = [],
                 autocomplete: bool = False,
                 min_value: Optional[Union[int, float]] = None,
                 max_value: Optional[Union[int, float]] = None,
                 channel_types: Optional[List[Union[type(GuildChannel), ChannelType, int]]] = None,
                 default: Optional[Any] = None,
                 **kwargs) -> None:
        """
        Representing an option for a :class:`SlashCommand`/:class:`SubCommand`.

        Parameters
        ----------
        option_type: Union[:class:`OptionType`, :class:`int`, :class:`type`]
            Could be any of :class:`OptionType`'s attributes, an integer between 0 and 10 or a :type:`type` like
            ``discord.Member``, ``discord.TextChannel`` or ``str``.
            If the :param:`option_type` is a :class:`type`, that subclasses :class:`abc.GuildChannel` the type of the
            channel would set as the defualt :param:`channel_types`.
        name: :class:`str`
            The 1-32 characters long name of the option shows up in discord.
            The name must be the same as the one of the parameter for the slash-command
            or connected using :param:`connector` of :class:`SlashCommand`/:class:`SubCommand` or the method
            that generates one of these.
        description: :class:`str`
            The 1-100 characters long description of the option shows up in discord.
        required: Optional[:class:`bool`]
            Wheater this option must be provided by the user, default ``True``.
            If ``False``, the parameter of the slash-command that takes this option needs a default value.
        choices: Optional[List[:class:`SlashCommandOptionChoice`]]
            A list of up to 25 choices the user could select. Only valid if the :param:`option_type` is one of
            :class:`OptionType.string`, :class:`OptionType.integer` or :class:`OptionType.number`.
            The :attr:`value`'s of the choices must be of the :param:`option_type` of this option
            (e.g. :class:`str`, :class:`int` or :class:`float`).
            If choices are set they are the only options a user could pass.
        autocomplete: Optional[:class:`bool`]
            Whether to enable
            `autocomplete <https://discord.com/developers/docs/interactions/application-commands#autocomplete>`_
            interactions for this option, default ``False``.
            With autocomplete, you can check the user's input and send matching choices to the client.
            **Autocomplete can only be used with options of the type** ``string``, ``integer`` or ``number``.
            **If autocomplete is activated, the option cannot have** :param:`choices` **.**
        min_value: Optional[Union[:class:`int`, :class:`float`]]
            If the :param:`option_type` is one of :class:`OptionType.integer` or :class:`OptionType.number`
            this is the minimum value the users input must be of.
        max_value: Optional[Union[:class:`int`, :class:`float`]]
            If the :param:`option_type` is one of :class:`OptionType.integer` or :class:`OptionType.number`
            this is the maximum value the users input could be of.
        channel_types: Optional[List[Union[:class:`abc.GuildChannel`, :class:`ChannelType`, :class:`int`]]]
            A list of :class:`ChannelType` or the type itself like ``TextChannel`` or ``StageChannel`` the user could select.
            Only valid if :param:`option_type` is :class:`OptionType.channel`.
        default: Optional[Any]
            The default value that should be passed to the function if the option is not providet, default ``None``.
            Usuly used for autocomplete callback.
        """
        #print(name, option_type)
        if not isinstance(option_type, OptionType):
            option_type, channel_type = OptionType.from_type(option_type)
            if channel_type and not channel_types:
                channel_types = channel_type
            if not isinstance(option_type, OptionType):
                print(type(option_type), option_type)
                raise TypeError(f'Discord does not has a option_type for {option_type.__class__.__name__}.')
        self.type = option_type

        if not re.match(r'^[-_\w\d\u0901-\u097D\u0E00-\u0E7F]{1,32}$', name, flags=re.RegexFlag.UNICODE):
            raise ValueError(
                r'Command names and options must follow the regex "^[-_\w\d\u0901-\u097D\u0E00-\u0E7F]{1,32}$"'
                f'{api_docs}/interactions/application-commands#application-command-object-application-command-naming.'
                f'Got "{name}" with length {len(name)}.'
            )
        self.name = name
        self.name_localizations: Localizations = name_localizations
        if 100 < len(description) < 1:
            raise ValueError('The description must be between 1 and 100 characters long, got %s.' % len(description))
        self.description = description
        self.description_localizations: Localizations = description_localizations
        self.required = required
        options = kwargs.get('options', [])
        if self.type == 2 and (not options):
            raise ValueError('You need to pass options if the option_type is subcommand_group.')
        self.options = options
        self.autocomplete: bool = autocomplete
        self.min_value: Optional[Union[int, float]] = min_value
        self.max_value: Optional[Union[int, float]] = max_value
        self.choices: Optional[List[SlashCommandOptionChoice]] = choices
        self.channel_types: Optional[List[Union[GuildChannel, ChannelType, int]]] = channel_types
        self.default = default

    def __repr__(self):
        return '<SlashCommandOption type=%s, name=%s, description=%s, required=%s, choices=%s>'\
               % (self.type,
                  self.name,
                  self.description,
                  self.required,
                  self.choices)

    @property
    def autocomplete(self) -> bool:
        """
        Whether to enable
        `autocomplete <https://discord.com/developers/docs/interactions/application-commands#autocomplete>`_
        interactions for this option.
        With autocomplete, you can check the user's input and send matching choices to the client.

        .. note::
            Autocomplete can only be used with options of the type :class:`OptionType.string`,
            :class:`OptionType.integer` or :class:`OptionType.number`.
            If autocomplete is activated, the option cannot have :attr:`choices`.
        """
        return getattr(self, '_autocomplete', False)

    @autocomplete.setter
    def autocomplete(self, value: bool) -> None:
        if bool(value) is True:
            if self.type not in (OptionType.string, OptionType.integer, OptionType.number):
                raise TypeError('Only Options of type string, integer or number could have autocomplete.')
            elif self.choices:
                raise TypeError('Options with choices could not have autocomplete.')
        self._autocomplete = bool(value)

    @property
    def choices(self) -> Optional[List[SlashCommandOptionChoice]]:
        """
        The coices that are set for this option

        Returns
        -------
        Optional[List[:class:`SlashCommandOptionChoice`]]
        """
        return getattr(self, '_choices', None)

    @choices.setter
    def choices(self, value: Optional[List[SlashCommandOptionChoice]]) -> None:
        if value:
            if self.type not in (OptionType.string, OptionType.integer, OptionType.number):
               raise TypeError('Only Options of type string, integer or number could have choices.')
            elif self.autocomplete:
                raise TypeError('Options with autocomplete could not have choices.')
        if len(value) > 25:
            raise ValueError('The maximum of choices per Option is 25, got %s.'
                             'It is recommended to use autocomplete if you have more than 25 options.' % len(choices))
        self._choices = value

    @property
    def min_value(self) -> Optional[Union[int, float]]:
        """
        The minimum value a user could enter that is set

        Returns
        -------
        Optional[Union[:class:`int`, :class:`float`]]
        """
        return getattr(self, '_min_value', None)

    @min_value.setter
    def min_value(self, value) -> None:
        if value is not None:
            if self.type not in (OptionType.integer, OptionType.number):
                raise TypeError('Only Options of type integer or number could have a min_value or/and max_value.')
        self._min_value = value

    @property
    def max_value(self) -> Optional[Union[int, float]]:
        """
        The maximum value a user could enter that is set.

        Returns
        -------
        Optional[Union[:class:`int`, :class:`float`]]
        """
        return getattr(self, '_max_value', None)

    @max_value.setter
    def max_value(self, value) -> None:
        if value is not None:
            if self.type not in (OptionType.integer, OptionType.number):
                raise TypeError('Only Options of type integer or number could have a min_value or/and max_value.')
        self._max_value = value

    @property
    def channel_types(self) -> Optional[List[ChannelType]]:
        """
        The types of channels that could be selected.

        Returns
        -------
        Optional[List[:class:`ChannelType`]]
        """
        return getattr(self, '_channel_types')

    @channel_types.setter
    def channel_types(self, value) -> None:
        if value is not None:
            if self.type != OptionType.channel:
                raise TypeError('Only options of type channel could have channel_types.')
            for index, c in enumerate(value):
                if not isinstance(c, ChannelType):
                    value[index] = ChannelType.from_type(c)
            if not any([isinstance(c, ChannelType) for c in value]):
                raise
        self._channel_types = value

    def to_dict(self) -> dict:
        base = {
            'type': int(self.type),
            'name': str(self.name),
            'description': str(self.description)
        }
        if bool(self.required) is True:
            base['required'] = bool(self.required)
        if self.choices:
            base['choices'] = [c.to_dict() for c in self.choices]
        elif self.autocomplete:
            base['autocomplete'] = True
        elif self.options:
            base['options'] = [o.to_dict() for o in self.options]
        if self.min_value is not None:
            base['min_value'] = self.min_value
        if self.max_value is not None:
            base['max_value'] = self.max_value
        if self.channel_types:
            base['channel_types'] = [int(ch_type) for ch_type in self.channel_types]
        return base

    @classmethod
    def from_dict(cls, data):
        option_type: OptionType = try_enum(OptionType, data['type'])
        if option_type.sub_command_group:
            return SubCommandGroup.from_dict(data)
        elif option_type.sub_command:
            return SubCommand.from_dict(data)
        return cls(
            option_type=try_enum(OptionType, data['type']),
            name=data['name'],
            description=data.get('description', 'No description'),
            required=data.get('required', False),
            choices=[SlashCommandOptionChoice.from_dict(c) for c in data.get('choices', [])],
            autocomplete=data.get('autocomplete', False),
            min_value=data.get('min_value', None),
            max_value=data.get('max_value', None)
        )


class SubCommand(SlashCommandOption):
    def __init__(self,
                 parent,
                 name: str,
                 description: str,
                 name_localizations: Optional[Localizations] = Localizations(),
                 description_localizations: Optional[Localizations] = Localizations(),
                 options: List[SlashCommandOption] = [],
                 **kwargs):
        self.parent: Union[SubCommandGroup, SubCommand] = parent
        if not re.match('^[-_\w\d\u0901-\u097D\u0E00-\u0E7F]{1,32}$', name):
            raise ValueError(
                r'Command names and options must follow the regex "^[-_\w\d\u0901-\u097D\u0E00-\u0E7F]{1,32}$"'
                f'{api_docs}/interactions/application-commands#application-command-object-application-command-naming.'
                f'Got "{name}" with length {len(name)}.'
            )
        self.name = name
        if 100 < len(description) < 1:
            raise ValueError('The description of the Sub-Command must be 1-100 characters long, got %s.' % len(description))
        if len(options) > 25:
            raise ValueError('The maximum of options per Sub-Command is 25, got %s.' % len(options))
        self.options = options
        self.func = kwargs.get('func', None)
        self.cog = kwargs.get('cog', None)
        self.connector = kwargs.get('connector', {})
        self.guild_id = kwargs.get('guild_id', parent.guild_id)
        super().__init__(OptionType.sub_command, name=name, description=description,
                         name_localizations=name_localizations, description_localizations=description_localizations,
                         options=options)

    def __repr__(self):
        return '<SubCommand parent=%s, name=%s, description=%s, options=%s>' \
               % (self.parent.name,
                  self.name,
                  self.description,
                  self.options)

    def to_dict(self):
        base = {
            'type': 1,
            'name': str(self.name),
            'name_localizations': self.name_localizations.to_dict(),
            'description': str(self.description),
            'description_localizations': self.description_localizations.to_dict(),
            'options': [c.to_dict() for c in self.options]
        }
        return base

    async def can_run(self, *args, **kwargs):
        if self.cog is not None:
            args = (self.cog, *args)
        checks = getattr(self, '__command_checks__', [])
        if not checks:
            return True

        return await async_all(check(*args, **kwargs) for check in checks)

    async def invoke(self, interaction, *args, **kwargs):
        if self.cog is not None:
            args = (self.cog, interaction, *args)
        else:
            args = (interaction, *args)
        try:
            if await self.can_run(*args):
                await self.func(*args, **kwargs)
        except Exception as exc:
            if hasattr(self, 'on_error'):
                if self.cog is not None:
                    await self.on_error(self.cog, interaction, exc)
                else:
                    await self.on_error(interaction, exc)
            else:
                self.parent.parent._state.dispatch('application_command_error', self, interaction, exc)

    def autocomplete_callback(self, coro):
        """
        A decortator that sets a coroutine function as the function that will be called
        when discord sends an autocomplete interaction for this command.

        Parameters
        ----------
        coro: Awaitable
            The function that should be set as autocomplete_func for this command.
            Must take the same amount of params the command itself takes.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The autocomplete callback function must be a coroutine.')
        self.autocomplete_func = coro

    async def invoke_autocomplete(self, interaction, *args, **kwargs):
        if not self.autocomplete_func:
            print(f'Sub-Command {self.name} of {self.parent} has options with autocomplete enabled but no autocomplete function.')
            return

        if self.cog is not None:
            args = (self.cog, interaction, *args)
        else:
            args = (interaction, *args)
        try:
            if await self.can_run(*args, __func=self.autocomplete_func):
                await self.autocomplete_func(*args, **kwargs)
        except Exception as exc:
            if hasattr(self, 'on_error'):
                if self.cog is not None:
                    await self.on_error(self.cog, interaction, exc)
                else:
                    await self.on_error(interaction, exc)
            else:
                self.parent.parent._state.dispatch('application_command_error', self, interaction, exc)

    def error(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler registered must be a coroutine.')
        self.on_error = coro
        return coro

    @classmethod
    def from_dict(cls, data):
        return cls(
            parent=data.get('parent', None),
            name=data['name'],
            name_localizations=Localizations.from_dict(data.get('name_localizations', {})),
            description=data.get('description', 'No description'),
            description_localizations=Localizations.from_dict(data.get('description_localizations', {})),
            options=[SlashCommandOption.from_dict(c) for c in data.get('options', [])],
        )

class GuildOnlySubCommand(SubCommand):
    """Represents a :class:`SubCommand` for multiple guilds with the same function."""
    def __init__(self, *args, guild_ids: List[int] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.guild_ids = guild_ids or self.parent.guild_ids
        self._commands = kwargs.get('commands', [])

    def __repr__(self):
        return '<GuildOnlySubCommand parent=%s, name=%s, description=%s, options=%s, guild_ids=%s>'\
               % (self.parent.name,
                  self.name,
                  self.description,
                  self.options,
                  ', '.join([str(g) for g in self.guild_ids])
                  )

    def error(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler registered must be a coroutine.')
        for cmd in self._commands:
            cmd.on_error = coro
        return coro


class SlashCommand(ApplicationCommand):
    def __init__(self,
                 name: str,
                 description: str,
                 name_localizations: Optional[Localizations] = Localizations(),
                 description_localizations: Optional[Localizations] = Localizations(),
                 default_member_permissions: Optional[Union[Permissions, int]] = None,
                 allow_dm: Optional[bool] = True,
                 options: List[SlashCommandOption] = [],
                 connector: Dict[str, str] = {},
                 **kwargs):
        """
        Represents a slash-command.
        You should use the :class:`discord.Client.slash_command` or :class:`discord.ext.commands.Cog.slash_command`
        decorator by default to create this.

        Parameters
        ----------
        name: :class:`str`
            The name of the slash-command. Must be between 1 and 32 characters long and oly contain a-z, _ and -.
        description: :class:`str`
            The description of the command shows up in discord. Between 1 and 100 characters long.
        default_permission: Optional[:class:`bool`]
            Wheater user could use this command by default, default ``True``.
            If ``False`` the command will no longe be avaible in direct messages.
        options: Optional[List[:class:`SlashCommandOption`]]
            A list of max. 25 options for the command.
            Required options **must** be listed before optional ones.
        connector: Optional[Dict[:class:`str`, :class:`str`]]
            A dictionary containing the name of function-parameters as keys and the name of the option as values.
            Useful for using non-ascii Letters in your option names without getting ide-errors.
        kwargs:
            Keyword arguments used for internal handlig.
        """
        self.autocomplete_func = None
        super().__init__(1,
                         name=name,
                         description=description,
                         name_localizations=name_localizations,
                         description_localizations=description_localizations,
                         default_member_permissions=default_member_permissions,
                         allow_dm=allow_dm,
                         options=options,
                         connector=connector,
                         **kwargs)
        if not re.match(r'^[-_\w\d\u0901-\u097D\u0E00-\u0E7F]{1,32}$', name):
            raise ValueError(
                r'Command names and options must follow the regex "^[-_\w\d\u0901-\u097D\u0E00-\u0E7F]{1,32}$"'
                f'{api_docs}/interactions/application-commands#application-command-object-application-command-naming.'
                f'Got "{name}" with length {len(name)}.'
            )
        self.name = name
        if 100 < len(description) < 1:
            raise ValueError('The description must be between 1 and 100 characters long, got %s.' % len(description))
        self.description = description
        if len(options) > 25:
            raise ValueError('The maximum of options per command is 25, got %s' % len(options))
        self.connector = connector
        self._sub_commands = {command.name: command for command in options if OptionType.try_value(command.type) in (OptionType.sub_command, OptionType.sub_command_group)}
        if not self._sub_commands:
            self._options = {option.name: option for option in options}
        for sc in self.sub_commands:
            sc.parent = self

    def __repr__(self):
        return '<SlashCommand name=%s, description=%s, default_member_permissions=%s, options=%s, guild_id=%s disabled=%s, id=%s>' \
               % (self.name,
                  self.description,
                  self.default_member_permissions,
                  self.options or self.sub_commands,
                  self.guild_id or 'None',
                  self.disabled,
                  self.id)

    @property
    def _state(self):
        return getattr(self, '_state_', None)

    @_state.setter
    def _state(self, value):
        setattr(self, '_state_', value)
        for sc in self.sub_commands:
            sc.parent = self

    @property
    def parent(self):
        return self

    @property
    def cog(self) -> Optional['Cog']:
        return getattr(self, '_cog', None)

    @cog.setter
    def cog(self, __cog: 'Cog'):
        setattr(self, '_cog', __cog)

    def _set_cog(self, cog: 'Cog', recursive: bool = False):
        self.cog = cog
        if recursive:
            for command in self.sub_commands:
                if command.type.sub_command_group:
                    for sub_command in command.sub_commands:
                        sub_command.cog = cog
                command.cog = cog

    @property
    def has_subcommands(self) -> bool:
        return bool(self.sub_commands)

    def autocomplete_callback(self, coro):
        """
        A decortator that sets a coroutine function as the function that will be called
        when discord sends an autocomplete interaction for this command.

        Parameters
        ----------
        coro: Awaitable
            The function that should be set as autocomplete_func for this command.
            Must take the same amount of params the command itself takes.

        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The autocomplete callback function must be a coroutine.')
        self.autocomplete_func = coro

    async def invoke_autocomplete(self, interaction, *args, **kwargs):
        if self.autocomplete_func is None:
            print(f'Application Command {self.name} has options with autocomplete enabled but no autocomplete function.')
            return
        if self.cog is not None:
            args = (self.cog, interaction, *args)
        else:
            args = (interaction, *args)

        try:
            if await self.can_run(*args, __func=self.autocomplete_func):
                await self.autocomplete_func(*args, **kwargs)
        except Exception as exc:
            if hasattr(self, 'on_error'):
                if self.cog is not None:
                    await self.on_error(self.cog, interaction, exc)
                else:
                    await self.on_error(interaction, exc)
            else:
                self._state.dispatch('application_command_error', self, interaction, exc)

    @property
    def sub_commands(self) -> Optional[List[Union['SubCommandGroup[SubCommand]', SubCommand]]]:
        """A :class:`list` of :class:`SubCommand` and :class:`SubCommandGroup` the command has."""
        return list(self._sub_commands.values())

    @property
    def options(self) -> Optional[List[SlashCommandOption]]:
        """A :class:`list` of :class:`SlashCommandOption` the command has."""
        return list(getattr(self, '_options', {}).values())

    @classmethod
    def from_dict(cls, state, data):
        self: cls = cls.__new__(cls)
        dmp = data.get('default_member_permissions', None)
        self._type = ApplicationCommandType.chat_input
        self.disabled = False
        self.connector = {}
        self.name = data.pop('name')
        self.name_localizations = Localizations.from_dict(data.get('name_localizations', {}))
        self.description = data.pop('description', 'No Description')
        self.description_localizations = Localizations.from_dict(data.get('description_localizations', {}))
        self.default_member_permissions = Permissions(int(dmp)) if dmp else None
        self.allow_dm = data.pop('dm_permission', True)
        self._guild_id = int(data.get('guild_id', 0))
        self._state_ = state
        for opt in data.get('options', []):
            opt['parent'] = self
        options = [SlashCommandOption.from_dict(opt) for opt in data.pop('options', [])]
        self._sub_commands = {command.name: command for command in options if OptionType.try_value(command.type) in (
        OptionType.sub_command, OptionType.sub_command_group)}
        if not self._sub_commands:
            self._options = {option.name: option for option in options}
        return self

    @staticmethod
    def _filter_id_out(argument):
        return int(argument.strip('<!@&#>'))

    async def invoke(self, interaction, *args, **kwargs):
        if not self.func:
            return
        if self.cog is not None:
            args = (self.cog, interaction, *args)
        else:
            args = (interaction, *args)

        try:
            if await self.can_run(*args):
                await self.func(*args, **kwargs)
        except Exception as exc:
            if hasattr(self, 'on_error'):
                if self.cog is not None:
                    await self.on_error(self.cog, interaction, exc)
                else:
                    await self.on_error(interaction, exc)
            else:
                self._state.dispatch('application_command_error', self, interaction, exc)

    async def _parse_arguments(self, interaction):
        to_invoke = self
        params = {}
        options = interaction.data.options
        if options:
            if options[0].type in (OptionType.sub_command_group, OptionType.sub_command):
                if options[0].type == OptionType.sub_command_group:
                    command_group: SubCommandGroup = self._sub_commands[options[0].name]
                    sub_command: SubCommand = command_group._sub_commands[options[0].options[0].name]
                    options = options[0].options[0].options

                else:
                    sub_command: SubCommand = self._sub_commands[options[0].name]
                    options = options[0].options
                to_invoke = sub_command
            connector = to_invoke.connector
            for option in options:
                name = connector.get(option.name) or option.name
                if option.type in (OptionType.string, OptionType.integer, OptionType.boolean, OptionType.number):
                    params[name] = option.value
                elif option.type == OptionType.user:
                    _id = self._filter_id_out(option.value)
                    params[name] = interaction.data.resolved.members[_id] or interaction.data.resolved.users[_id] or option.value
                elif option.type == OptionType.role:
                    _id = self._filter_id_out(option.value)
                    params[name] = interaction.data.resolved.roles[_id] or option.value
                elif option.type == OptionType.channel:
                    _id = self._filter_id_out(option.value)
                    params[name] = interaction.data.resolved.channels[_id] or option.value
                elif option.type == OptionType.mentionable:
                    _id = self._filter_id_out(option.value)
                    if '&' in option.value:
                        params[name] = interaction.data.resolved.roles[_id] or option.value
                    else:
                        params[name] = interaction.data.resolved.members[_id] or interaction.data.resolved.users[_id] or option.value
                elif option.type == OptionType.attachment:
                    _id = self._filter_id_out(option.value)
                    params[name] = interaction.data.resolved.attachments[_id] or option.value

        # pass the default values of the options to the params if they are not providet (usaly used for autocomplete)
        connector = to_invoke.connector
        for o in to_invoke.options:
            name = connector.get(o.name, o.name)
            if name not in params and o.default is not None:
                params[name] = o.default

        interaction._command = self
        interaction.params = params
        if interaction.type == InteractionType.ApplicationCommandAutocomplete:
            interaction.focused = find(lambda o: (o.__getattribute__('focused') or None == True), options)
            return await to_invoke.invoke_autocomplete(interaction, **params)
        return await to_invoke.invoke(interaction, **params)


class GuildOnlySlashCommand(SlashCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands = kwargs.get('commands', [])

    def __repr__(self):
        return '<GuildOnlySlashCommand name=%s, description=%s, default_member_permissions=%s, options=%s, guild_ids=%s>'\
               % (self.name,
                  self.description,
                  self.default_member_permissions,
                  self.options,
                  ', '.join([str(g) for g in self.guild_ids])
                  )

    def error(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler registered must be a coroutine.')
        for cmd in self._commands:
            cmd.on_error = coro
        return coro


class UserCommand(ApplicationCommand):
    def __init__(self,
                 name: str,
                 name_localizations: Optional[Localizations] = None,
                 default_member_permissions: Optional[Union[Permissions, int]] = None,
                 allow_dm: Optional[bool] = True,
                 **kwargs):
        if 32 < len(name) < 1:
            raise ValueError('The name of the User-Command has to be 1-32 characters long, got %s.' % len(name))
        super().__init__(2, name=name, name_localizations=name_localizations, default_member_permissions=default_member_permissions, allow_dm=allow_dm, **kwargs)
    
    @classmethod
    def from_dict(cls, state, data):
        dmp = data.get('default_member_permissions', None)
        return cls(
            name=data.pop('name'),
            name_localizations=Localizations.from_dict(data.get('name_localizations', {})),
            default_member_permissions=int(dmp) if dmp else None,
            allow_dm=data.get('dm_permission', True),
            state=state,
            **data
        )

    async def _parse_arguments(self, interaction):
        await self.invoke(interaction, interaction.target)


class MessageCommand(ApplicationCommand):
    def __init__(self,
                 name: str,
                 name_localizations: Optional[Localizations] = Localizations(),
                 default_member_permissions: Optional[Union[Permissions, int]] = None,
                 allow_dm: Optional[bool] = True,
                 **kwargs):
        if 32 < len(name) < 1:
            raise ValueError('The name of the Message-Command has to be 1-32 characters long, got %s.' % len(name))
        super().__init__(3, name=name, name_localizations=name_localizations, default_member_permissions=default_member_permissions, allow_dm=allow_dm, **kwargs)

    @classmethod
    def from_dict(cls, state, data):
        dmp = data.get('default_member_permissions', None)
        return cls(
            name=data.pop('name'),
            name_localizations=Localizations.from_dict(data.get('name_localizations', {})),
            default_member_permissions=int(dmp) if dmp else None,
            allow_dm=data.get('dm_permission', True),
            state=state,
            **data
        )

    async def _parse_arguments(self, interaction):
        await self.invoke(interaction, interaction.target)


class SubCommandGroup(SlashCommandOption):
    def __init__(self,
                 parent: Union[SlashCommand, GuildOnlySlashCommand],
                 name: str,
                 description: str,
                 name_localizations: Optional[Localizations] = Localizations(),
                 description_localizations: Optional[Localizations] = Localizations(),
                 commands: List[SubCommand] = [],
                 **kwargs):
        self.cog = kwargs.get('cog', None)
        if not re.match(r'^[-_\w\d\u0901-\u097D\u0E00-\u0E7F]{1,32}$', name):
            raise ValueError(
                r'Command names and options must follow the regex "^[-_\w\d\u0901-\u097D\u0E00-\u0E7F]{1,32}$"'
                f'{api_docs}/interactions/application-commands#application-command-object-application-command-naming.'
                f'Got "{name}" with length {len(name)}.'
            )
        self.name = name
        if 100 < len(description) < 1:
            raise ValueError('The description of the Sub-Command-Group must be 1-100 characters long, got %s.' % len(description))
        if 25 < len(commands) < 1:
            raise ValueError('A Sub-Command-Group needs 1-25 sub-sub_commands, got %s.' % len(commands))
        self.guild_ids = kwargs.get('guild_ids', parent.guild_ids)
        self.guild_id = kwargs.get('guild_id', parent.guild_id)
        self.func = kwargs.get('func', None)
        super().__init__(OptionType.sub_command_group, name=name, name_localizations=name_localizations,
                         description=description, description_localizations=description_localizations,
                         options=commands)
        self._sub_commands = {command.name: command for command in commands}
        for sub_command in self.sub_commands:
            sub_command.parent = self

        self.parent = parent

    def __repr__(self):
        print(self.to_dict())
        return '<SubCommandGroup parent=%s, name=%s, description=%s, sub_commands=%s>' % \
               (self.parent.name,
                self.name,
                self.description,
                ', '.join([sub_cmd.name for sub_cmd in self.sub_commands])
                )

    @property
    def parent(self) -> SlashCommand:
        return getattr(self, '_parent_', None)

    @parent.setter
    def parent(self, value) -> None:
        setattr(self, '_parent_', value)
        for sub_command in self.sub_commands:
            sub_command.parent = self

    @property
    def sub_commands(self):
        return list(self._sub_commands.values())

    def to_dict(self):
        base = {
            'type': 2,
            'name': str(self.name),
            'name_localizations': self.name_localizations.to_dict(),
            'description': str(self.description),
            'description_localizations': self.description_localizations.to_dict(),
            'options': [c.to_dict() for c in self.sub_commands]
        }
        return base

    @classmethod
    def from_dict(cls, data):
        return cls(
            parent=data.get('parent', None),
            name=data['name'],
            name_localizations=Localizations(data.get('name_localizations', {})),
            description=data.get('description', 'No description'),
            description_localizations=Localizations(data.get('description_localizations', {})),
            options=[SubCommand.from_dict(c) for c in data.get('options', [])]
        )


class GuildOnlySubCommandGroup(SubCommandGroup):
    def __init__(self,  *args, guild_ids: List[int] = None, **kwargs):
        super().__init__(*args, **kwargs, guild_ids=guild_ids)

    def __repr__(self):
        return '<GuildOnlySubCommandGroup parent=%s, name=%s, description=%s, sub_commands=%s, guild_ids=%s>' % \
               (self.parent.name,
                self.name,
                self.description,
                ', '.join([sub_cmd.name for sub_cmd in self.sub_commands]),
                ', '.join([str(g) for g in self.guild_ids])
                )


def generate_options(
        func: Awaitable[Any],
        descriptions: dict = {},
        descriptions_localizations: Dict[str, Localizations] = {},
        connector: dict = {},
        is_cog: bool = False):
    """
    This function is used to create the options for a :class:`SlashCommand`/:class:`SubCommand`
    out of the parameters of a functionn if no options are providet in the decorator.

    .. warning::
        It is recomered to specifiy the options for the slash-command in the decorator.

    Parameters
    ----------
    func: :class:`types.FunctionType`
        The function from whose parameters and annotations the options for the slash-command are generated.
    descriptions:  Optional[Dict[:class:`str`, :class:`str`]]
        A dictionary with the name of the parameter as key and the description as value.
        The default description would be "No Description".
    connector: Optional[Dict[:class:`str`, :class:`str`]]
        A dictionary containing the name of function-parameters as keys and the name of the option as values.
        Useful for using non-ascii letters in your option names without getting (IDE-)errors.
    is_cog: Optional[:class:`bool`]
        Wheater the :param:`func` is inside a :class:`discord.exc.commands.Cog`. Used for Error handling.

    Returns
    -------
    List[:class:`SlashCommandOption`]
        The options that where createt.

    Raises
    ------
    TypeError:
        The function/method specified at :param:`func` is missing a parameter to which the interaction object is passed.
    """
    options = []
    parameters = inspect.signature(func).parameters.values()
    if (not parameters) or is_cog and len(parameters) < 2:
        raise TypeError(f'The {"method" if is_cog else "function"} for the slash-command must take at least '
                        f'{"two parameters" if is_cog else "one parameter"}; {"self and " if is_cog else ""} a parameter'
                        f'that takes the Interaction object.')
    parameters = parameters.__iter__()
    if next(parameters).name in ('self', 'cls'):
        next(parameters)

    for param in parameters:
        description_localizations = descriptions_localizations.get(connector.get(param.name, param.name), Localizations())
        description = descriptions.get(param.name, descriptions.get(connector.get(param.name, ''), 'No Description'))
        name = connector.get(param.name, param.name)
        choices = []
        channel_types = []
        required = True
        is_channel = False
        default = None

        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD): # Skip parameters like *args and **kwargs
            continue
        if param.default is not inspect._empty:
            # If a default value for the parameter is set, then the option is not requiered.
            required = False
            default = param.default
        if param.annotation is inspect._empty:
            # The parameter is not anotated.
            # Since we can't know what the person wants, we assume it's a string, add the option and continue.
            options.append(
                SlashCommandOption(option_type=OptionType.string,
                                   name=name,
                                   description=description,
                                   description_localizations=description_localizations,
                                   required=required,
                                   default=default)
            )
            continue
        if isinstance(param.annotation, SlashCommandOption):
            # If you annotate a parameter with an instance of SlashCommandOption (not recomered)
            # yust add to the options and continue.
            param.annotation.name = name
            options.append(param.annotation)
            continue
        elif getattr(param.annotation, '__origin__', None) is Union:
            # The parameter is annotated with a Union so multiple types are possible.
            args = getattr(param.annotation, '__args__', [])
            _remove_none = []
            for arg in args:
                if arg is type(None): # If one of the types is NoneType, then the option is also not requiered.
                    if isinstance(args, tuple):
                        del arg
                    else:
                        _remove_none.append(arg)
                    required = False
                elif isinstance(arg, (GuildChannel, ChannelType)):
                    # If you use Union to define the types of channels you can choose from.
                    # For example only voice- and stage-channels.
                    channel_types.append(ChannelType.from_type(arg))
                    is_channel = True
            [args.remove(rn) for rn in _remove_none]
            if is_channel:
                options.append(
                    SlashCommandOption(option_type=OptionType.channel,
                                       name=name,
                                       required=required,
                                       channel_types=channel_types,
                                       description=description,
                                       description_localizations=description_localizations,
                                       default=default)
                )
                continue
            else:
                param = param.replace(annotation=args[0])
        elif getattr(param.annotation, '__origin__', None) is Literal:
            # Use Literal to specifiy choices in the annotation.
            args = getattr(param.annotation, '__args__', [])
            try:
                # Get all the values for the choices
                values = []
                for a in args:
                    if isinstance(a, dict):
                        values.extend(list(a.values()))
                    elif isinstance(a, (list, tuple)):
                        values.append(a[1])
                    else:
                        values.append(a)
            except Exception:
                raise ValueError(
                    'If you use Literal to declare choices for the Option you could only use the folowing shemas:'
                    '[name, value], (name, value) or {one_name: one_value, other_name: other_value, ...}'
                    'The way you do it is not supportet.'
                )
            if all([type(c) == type(values[0]) for c in values]):
                # Find out what type of option it is; string, integer or number. Default to string.
                option_type: Union[str, int, float] = type(values[0]) if isinstance(values[0], (str, int, float)) else str
            else:
                option_type = str
            for arg in args:
                if isinstance(arg, (list, tuple)):
                    choices.append(SlashCommandOptionChoice(str(arg[0]), option_type(arg[1])))
                elif isinstance(arg, dict):
                    for k, v in arg.items():
                        choices.append(SlashCommandOptionChoice(str(k), option_type(v)))
                else:
                    choices.append(SlashCommandOptionChoice(str(arg), option_type(arg)))
            options.append(
                SlashCommandOption(
                    option_type=option_type,
                    name=name,
                    description=description,
                    description_localizations=description_localizations,
                    requiered=required,
                    choices=choices,
                    default=default)
            )
            continue
        elif isinstance(param.annotation, dict):
            # Use a dictionary as annotation to declare choices for a option.
            values = list(param.annotation.values())
            if all([type(v) == type(values[0]) for v in values]):
                # Find out what type of option it is; string, integer or number. Default to string.
                option_type = type(values[0]) if isinstance(values[0], (str, int, float)) else str
            else:
                option_type = str
            for k, v in param.annotation.items():
                choices.append(SlashCommandOptionChoice(str(k), option_type(v)))
            options.append(
                SlashCommandOption(option_type=option_type,
                                   name=name,
                                   description=description,
                                   description_localizations=description_localizations,
                                   requiered=required,
                                   choices=choices,
                                   default=default)
            )
            continue
        _type, channel_types = OptionType.from_type(param.annotation) or (OptionType.string, None)
        options.append(
            SlashCommandOption(option_type=_type,
                               name=name,
                               description=description,
                               description_localizations=description_localizations,
                               required=required,
                               choices=choices,
                               channel_types=channel_types,
                               default=default)
        )
    return options
