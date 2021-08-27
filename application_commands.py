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

import re
import inspect
from .abc import User, GuildChannel, Role
import typing
import asyncio
from .utils import async_all
from .enums import Enum, ApplicationCommandType, try_enum


__all__ = ('OptionType',
           'ApplicationCommand',
           'SlashCommand',
           'SlashCommandOption',
           'SlashCommandOptionChoice',
           'SubCommandGroup',
           'SubCommand',
           'UserCommand',
           'MessageCommand')


class OptionType(Enum):
    sub_command       = 1
    sub_command_group = 2
    string            = 3
    integer           = 4
    boolean           = 5
    user              = 6
    channel           = 7
    role              = 8
    mentionable       = 9
    number            = 10

    def __int__(self):
        return getattr(self, 'value')

    def __str__(self):
        return getattr(self, 'name')

    @classmethod
    def from_type(cls, t):
        if issubclass(t, str):
            return cls.string
        if issubclass(t, bool):
            return cls.boolean
        if issubclass(t, int):
            return cls.integer
        if issubclass(t, User):
            return cls.user
        if issubclass(t, GuildChannel):
            return cls.channel
        if issubclass(t, Role):
            return cls.role
        if getattr(t, '__origin__', None) is typing.Union and any([issubclass(a, (User, Role)) for a in t.__args__]):
            return cls.mentionable


class ApplicationCommand:
    __slots__ = ('_type', 'name', 'description', 'default_permission',
                 '_permissions', 'options', '_id', 'application_id',
                 '_guild_id', '_guild_ids', 'func', 'cog', '_state_', 'on_error')

    def __init__(self, type: int, *args, **kwargs):
        self._type = type
        self._guild_ids = kwargs.get('guild_ids', None)
        self._guild_id = kwargs.get('guild_id', None)
        self._state_ = kwargs.get('state', None)
        self.func = kwargs.pop('func', None)
        self.cog = kwargs.get('cog', None)

    @property
    def _state(self):
        return self._state_

    @_state.setter
    def _state(self, value):
        setattr(self, '_state_', value)

    def __call__(self, *args, **kwargs):
        return super().__init__(self, *args, **kwargs)

    def __repr__(self):
        return '<%s name=%s, id=%s>' % (self.__class__.__name__, self.name, self.id)

    def __eq__(self, other):
        if isinstance(other, dict):
            if hasattr(self, 'options'):
                options = [o.to_dict() for o in self.options]
            else:
                options = []
            return self.name == other.get('name', None) and getattr(self, 'description', '') == other.get('description', '') and self.default_permission == other.get('default_permission', None) and other.get('options', []) == options

    def __ne__(self, other):
        return not self.__eq__(other)

    def _fill_data(self, data):
        self._id = int(data.get('id', 0))
        self.application_id = int(data.get('application_id', 0))
        self._guild_id = int(data.get('guild_id', 0))
        self._permissions = data.get('permissions', {})
        return self

    async def can_run(self, *args, **kwargs):
        if self.cog is not None:
            args = (self.cog, *args)
        checks = getattr(self, '__checks__', [])
        if not checks:
            return True

        return await async_all(check(*args, **kwargs) for check in checks)

    async def invoke(self, *args, **kwargs):
        if await self.can_run(*args, **kwargs):
            if self.cog is not None:
                args = (self.cog, *args)
            try:
                await self.func(*args, **kwargs)
            except Exception as exc:
                if hasattr(self, 'on_error'):
                    await self.on_error(exc, *args, **kwargs)
                self._state.dispatch('application_command_error', self, exc)

    def error(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler must be a coroutine.')
        self.on_error = coro
        return coro

    def to_dict(self):
        base = {
            'name': str(self.name),
            'type': int(self.type),
            'description': getattr(self, 'description', ''),
            'default_permission': bool(self.default_permission)
        }
        if hasattr(self, 'options'):
            base['options'] = [o.to_dict() for o in self.options]
        return base

    @property
    def id(self):
        return getattr(self, '_id', None)

    @property
    def type(self):
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


class SlashCommandOptionChoice:
    def __init__(self, name: str, value: typing.Union[str, bool, int] = None):
        if 100 < len(name) < 1:
            raise ValueError('The name of a choice must bee between 1 and 100 Characters long, got %s.' % len(name))
        self.name = name
        self.value = value or name

    def __repr__(self):
        return '<SlashCommandOptionChoice name=%s, value=%s>' % (self.name, self.value)

    def to_dict(self):
        base = {
            'name': str(self.name),
            'value': self.value
        }
        return base

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['value'])


