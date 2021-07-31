import typing
import logging
from . import utils
from .user import User
from .member import Member
from .http import HTTPClient
from .message import Message
from .errors import NotFound
from .channel import DMChannel
from .components import Button, SelectMenu
from .enums import ComponentType, InteractionCallbackType

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
        self._state = state
        self._http: HTTPClient = state.http
        self._interaction_type = data.get('type', None)
        self.__token = data.get('token', None)
        self._message = data.get('message')
        self.message_id = int(self._message.get('id'))
        self.message_flags = self._message.get('flags', 0)
        self._data = data.get('data', None)
        self._member = data.get('member', None)
        self._user = data.get('user', self._member.get('user', None) if self._member else None)
        self.user_id = int(self._user['id'])
        self.__interaction_id = int(data.get('id'))
        self.guild_id = int(data.get('guild_id', 0))
        self._guild = None
        self._channel = None
        self.channel_id = int(data.get('channel_id', 0))
        self.__application_id = int(data.get('application_id'))
        self.message: typing.Union[Message, EphemeralMessage] = EphemeralMessage() if self.message_is_hidden else None
        self.member: typing.Optional[Member] = None
        self.user: typing.Optional[User] = None
        self.deferred = False
        self.deferred_hidden = False
        self.callback_message = None
        self._component = None
        self.component_type = self._data.get('component_type', None)
        # maybe ``later`` this library will also supports Slash-Commands
        # self.command = None

    def __repr__(self):
        """Represents a :class:`discord.Interaction`-object."""
        return f'<Interaction {", ".join(["%s=%s" % (a, getattr(self, a)) for a in self.__slots__ if a[0] != "_"])}>'

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

        if isinstance(response_type, int):
            response_type = InteractionCallbackType.from_value(response_type)
        if response_type not in (InteractionCallbackType.deferred_msg_with_source, InteractionCallbackType.deferred_update_msg):
            raise ValueError('response_type has to bee discord.InteractionCallbackType.deferred_msg_with_source or discord.InteractionCallbackType.deferred_update_msg (e.g. 5 or 6), not %s.__class__.__name__' % response_type)
        if self.deferred:
            return log.warning("\033[91You have already responded to this Interaction!\033[0m")
        base = {"type": response_type.value, "data": {'flags': 64 if hidden else None}}
        try:
            data = await self._http.post_initial_response(_resp=base, use_webhook=False, interaction_id=self.__interaction_id,
                                                          token=self.__token, application_id=self.__application_id)
        except NotFound:
            log.warning(f'Unknown Interaction {self.__interaction_id}')
        else:
            self.deferred = True
            if hidden is True and response_type is InteractionCallbackType.deferred_msg_with_source:
                self.deferred_hidden = True
            return data

    async def edit(self, **fields) -> Message:
        """|coro|

        'Defers' if it isn't yet and edit the message
        """
        if not self.channel:
            self._channel = self._state.add_dm_channel(data=await self._http.get_channel(self.channel_id))
        await self.message.edit(__is_interaction_response=True, __deferred=False if (not self.deferred or self.callback_message) else True, __use_webhook=False,
                                __interaction_id=self.__interaction_id, __interaction_token=self.__token,
                                __application_id=self.__application_id, **fields)
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
                                      __deferred=self.deferred, __use_webhook=False, __interaction_id=self.__interaction_id,
                                      __interaction_token=self.__token, __application_id=self.__application_id,
                                      followup=True if self.callback_message else False)

        if hidden is True:
            self.deferred_hidden = True
        if not self.callback_message and not self.deferred:
            self.callback_message = msg if msg else EphemeralMessage()
        self.deferred = True
        return msg

    async def get_original_callback(self):
        """|coro|

        Fetch the Original Callback-Message of the Interaction

        .. warning::
            This is a API-Call and should use carefully"""
        return await self._state.http.get_original_interaction_response(self.__token, self.__application_id)

    @property
    def created_at(self):
        """
        Returns the Interaction’s creation time in UTC.

        :return: datetime.datetime
        """
        return utils.snowflake_time(self.__interaction_id)

    @property
    def author(self) -> typing.Union[Member, User]:
        return self.member if self.member is not None else self.user

    @property
    def channel(self):
        return self._channel if self._channel else self.message.channel

    @property
    def guild(self):
        return self._guild

    @property
    def message_is_dm(self) -> bool:
        return not self.guild_id

    @property
    def message_is_hidden(self) -> bool:
        return self.message_flags == 64

    @property
    def component(self) -> typing.Union[Button, SelectMenu, ButtonClick, SelectionSelect]:
        if self._component is None:
            custom_id = self._data['custom_id']
            if custom_id.isdigit():
                custom_id = int(custom_id)
            if isinstance(self.message, Message):
                if self._data['component_type'] == ComponentType.Button:
                    self._component = utils.get(self.message.all_buttons, custom_id=custom_id)
                elif self._data['component_type'] == ComponentType.SelectMenu:
                    select_menu = utils.get(self.message.all_select_menus, custom_id=custom_id)
                    setattr(select_menu, '_values', self._data['values'])
                    self._component = select_menu

            else:
                if self._data['component_type'] == ComponentType.Button:
                    self._component = ButtonClick(self._data)
                elif self._data['component_type'] == ComponentType.SelectMenu:
                    self._component = SelectionSelect(self._data)
        return self._component


class InteractionType:
    PingAck = 1
    SlashCommand = 2
    Component = 3
