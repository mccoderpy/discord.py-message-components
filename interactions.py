import typing
import logging
from . import utils
from .role import Role
from .user import User
from .member import Member
from .http import HTTPClient
from .message import Message
from .errors import NotFound, UnknowInteraction
from .channel import DMChannel, _channel_factory
from .embeds import Embed
from .components import Button, SelectMenu, ActionRow
from .application_commands import OptionType
from .enums import InteractionType, ApplicationCommandType, ComponentType, InteractionCallbackType

log = logging.getLogger(__name__)

__all__ = ('EphemeralMessage',
           'Interaction',
           'ButtonClick',
           'SelectionSelect')


class EphemeralMessage:

    """
    Since Discord doesn't return anything when we send a ephemeral message,
    this class has no attributes and you can't do anything with it.
    """

    def __init__(self, interaction, data):
        self._state = interaction._state
        self._interaction = interaction
        self.application_id = interaction._application_id
        self.interaction_id = interaction.id
        self.token = interaction._token


    async def edit(self, **fields):
        content: str = fields.pop('content', None)
        if content:
            fields['content'] = str(content)
        embeds: typing.Optional[typing.Union[typing.List[Embed], Embed]] = fields.pop('embed', fields.pop('embeds', None))
        if embeds is not None and not isinstance(embeds, list):
            embeds = [embeds]
        if embeds is not None:
            fields['embeds'] = [e.to_dict() for e in embeds]
        components: typing.Optional[typing.List[typing.Union[typing.List[Button, SelectMenu], ActionRow, Button, SelectMenu]]] = fields.pop('components', None)
        _components = []
        if components is not None and not isinstance(components, list):
            components = [components]
        if components is not None:
            for index, component in enumerate(components):
                if isinstance(component, (SelectMenu, Button)):
                    components[index] = ActionRow(component)
                elif isinstance(component, list):
                    components[index] = ActionRow(*component)
            [_components.extend(*[c.to_dict()]) for c in components]
            fields['components'] = _components
        try:
            await self._state.http.edit_interaction_response(interaction_id=self.interaction_id, token=self.token, application_id=self.application_id, deferred=self._interaction.deferred, use_webhook=True, files=None, **fields)
        except NotFound as exc:
            log.warning('Unknown Interaction')
        else:
            if not self._interaction.callback_message:
                self._interaction.callback_message = self
        return self




class ButtonClick:
    """Represents a :class:`discord.Button` that was pressed in an ephemeral Message(contains its custom_id and its hash)."""
    def __init__(self, data):
        self.component_type: int = data.get('component_type')
        custom_id = data.get('custom_id')
        self.custom_id: typing.Union[str, int] = int(custom_id) if custom_id.isdigit() else custom_id
        self.__hash__: str = data.get('hash', None)

    def __hash__(self):
        return self.__hash__

    def __repr__(self):
        return f"<ButtonClick custom_id={self.custom_id}{', hash='+self.__hash__ if self.__hash__ else ''}>"


class SelectionSelect:
    """Represents a :class:`discord.SelectMenu` in an ephemeral Message from which options have been selected (contains its custom_id and the selected options)."""
    def __init__(self, data):
        self.component_type: int = data.get('component_type')
        custom_id = data.get('custom_id')
        self.custom_id: typing.Union[str, int] = int(custom_id) if custom_id.isdigit() else custom_id
        self.values: typing.List[typing.Union[str, int]] = [int(value) if value.isdigit() else value for value in data.get('values', [])]

    def __repr__(self):
        return f'<SelectionSelect custom_id={self.custom_id}, values={self.values}>'