class SlashCommandOption:
    __slots__ = ('type', 'name', 'description', 'required', 'choices', 'options')

    def __init__(self, type: typing.Union[OptionType, int], name: str, description: str, required: bool = True, choices: typing.List[SlashCommandOptionChoice] = [], **kwargs):
        self.type = type
        if (not re.match(r'^[\w-]{1,32}$', name)) or 32 < len(name) < 1:
            raise ValueError('The name of the option has to be 1-32 characters long and only contain lowercase a-z, _ and -. Got %s with length %s.' % (name, len(name)))
        self.name = name
        if 100 < len(description) < 1:
            raise ValueError('The description must be between 1 and 100 Characters long, got %s.' % len(description))
        self.description = description
        self.required = required
        if len(choices) > 25:
            raise ValueError('The maximum of choices per Option is 25, got %s' % len(choices))
        self.choices = choices
        options = kwargs.get('options', [])
        if self.type == 2 and (not options):
            raise ValueError('You need to pass options if the type is subcommand_group.')
        self.options = options

    def __repr__(self):
        return '<SlashCommandOption type=%s, name=%s, description=%s, required=%s, choices=%s>' % (self.type, self.name, self.description, self.required, self.choices)

    def to_dict(self):
        base = {
            'type': int(self.type),
            'name': str(self.name),
            'description': str(self.description)
        }
        if bool(self.required) is True:
            base['required'] = bool(self.required)
        if self.choices:
            base['choices'] = [c.to_dict() for c in self.choices]
        elif self.options:
            base['options'] = [o.to_dict() for o in self.options]
        return base

    @classmethod
    def from_dict(cls, data):
        return cls(try_enum(OptionType, data['type']), data['name'], data.get('description', 'No description'), data.get('required', False), choices=[SlashCommandOptionChoice.from_dict(c) for c in data.get('choices', [])])


