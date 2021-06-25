import sys
import typing
import warnings
from .user import User
from .member import Member
from .http import HTTPClient
from .message import Message
import logging
from .errors import NotFound, UnknowInteraction
from .channel import TextChannel, DMChannel
from .components import ActionRow, Button, SelectionMenu, ComponentType

log = logging.getLogger(__name__)


class Interaction:

    """
    The Class for an discord-interaction like klick an :class:`Button` or select an option of :class:`SelectionMenu` in discord

    for more informations about Interactions visit the Documentation of the
    `Discord-API <https://discord.com/developers/docs/interactions/slash-commands#interaction-object>`_
    """

    def __repr__(self):
        return f'<Interaction {" ".join([f"{a}={getattr(self, a)}" for a in self.__all__])}>'

    # __slots__ = ('member', 'user', 'message', 'channel', 'guild', '__token', '__interaction_id', '_type', 'interaction_type', 'component_type', 'component', 'http')

    __all__ = ('member', 'user', 'guild', 'channel', 'message', '_deferred', 'component')

    def __init__(self, state, data):
        self.state = state
        self.http: HTTPClient = state.http
        self.interaction_type = data.get('type', None)
        self.__token = data.get('token', None)
        self._raw = data
        self._message = data.get('message')
        self._message_id = int(self._message.get('id'))
        self.message_flags = self._message.get('flags', 0)
        self._data = data.get('data', None)
        self._member = data.get('member', None)
        self._user = data.get('user', self._member.get('user', None) if self._member else None)
        self.__interaction_id = int(data.get('id', 0))
        self._guild_id = int(data.get('guild_id', 0))
        self._channel_id = int(data.get('channel_id', 0))
        self.__application_id = int(data.get('application_id', 0))
        self.guild = None
        self.channel = None
        self.member: Member = None
        self.user: User = None
        self.message: typing.Union[Message, EphemeralMessage] = EphemeralMessage() if self.message_is_hidden else None
        self._deferred = False
        self._deferred_hidden = False
        self.callback_message = None
        self.component: typing.Union[ButtonClick, SelectionSelect] = _component_factory(self._data)
        self.component_type = None
        if self.component:
            self.component_type = self.component.component_type
        # maybe ``later`` this library will alsow supports Slash-Commands
        # self.command = None


    async def defer(self):
        """
        'Defers' the response, showing a loading state to the user
        """
        if self._deferred:
            return log.warning("\033[91You have already responded to this Interaction!\033[0m")
        base = {"type": 6}
        try:
            await self.http.post_initial_response(_resp=base, use_webhook=False, interaction_id=self.__interaction_id, token=self.__token, application_id=self.__application_id)
        except NotFound:
            log.warn(f'Unknow Interaction {self.__interaction_id}')
        self._deferred = True

    async def edit(self, **fields):
        """
        'Defers' if it isn't yet and edit the message
        """
        if not self.channel:
            self.channel = self.state.add_dm_channel(data=await self.http.get_channel(self.channel_id))
        if not self.message:
            self.message: Message = await self.channel.fetch_message(self._message_id)
        await self.message.edit(__is_interaction_responce=True, __deferred=self._deferred, __use_webhook=False, __interaction_id=self.__interaction_id, __interaction_token=self.__token, __application_id=self.__application_id, **fields)
        self._deferred = True
        return self.message

    async def respond(self, content=None, *, tts=False, embed=None, embeds=None, components=None, file=None,
                                          files=None, delete_after=None, nonce=None,
                                          allowed_mentions=None, reference=None,
                                          mention_author=None, hidden=False):
        """Responds to an interaction by sending a message that can be made visible only to the person who performed the
         interaction by setting the `hidden` parameter to :bool:`True`."""
        if not self.channel:
            self.channel = self.state.add_dm_channel(data=await self.http.get_channel(self.channel_id))
        msg = await self.channel.send(content, tts=tts, embed=embed, embeds=embeds, components=components, file=file,
                                       files=files, delete_after=delete_after, nonce=nonce,allowed_mentions=allowed_mentions,
                                       reference=reference, mention_author=mention_author, hidden=hidden,
                                       __is_interaction_responce=True, __deferred=self._deferred or self._deferred_hidden, __use_webhook=False,
                                       __interaction_id=self.__interaction_id, __interaction_token=self.__token,
                                       __application_id=self.__application_id, followup=True if self._deferred or self._deferred_hidden else False)

        self._deffered = True
        if hidden is True:
            self._deferred_hidden = True
        if not self.callback_message:
            self.callback_message = msg if msg else EphemeralMessage()
        return msg if msg else self.callback_message

    @property
    def message_is_dm(self):
        if self.message:
            return isinstance(self.channel, DMChannel)

    @property
    def deferred(self):
        return self._deferred

    @property
    def token(self):
        return self.__token

    @property
    def initeraction_id(self):
        return int(self.__interaction_id)

    @property
    def guild_id(self):
        if self._guild_id:
            return int(self._guild_id)

    @property
    def channel_id(self):
        return int(self._channel_id)

    @property
    def message_id(self):
        if self._message_id:
            return int(self._message_id)


    @property
    def message_is_hidden(self):
        return self.message_flags == 64

class ButtonClick:
    def __init__(self, data):
        self.component_type = data.get('component_type')
        self.custom_id = data.get('custom_id', None)
        self.__hash__ = data.get('hash', None)

    def __hash__(self):
        return self.__hash__

    def __repr__(self):
        return f"<ButtonClick custom_id={self.custom_id}>"


class SelectionSelect:
    def __init__(self, data):
        self.component_type = data.get('component_type')
        self.custom_id = data.get('custom_id', None)
        self.value = data.get('value')


    def __repr__(self):
        return f'<SelectionSelect custom_id={self.custom_id} value={self.value}>'


def _component_factory(data):
    if data['component_type'] == ComponentType.Button:
        return ButtonClick(data)

    elif data['component_type'] == ComponentType.SlectionMenu:
        return SelectionSelect(data)

    else:
        return None


class InteractionType:
    PingAck = 1
    SlashCommand = 2
    Component = 3
    ChannelMessageWithSource = 4
    DeferredChannelMessageWithSource = 5
    DeferredUpdateMessage = 6
    UpdateMessage = 7


class EphemeralMessage:

    """
    Since Discord doesn't return anything when we send a ephemeral message,
    this class has no attributes and you can't do anything with it.
    """