class Interaction:

    """
    The Class for an discord-interaction like klick an :class:`Button` or select an option of :class:`SelectMenu` in discord

    For more general information's about Interactions visit the Documentation of the
    `Discord-API <https://discord.com/developers/docs/interactions/slash-commands#interaction-object>`_
    """

    def __init__(self, state, data):
        self._data = data
        self._state = state
        self._http: HTTPClient = state.http
        self.type = InteractionType.try_value(data['type'])
        self._application_id = int(data.get('application_id'))
        self.id = int(data.get('id'))
        self._token = data.get('token', None)
        self.interaction_type = data.get('type', None)
        self._message_data = data.get('message', {})
        self.message_id = int(self._message_data.get('id', 0))
        self.message_flags = self._message_data.get('flags', 0)
        self.guild_id = int(data.get('guild_id', 0))
        self.channel_id = int(data.get('channel_id', 0))
        self.data = InteractionData(data=data.get('data', None), state=state, guild=self.guild, channel_id=self.channel_id)
        self._member = data.get('member', None)
        self._user = data.get('user', self._member.get('user', None) if self._member else None)
        self.user_id = int(self._user['id'])
        self._guild = None
        self._channel = None
        self._message: typing.Union[Message, EphemeralMessage] = None
        self.member: typing.Optional[Member] = None
        self.user: typing.Optional[User] = None
        self.deferred = False
        self.deferred_hidden = False
        self.callback_message = None
        self._command = None
        self._component = None


    def __repr__(self):
        """Represents a :class:`discord.Interaction`-object."""
        return f'<Interaction {", ".join(["%s=%s" % (k, v) for k, v in self.__dict__.items() if k[0] != "_"])}>'

    async def defer(self, response_type: typing.Literal[5, 6] = InteractionCallbackType.deferred_update_msg, hidden: bool = False) -> None:
        """
        |coro|

        'Defers' the response.

        If :attr:`response_type` is `InteractionCallbackType.deferred_msg_with_source` it shows a loading state to the user.

        :param response_type: Optional[typing.Literal[5, 6]]
            The type to response with, aiter :class:`InteractionCallbackType.deferred_msg_with_source` or :class:`InteractionCallbackType.deferred_update_msg` (e.g. 5 or 6)

        :param hidden: Optional[bool]
            Whether to defer ephemerally(only the :attr:`author` of the interaction can see the message)

            .. note::
                Only for :class:`InteractionCallbackType.deferred_msg_with_source`.

        .. important::
            If you doesn't respond with an message using :meth:`respond`
            or edit the original message using :meth:`edit` within less than 3 seconds,
            discord will indicates that the interaction failed and the interaction-token will be invalidated.
            To provide this us this method

        .. note::
            A Token will be Valid for 15 Minutes so you could edit the original :attr:`message` with :meth:`edit`, :meth:`respond` or doing anything other with this interaction for 15 minutes.
            after that time you have to edit the original message with the Methode :meth:`edit` of the :attr:`message` and sending new messages with the :meth:`send` Methode of :attr:`channel`
            (you could not do this hidden as it isn't an respond anymore).
        """
        if self.type == InteractionType.ApplicationCommand and not response_type:
            response_type = 5
        if isinstance(response_type, int):
            response_type = InteractionCallbackType.from_value(response_type)
        if response_type not in (InteractionCallbackType.deferred_msg_with_source, InteractionCallbackType.deferred_update_msg):
            raise ValueError('response_type has to bee discord.InteractionCallbackType.deferred_msg_with_source or discord.InteractionCallbackType.deferred_update_msg (e.g. 5 or 6), not %s.__class__.__name__' % response_type)
        if self.deferred:
            return log.warning("\033[91You have already responded to this Interaction!\033[0m")
        base = {"type": int(response_type), "data": {'flags': 64 if hidden else None}}
        try:
            data = await self._http.post_initial_response(_resp=base, use_webhook=False, interaction_id=self.id,
                                                          token=self._token, application_id=self._application_id)
        except NotFound:
            log.warning(f'Unknown Interaction {self.id}')
        else:
            self.deferred = True
            if hidden is True and response_type is InteractionCallbackType.deferred_msg_with_source:
                self.deferred_hidden = True
            return data

    async def edit(self, **fields) -> typing.Union[Message, EphemeralMessage, None]:
        """|coro|

        'Defers' if it isn't yet and edit the message
        """
        if self.message_is_hidden:
            return await self.message.edit(**fields)
        if not self.channel:
            self._channel = self._state.add_dm_channel(data=await self._http.get_channel(self.channel_id))
        await self.message.edit(__is_interaction_response=True, __deferred=False if (not self.deferred or self.callback_message) else True, __use_webhook=False,
                                __interaction_id=self.id, __interaction_token=self._token,
                                __application_id=self._application_id, **fields)
        self.deferred = True
        return self.message

    async def respond(self, content=None, *, tts=False, embed=None, embeds=None, components=None, file=None,
                      files=None, delete_after=None, nonce=None,
                      allowed_mentions=None, reference=None,
                      mention_author=None, hidden=False) -> typing.Union[Message, EphemeralMessage]:
        """|coro|

        Responds to an interaction by sending a message that can be made visible only to the person who performed the
         interaction by setting the `hidden` parameter to :bool:`True`.
        """
        if not self.channel:
            self._channel = self._state.add_dm_channel(data=await self._http.get_channel(self.channel_id))
        msg = await self.channel.send(content, tts=tts, embed=embed, embeds=embeds, components=components, file=file,
                                      files=files, delete_after=delete_after, nonce=nonce,
                                      allowed_mentions=allowed_mentions, reference=reference,
                                      mention_author=mention_author, hidden=hidden, __is_interaction_response=True,
                                      __deferred=self.deferred, __use_webhook=False, __interaction_id=self.id,
                                      __interaction_token=self._token, __application_id=self._application_id,
                                      followup=True if self.callback_message else False)

        if hidden is True:
            self.deferred_hidden = True
        if not self.callback_message and not self.deferred:
            self.callback_message = msg if msg else EphemeralMessage(self, msg)
        self.deferred = True
        return msg

    async def get_original_callback(self):
        """|coro|

        Fetch the Original Callback-Message of the Interaction

        .. warning::
            This is a API-Call and should use carefully"""
        return await self._state.http.get_original_interaction_response(self._token, self._application_id)

    @property
    def created_at(self):
        """
        Returns the Interaction’s creation time in UTC.

        :return: datetime.datetime
        """
        return utils.snowflake_time(self.id)

    @property
    def author(self) -> typing.Union[Member, User]:
        return self.member if self.member is not None else self.user

    @property
    def channel(self):
        return self._channel if self._channel else self.message.channel

    @property
    def guild(self):
        return self._state._get_guild(self.guild_id)

    @property
    def message(self) -> typing.Union[Message, EphemeralMessage]:
        if not self._message:
            if self.message_is_hidden:
                self._message = EphemeralMessage(self)
        return self._message

    @property
    def message_is_dm(self) -> bool:
        return not self.guild_id

    @property
    def message_is_hidden(self) -> bool:
        return self.message_flags == 64

    @property
    def component(self) -> typing.Union[Button, SelectMenu, ButtonClick, SelectionSelect, None]:
        if self._component is None:
            custom_id = self.data.custom_id
            if custom_id:
                if custom_id.isdigit():
                    custom_id = int(custom_id)
                if isinstance(self.message, Message):
                    if self.data.component_type == ComponentType.Button:
                        self._component = utils.get(self.message.all_buttons, custom_id=custom_id)
                    elif self.data.component_type == ComponentType.SelectMenu:
                        select_menu = utils.get(self.message.all_select_menus, custom_id=custom_id)
                        if select_menu:
                            setattr(select_menu, '_values', self.data.values)
                        self._component = select_menu

                else:
                    if self.data.component_type == ComponentType.Button:
                        self._component = ButtonClick(self._data)
                    elif self.data.component_type == ComponentType.SelectMenu:
                        self._component = SelectionSelect(self._data)
            return self._component

    @property
    def command(self):
        return self.data.name if self.interaction_type == InteractionType.ApplicationCommand else None