class SubCommand(SlashCommandOption):
    def __init__(self, parent, name: str, description: str, options: typing.List[SlashCommandOption] = [], **kwargs):
        self.parent = parent
        if (not re.match('^[\w-]{1,32}$', name)) or 32 < len(name) < 1:
            raise ValueError('The name of the Sub-Command must be 1-32 Characters long and only contain lowercase a-z, _ and -. Got %s with length %s.' % (name, len(name)))
        self.name = name
        if 100 < len(description) < 1:
            raise ValueError('The description of the Sub-Command must be 1-100 Characters long, got %s.' % len(description))
        if len(options) > 25:
            raise ValueError('The maximum of options per Sub-Command is 25, got %s.' % len(options))
        self.options = options
        self.func = kwargs.get('func', None)
        self.cog = kwargs.get('cog', None)
        super().__init__(OptionType.sub_command, name=name, description=description, options=options)

    def __repr__(self):
        return '<SubCommand parent=%s, name=%s, description=%s, options=%s>' % (self.parent.name, self.name, self.description, self.options)

    def to_dict(self):
        base = {
            'type': 1,
            'name': str(self.name),
            'description': str(self.description),
            'options': [c.to_dict() for c in self.options]
        }
        return base

    async def can_run(self, *args, **kwargs):
        if self.cog is not None:
            args = (self.cog, *args)
        checks = getattr(self, '__checks__', [])
        if not checks:
            return True

        return await async_all(check(*args, **kwargs) for check in checks)

    async def invoke(self, *args, **kwargs):
        if await self.can_run(*args, **kwargs):
            if self.cog is not None:
                args = (self.cog, *args)
            try:
                await self.func(*args, **kwargs)
            except Exception as exc:
                if hasattr(self, 'on_error'):
                    await self.on_error(exc, *args, **kwargs)
                self.parent.parent._state.dispatch('application_command_error', self, exc)

    def error(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler registered must be a coroutine.')
        self.on_error = coro
        return coro


class SlashCommand(ApplicationCommand):
    def __init__(self, name: str, description: str, default_permission: bool = True, options: typing.List[SlashCommandOption] = [], **kwargs):
        super().__init__(1, **kwargs)
        if (not re.match(r'^[\w-]{1,32}$', name)) or 32 < len(name) < 1:
            raise ValueError('The name of the Slash-Command has to be 1-32 Characters long and only contain lowercase a-z, _ and -. Got %s with length %s.' % (name, len(name)))
        self.name = name
        if 100 < len(description) < 1:
            raise ValueError('The description must be between 1 and 100 Characters long, got %s.' % len(description))
        self.description = description
        self.default_permission = default_permission
        if len(options) > 25:
            raise ValueError('The maximum of options per command is 25, got %s' % len(options))
        self._options = options
        self._sub_commands = {}

    def __repr__(self):
        return '<SlashCommand name=%s, description=%s, default_permission=%s, options=%s, guild_id=%s>' % (self.name, self.description, self.default_permission, self._options or self.subcommands, self.guild_id)

    @property
    def _state(self):
        return getattr(self, '_state_')

    @_state.setter
    def _state(self, value):
        setattr(self, '_state_', value)
        for sc in self._sub_commands.values():
            sc.parent = self

    def subcommand(self, name: str = None, description: str = None, options: typing.List[SlashCommandOption] = []):
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The sub-command must be a coroutine.')
            _name = (name or func.__name__).lower()
            _description = description or inspect.cleandoc(func.__doc__)[:100] or 'No Description'
            if len(options) > 25:
                raise ValueError('The maximum of options per command is 25, got %s' % len(options))
            _options = options or generate_options(func)
            self._sub_commands[_name] = subcommand = SubCommand(self, _name, _description, _options, func=func)
            return subcommand
        return decorator

    def subcommandgroup(self, name: str = None, description: str = None, commands: typing.List[SubCommand] = []):
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The sub-command must be a coroutine.')
            _name = (name or func.__name__).lower()
            _description = description or inspect.cleandoc(func.__doc__)[:100] or 'No Description'
            if len(commands) > 25:
                raise ValueError('The maximum of options per command is 25, got %s' % len(commands))
            _options = commands or generate_options(func)
            self._sub_commands[_name] = subcommand = SubCommandGroup(self, _name, _description, _options, func=func)
            return subcommand
        return decorator

    @property
    def subcommands(self):
        return list(self._sub_commands.values())

    @property
    def options(self):
        return self._options or self.subcommands

    @classmethod
    def from_dict(cls, state, data):
        return cls(data['name'], data.get('description', 'No Description'), data.get('default_permission', True), [SlashCommandOption.from_dict(opt) for opt in data.get('options', [])], state=state, **data)

    @staticmethod
    def _filter_id_out(argument):
        return int(argument.strip('<!@&#>'))

    async def invoke(self, *args, **kwargs):
        if await self.can_run(*args, **kwargs):
            if self.cog is not None:
                args = (self.cog, *args)
            try:
                await self.func(*args, **kwargs)
            except Exception as exc:
                if hasattr(self, 'on_error'):
                    await self.on_error(exc, *args, **kwargs)
                self._state.dispatch('application_command_error', self, exc, *args, **kwargs)

    async def _parse_arguments(self, interaction):
        to_invoke = self
        params = {}
        options = interaction.data.options
        if options[0].type in (OptionType.sub_command_group, OptionType.sub_command):
            if options[0].type == OptionType.sub_command_group:
                command_group: SubCommandGroup = self._sub_commands[options[0].name]
                sub_command: SubCommand = command_group._sub_commands[options[0].options[0].name]
                options = options[0].options[0].options

            else:
                sub_command: SubCommand = self._sub_commands[options[0].name]
                options = options[0].options
            to_invoke = sub_command
        for option in options:
            if option.type in (OptionType.string, OptionType.integer, OptionType.boolean, OptionType.number):
                params[option.name] = option.value
            elif option.type == OptionType.user:
                _id = self._filter_id_out(option.value)
                params[option.name] = interaction.data.resolved.members[_id] or interaction.data.resolved.users[_id] or option.value
            elif option.type == OptionType.role:
                _id = self._filter_id_out(option.value)
                params[option.name] = interaction.data.resolved.roles[_id] or option.value
            elif option.type == OptionType.channel:
                _id = self._filter_id_out(option.value)
                params[option.name] = interaction.data.resolved.channels[_id] or option.value
            elif option.type == OptionType.mentionable:
                _id = self._filter_id_out(option.value)
                if '&' in option.value:
                    params[option.name] = interaction.data.resolved.roles[_id] or option.value
                else:
                    params[option.name] = interaction.data.resolved.members[_id] or interaction.data.resolved.users[_id] or option.value
        return await to_invoke.invoke(interaction, **params)


class GuildOnlySlashCommand(SlashCommand):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return '<GuildOnlySlashCommand name=%s, description=%s, default_permission=%s, options=%s, guild_ids=%s>' % (self.name, self.description, self.default_permission, self.options, self.guild_ids)

    def subcommandgroup(self, name: str = None, description: str = None, commands: typing.List[SubCommand] = [], guild_ids: typing.List[int] = None):
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The sub-command-group registered must be a coroutine.')
            _name = (name or func.__name__).lower()
            _description = description or inspect.cleandoc(func.__doc__)[:100] or 'No Description'
            if len(commands) > 25:
                raise ValueError('The maximum of options per command is 25, got %s' % len(commands))
            _options = commands or generate_options(func)
            _guild_ids = guild_ids or self.guild_ids
            for guild_id in _guild_ids:
                self.client._guild_specific_application_commands[guild_id]['chat_input'][self.name]._sub_commands[_name] = SubCommandGroup(self, _name, _description, _options, func=func)
            self._sub_commands[_name] = subcommand = GuildOnlySubCommandGroup(parent=self, name=_name, description=_description, commands=_options, guild_ids=_guild_ids, func=func)
            return subcommand
        return decorator

    def subcommand(self, name: str = None, description: str = None, options: typing.List[SlashCommandOption] = [], guild_ids: typing.List[int] = None):
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The sub-command registered must be a coroutine.')
            _name = (name or func.__name__).lower()
            _description = description or inspect.cleandoc(func.__doc__)[:100] or 'No Description'
            if len(options) > 25:
                raise ValueError('The maximum of options per command is 25, got %s' % len(options))
            _options = options or generate_options(func)
            _guild_ids = guild_ids or self.guild_ids
            for guild_id in _guild_ids:
                self.client._guild_specific_application_commands[guild_id]['chat_input'][self.name]._sub_commands[_name] = SubCommand(self, _name, _description, _options, func=func)
            self._sub_commands[_name] = subcommand = GuildOnlySubCommand(parent=self, name=_name, description=_description, options=_options, guild_ids=_guild_ids, func=func)
            return subcommand
        return decorator


class UserCommand(ApplicationCommand):
    def __init__(self, name, default_permission: bool = True, **kwargs):
        super().__init__(2, **kwargs)
        if 32 < len(name) < 1:
            raise ValueError('The name of the User-Command has to be 1-32 Characters long, got %s.' % len(name))
        self.name = name
        self.default_permission = default_permission
    
    @classmethod
    def from_dict(cls, state, data):
        return cls(data['name'], data['default_permission'], state=state, **data)

    async def _parse_arguments(self, interaction):
        member = interaction.data.resolved.members[interaction.data.target_id]
        await self.invoke(interaction, member)


class MessageCommand(ApplicationCommand):
    def __init__(self, name: str, default_permission: bool = True, **kwargs):
        super().__init__(3, **kwargs)
        if 32 < len(name) < 1:
            raise ValueError('The name of the Message-Command has to be 1-32 Characters long, got %s.' % len(name))
        self.name = name
        self.default_permission = default_permission

    @classmethod
    def from_dict(cls, state, data):
        return cls(data['name'], data['default_permission'], state=state, **data)

    async def _parse_arguments(self, interaction):
        message = interaction.data.resolved.messages[interaction.data.target_id]
        await self.invoke(interaction, message)


class SubCommandGroup(SlashCommandOption):
    def __init__(self, parent: typing.Union[SlashCommand, GuildOnlySlashCommand], name: str, description: str, commands: typing.List[SubCommand] = [], **kwargs):
        self.parent = parent
        self.cog = parent.cog
        if (not re.match('^[\w-]{1,32}$', name)) or 32 < len(name) < 1:
            raise ValueError('The name of the Sub-Command-Group must be 1-32 Characters long and only contain lowercase a-z, _ and -. Got %s with length %s.' % (name, len(name)))
        self.name = name
        if 100 < len(description) < 1:
            raise ValueError('The description of the Sub-Command-Group must be 1-100 Characters long, got %s.' % len(description))
        if 25 < len(commands) < 1:
            raise ValueError('A Sub-Command-Group needs 1-25 sub-commands, got %s.' % len(commands))
        self._sub_commands = {command.name: command for command in commands}
        self.guild_ids = kwargs.get('guild_ids', parent.guild_ids)
        self.cog = kwargs.get('cog', None)
        self.func = kwargs.get('func', None)
        super().__init__(OptionType.sub_command_group, name=name, description=description, options=commands)

    def __repr__(self):
        return '<SubCommandGroup parent=%s, name=%s, description=%s, commands=%s>' % (self.parent.name, self.name, self.description, self.commands)

    def subcommand(self, name: str = None, description: str = None, options: typing.List[SlashCommandOption] = []):
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The sub-command must be a coroutine.')
            _name = (name or func.__name__).lower()
            _description = description or inspect.cleandoc(func.__doc__)[:100] or 'No Description'
            if len(options) > 25:
                raise ValueError('The maximum of options per command is 25, got %s' % len(options))
            _options = options or generate_options(func)
            self._sub_commands[_name] = subcommand = SubCommand(self, _name, _description, _options, func=func)
            return subcommand
        return decorator

    @property
    def commands(self):
        return list(self._sub_commands.values())

    def to_dict(self):
        base = {
            'type': 2,
            'name': str(self.name),
            'description': str(self.description),
            'options': [c.to_dict() for c in self.commands]
        }
        return base


class GuildOnlySubCommandGroup(SubCommandGroup):
    def __init__(self,  *args, guild_ids: typing.List[int] = None, **kwargs):
        super().__init__(*args, **kwargs, guild_ids=guild_ids)

    def __repr__(self):
        return '<GuildOnlySubCommandGroup parent=%s, name=%s, description=%s, commands=%s, guild_ids=%s>' % (self.parent, self.name, self.description, self.commands, self.guild_ids)

    def subcommand(self, name: str = None, description: str = None, options: typing.List[SlashCommandOption] = [], guild_ids: typing.List[int] = None):
        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The sub-command registered must be a coroutine.')
            _name = (name or func.__name__).lower()
            _description = description or inspect.cleandoc(func.__doc__)[:100] or 'No Description'
            if len(options) > 25:
                raise ValueError('The maximum of options per command is 25, got %s' % len(options))
            _options = options or generate_options(func)
            _guild_ids = guild_ids or self.guild_ids
            for guild_id in _guild_ids:
                self.parent.client._guild_specific_application_commands[guild_id]['chat_input'][self.parent.name]._sub_commands[self.name]._sub_commands[_name] = SubCommand(self, _name, _description, _options, func=func)

            self._sub_commands[_name] = subcommand = GuildOnlySubCommand(parent=self, name=_name, description=_description, options=_options, guild_ids=_guild_ids, func=func)
            return subcommand
        return decorator


class GuildOnlySubCommand(SubCommand):
    def __init__(self, *args, guild_ids: typing.List[int] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.guild_ids = guild_ids or self.parent.guild_ids

    def __repr__(self):
        return '<GuildOnlySubCommand parent=%s, name=%s, description=%s, options=%s, guild_ids=%s>' % (self.parent.name, self.name, self.description, self.options, self.guild_ids)


from typing_extensions import Literal

def generate_options(func: typing.Callable, description: str = 'No Description'):
    options = []
    parameters = inspect.signature(func).parameters.values().__iter__()
    if next(parameters).name in ('self', 'cls'):
        next(parameters)

    for param in parameters:
        required = True
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if param.default is not inspect._empty:
            required = False
        if param.annotation is inspect._empty:
            options.append(SlashCommandOption(OptionType.string, param.name, description, required))
            continue
        elif getattr(param.annotation, '__origin__', None) is typing.Union:
            args = getattr(param.annotation, '__args__', None)
            if args:
                param = param.replace(annotation=args[0])
                required = not isinstance(args[-1], type(None))
        elif getattr(param.annotation, '__origin__', None) is Literal:
            args = getattr(param.annotation, '__args__', None)
            choices = []
            for arg in args:
                if isinstance(arg, (list, tuple)):
                    choices.append(SlashCommandOptionChoice(str(arg[0]), args[1]))
                else:
                    choices.append(SlashCommandOptionChoice(str(arg), arg))
            options.append(SlashCommandOption(OptionType.string, param.name, description, required))
            continue

        _type = OptionType.from_type(param.annotation) or OptionType.string
        options.append(SlashCommandOption(_type, param.name, description, required))

    return options


def message_command(name: str = None, default_permission: bool = True):
    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('The message-command must be a coroutine.')
        _name = name or func.__name__
        cmd = MessageCommand(name=_name, default_permission=default_permission, func=func)
        return cmd
    return decorator