class InteractionData:
    def __init__(self, *, state, data, guild=None, **kwargs):
        self._data = data
        self._state = state
        self._guild=guild
        self._channel_id = kwargs.pop('channel_id', None)
        resolved = data.get('resolved', None)
        if resolved:
            self.resolved = ResolvedData(state=state, data=resolved, guild=guild, channel_id=self._channel_id)
        options = self._data.get('options', None)
        if options:
            self.options = [InteractionDataOption(state=state, data=option, guild=guild) for option in options]

    def __getitem__(self, item):
        return getattr(self, item, NotImplemented)

    def __getattr__(self, item):
        pass

    @property
    def name(self):
        return self._data.get('name', None)

    @property
    def id(self):
        return int(self._data.get('id', 0))

    @property
    def type(self):
        return InteractionType.try_value(self._data.get('type', None))

    @property
    def component_type(self):
        return self._data.get('component_type', None)

    @property
    def custom_id(self):
        return self._data.get('custom_id', None)

    @property
    def target_id(self):
        return int(self._data.get('target_id', 0))

    @property
    def values(self):
        return self._data.get('values', [])


class InteractionDataOption:
    def __init__(self, *, state, data, guild=None, **kwargs):
        self._state = state
        self._guild = guild
        self._data =data
        self._channel_id = kwargs.pop('channel_id', None)
        self.name = data['name']
        self.type = OptionType.try_value(data['type'])

    @property
    def value(self):
        return self._data.get('value', None)

    @property
    def options(self):
        options = self._data.get('options', [])
        return [InteractionDataOption(state=self._state, data=option, guild=self._guild) for option in options]


class ResolvedData:
    def __init__(self, *, state, data, guild=None, **kwargs):
        self._state = state
        self._data = data
        self._guild = guild
        self._channel_id = kwargs.pop('channel_id', None)
    
    @property
    def users(self):
        _users = {}
        for _id, u in self._data.get('users', {}).items():
            _users[int(_id)] = User(state=self._state, data=u)
        return _users

    @property
    def members(self):
        _members = {}
        for _id, m in self._data.get('members', {}).items():
            m['user'] = self._data['users'][_id]
            _members[int(_id)] = Member(state=self._state, data=m, guild=self._guild)
        return _members

    @property
    def channels(self):
        _channels = {}
        for _id, c in self._data.get('channels', {}).items():
            channel = self._state.get_channel(int(_id))
            if not channel:
                factory, _ch_type_ = _channel_factory(c['type'])
                channel = factory(guild=self._guild, data=c, state=self._state)
            _channels[int(_id)] = channel
        return _channels
    
    @property
    def roles(self):
        _roles = {}
        for _id, r in self._data.get('roles', {}).items():
             _roles[int(_id)] = Role(guild=self._guild, data=r, state=self._state)
        return _roles
            
    @property
    def messages(self):
        _messages = {}
        for _id, m in self._data.get('messages', {}).items():
            _messages[int(_id)] = Message(state=self._state, channel=self._state.get_channel(self._channel_id), data=m)
        return _messages
