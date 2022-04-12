import logging
import warnings

from . import abc

from . import utils
from .role import Role
from .user import User
from .file import File
from .guild import Guild
from .embeds import Embed
from .member import Member
from .http import HTTPClient
from .reaction import Reaction
from .flags import MessageFlags
from .mentions import AllowedMentions
from typing_extensions import Literal
from .message import Message, Attachment
from .application_commands import OptionType, SlashCommandOptionChoice
from typing import (Union,
                    List,
                    Optional,
                    Dict,
                    Any,
                    TYPE_CHECKING)
from .components import Button, SelectMenu, ActionRow
from .channel import DMChannel, ThreadChannel, _channel_factory, TextChannel, PartialMessageable
from .errors import NotFound, InvalidArgument
from .enums import InteractionType, ApplicationCommandType, ComponentType, InteractionCallbackType, Locale, MessageType,\
    try_enum

if TYPE_CHECKING:
    from .application_commands import SlashCommand, MessageCommand, UserCommand

log = logging.getLogger(__name__)

__all__ = (
    'EphemeralMessage',
    'BaseInteraction',
    'ApplicationCommandInteraction',
    'ComponentInteraction',
    'AutocompleteInteraction',
    'option_str',
    'option_float',
    'option_int'
)


class EphemeralMessage:
    """
    Since Discord doesn't return anything when we send a ephemeral message,
    this class has no attributes and you can't do anything with it.
    """

    def __init__(self, *, state, channel, data, interaction):
        self._state = state
        self.__interaction__ = interaction
        self.id = int(data.get('id', 0))
        self.webhook_id = utils._get_as_snowflake(data, 'webhook_id')
        self.reactions = [Reaction(message=self, data=d) for d in data.get('reactions', [])]
        self.attachments = [Attachment(data=a, state=self._state) for a in data.get('attachments', [])]
        self.embeds = [Embed.from_dict(a) for a in data.get('embeds', [])]
        self.components = [ActionRow.from_dict(d) for d in data.get('components', [])]
        self.application = data.get('application')
        self.activity = data.get('activity')
        self.channel = channel
        self._edited_timestamp = utils.parse_time(data['edited_timestamp'])
        self.type = try_enum(MessageType, data['type'])
        self._thread = data.get('thread', None)
        self.pinned = data['pinned']
        self.flags = MessageFlags._from_value(data.get('flags', 0))
        self.mention_everyone = data['mention_everyone']
        self.tts = data['tts']
        self.content = data['content']

        for handler in ('author', 'member', 'mentions', 'mention_roles', 'flags', 'interaction', 'thread'):
            try:
                getattr(self, '_handle_%s' % handler)(data[handler])
            except KeyError:
                continue

    def _handle_flags(self, value):
        self.flags = MessageFlags._from_value(value)

    def _handle_application(self, value):
        self.application = value

    def _handle_activity(self, value):
        self.activity = value

    def _handle_mention_everyone(self, value):
        self.mention_everyone = value

    def _handle_tts(self, value):
        self.tts = value

    def _handle_type(self, value):
        self.type = try_enum(MessageType, value)

    def _handle_content(self, value):
        self.content = value

    def _handle_attachments(self, value):
        self.attachments = [Attachment(data=a, state=self._state) for a in value]

    def _handle_embeds(self, value):
        self.embeds = [Embed.from_dict(data) for data in value]

    def _handle_interaction(self, value):
        pass

    def _handle_thread(self, value):
        thread = self.channel.get_thread(self.id)
        if thread:
            thread._update(value)
        else:
            thread = ThreadChannel(state=self._state, guild=self.channel.guild, data=value)
            self.channel.guild._add_thread(thread)

    def _handle_components(self, value):
        self.components = [ActionRow.from_dict(data) for data in value]

    def _handle_nonce(self, value):
        self.nonce = value

    def _handle_author(self, author):
        self.author = self._state.store_user(author)
        if isinstance(self.guild, Guild):
            found = self.guild.get_member(self.author.id)
            if found is not None:
                self.author = found

    def _handle_member(self, member):
        # The gateway now gives us full Member objects sometimes with the following keys
        # deaf, mute, joined_at, roles
        # For the sake of performance I'm going to assume that the only
        # field that needs *updating* would be the joined_at field.
        # If there is no Member object (for some strange reason), then we can upgrade
        # ourselves to a more "partial" member object.
        author = self.author
        try:
            # Update member reference
            author._update_from_message(member)
        except AttributeError:
            # It's a user here
            # TODO: consider adding to cache here
            self.author = Member._from_message(message=self, data=member)

    def _handle_mentions(self, mentions):
        self.mentions = r = []
        guild = self.guild
        state = self._state
        if not isinstance(guild, Guild):
            self.mentions = [state.store_user(m) for m in mentions]
            return

        for mention in filter(None, mentions):
            id_search = int(mention['id'])
            member = guild.get_member(id_search)
            if member is not None:
                r.append(member)
            else:
                r.append(Member._try_upgrade(data=mention, guild=guild, state=state))

    def _handle_mention_roles(self, role_mentions):
        self.role_mentions = []
        if isinstance(self.guild, Guild):
            for role_id in map(int, role_mentions):
                role = self.guild.get_role(role_id)
                if role is not None:
                    self.role_mentions.append(role)

    @utils.cached_slot_property('_cs_guild')
    def guild(self):
        """Optional[:class:`Guild`]: The guild that the message belongs to, if applicable."""
        return getattr(self.channel, 'guild', None)

    def __repr__(self):
        return '<EphemeralMessage id={0.id} channel={0.channel!r} type={0.type!r} author={0.author!r} flags={0.flags!r}>'.format(self)

    def __eq__(self, other):
        return isinstance(other.__class__, self.__class__) and self.id == other.id

    @property
    def all_components(self):
        """Returns all :class:`Button`'s and :class:`SelectMenu`'s that are contained in the message"""
        for action_row in self.components:
            for component in action_row:
                yield component

    @property
    def all_buttons(self):
        """Returns all :class:`Button`'s that are contained in the message"""
        for action_row in self.components:
            for component in action_row:
                yield component

    @property
    def all_select_menus(self):
        """Returns all :class:`SelectMenu`'s that are contained in the message"""
        for action_row in self.components:
            for component in action_row:
                if isinstance(component, SelectMenu):
                    yield component

    async def edit(self, **fields):
        content: str = fields.pop('content', None)
        if content:
            fields['content'] = str(content)
        embeds: Optional[Union[List[Embed], Embed]] = fields.pop('embed', fields.pop('embeds', None))
        if embeds is not None and not isinstance(embeds, list):
            embeds = [embeds]
        if embeds is not None:
            fields['embeds'] = [e.to_dict() for e in embeds]
        components: Optional[List[Union[List[Button, SelectMenu], ActionRow, Button, SelectMenu]]] = fields.pop('components', None)
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
            await self._state.http.edit_interaction_response(interaction_id=self.__interaction__.id, token=self.__interaction__._token, application_id=self.__interaction__._application_id, deferred=self.__interaction__.deferred, use_webhook=True, files=None, data=fields)
        except NotFound:
            log.warning('Unknown Interaction')
        else:
            if not self.__interaction__.callback_message:
                self.__interaction__.callback_message = self
        return self


class BaseInteraction:

    """
    The Class for an discord-interaction like klick a :class:`Button` or select an option of :class:`SelectMenu` in discord

    For more general information's about Interactions visit the Documentation of the
    `Discord-API <https://discord.com/developers/docs/interactions/slash-commands#interaction-object>`_
    """

    def __init__(self, state, data):
        self._data = data
        self._state = state
        self._http: HTTPClient = state.http
        self.type: InteractionType = InteractionType.try_value(data['type'])
        self._application_id = int(data.get('application_id'))
        self.id = int(data['id'])
        self._token = data['token']
        self.guild_id = int(data.get('guild_id', 0))
        self.channel_id = int(data.get('channel_id', 0))
        message_data = data.get('message', {})
        if message_data:
            self.message = Message(state=state, channel=self.channel, data=message_data)
            self.cached_message = self.message and self._state._get_message(self.message.id)
            self.message_id = self.message.id
        self.data = InteractionData(data=data.get('data', None), state=state, guild=self.guild, channel_id=self.channel_id)
        self._member = data.get('member', None)
        self._user = data.get('user', self._member.get('user', None) if self._member else None)
        self.user_id = int(self._user['id'])
        self.author_locale: Locale = try_enum(Locale, data.get('locale', None))
        self.guild_locale: Locale = try_enum(Locale, data.get('guild_locale', None))
        self._message: Optional[Message, EphemeralMessage] = None
        self.member: Optional[Member] = None
        self.user: Optional[User] = None
        self.deferred = False
        self.deferred_hidden = False
        self.callback_message: Optional[Message] = None
        self._command = None
        self._component = None


    def __repr__(self):
        """Represents a :class:`discord.B aseInteraction`-object."""
        return f'<{self.__class__.__name__} {", ".join(["%s=%s" % (k, v) for k, v in self.__dict__.items() if k[0] != "_"])}>'
    
    async def defer(self,
                    response_type: Optional[InteractionCallbackType] = InteractionCallbackType.deferred_update_msg,
                    hidden: Optional[bool] = False) -> Optional[Message]:
        """
        |coro|

        'Defers' the response.

        If :attr:`response_type` is `InteractionCallbackType.deferred_msg_with_source` it shows a loading state to the user.

        :param response_type: Optional[:class:`InteractionCallbackType`]
            The type to response with, aiter :class:`InteractionCallbackType.deferred_msg_with_source` or :class:`InteractionCallbackType.deferred_update_msg` (e.g. 5 or 6)

        :param hidden: Optional[:class:`bool`]
            Whether to defer ephemerally(only the :attr:`author` of the interaction can see the message)

            .. note::
                Only for :class:`InteractionCallbackType.deferred_msg_with_source`.

        .. important::
            If you doesn't respond with an message using :meth:`respond`
            or edit the original message using :meth:`edit` within less than 3 seconds,
            discord will indicates that the interaction failed and the interaction-token will be invalidated.
            To provide this us this method

        .. note::
            A Token will be Valid for 15 Minutes so you could edit the original :attr:`message` with :meth:`edit`,
             :meth:`respond` or doing anything other with this interaction for 15 minutes.
            After that time you have to edit the original message with the Methode :meth:`edit` of the :attr:`message`
             and send new messages with the :meth:`send` Methode of :attr:`channel`
            (you could not do this hidden as it isn't a response anymore).
        """
        if self.deferred:
            return warnings.warn("\033[91You have already responded to this Interaction!\033[0m")
        base = {"type": int(response_type), "data": {'flags': 64 if hidden else None}}
        try:
            data = await self._http.post_initial_response(_resp=base,
                                                          use_webhook=False,
                                                          interaction_id=self.id,
                                                          token=self._token,
                                                          application_id=self._application_id)
        except NotFound:
            log.warning(f'Unknown Interaction {self.id}')
        else:
            self.deferred = True
            if hidden is True and response_type is InteractionCallbackType.deferred_msg_with_source:
                self.deferred_hidden = True
            if not data and response_type.msg_with_source or response_type.deferred_msg_with_source:
                msg = self.callback_message = await self.get_original_callback()
                return msg

    async def edit(self,
                   content: Optional[str] = None,
                   embed: Optional[Embed] = None,
                   embeds: Optional[List[Embed]] = None,
                   components: Optional[List[Union[ActionRow, List[Union[Button, SelectMenu]]]]] = None,
                   delete_after: Optional[float] = None,
                   suppress: bool = False,
                   **fields
                   ) -> Union[Message, EphemeralMessage, None]:
        """|coro|

        'Defers' if it isn't yet and edit the message
        """
        try:
            content: Optional[str] = fields['content']
        except KeyError:
            pass
        else:
            if content is not None:
                fields['content'] = str(content)

        try:
            embeds: Optional[List[Embed]] = fields['embeds']
        except KeyError:
            pass
        else:
            if embeds is not None:
                fields['embeds'] = [e.to_dict() for e in embeds]

        try:
            embed: Optional[Embed] = fields.pop('embed')
        except KeyError:
            pass
        else:
            if embed is not None:
                embeds = list(reversed(fields.pop('embeds', [])))
                embeds.append(embed.to_dict())
                fields['embeds'] = list(reversed(embeds))
            else:
                fields['embeds'] = None

        if fields.get('embeds', None) and len(fields['embeds']) > 10:
            raise InvalidArgument(f'The maximum number of embeds that can be send with a message is 10, '
                                  f'got: {len(fields["embeds"])}')

        try:
           components: Optional[List[Union[ActionRow, List[Union[Button, SelectMenu]]]]] = fields['components']
        except KeyError:
            pass
        else:
            if components is not None:
                c_list = []
                for i, component in enumerate(list(components) if not isinstance(components, list) else components):
                    if isinstance(component, ActionRow):
                       c_list.extend(component.to_dict())
                    elif isinstance(component, list):
                        c_list.extend(ActionRow(*[obj for obj in component if isinstance(obj, (Button, SelectMenu))]).to_dict())
                    elif isinstance(component, (Button, SelectMenu)):
                        c_list.extend(ActionRow(component).to_dict())
                fields['components'] = c_list
        flags = MessageFlags._from_value(self.message.flags)
        if suppress:
            flags.suppress_embeds = True
        if flags:
            fields['flags'] = flags.value
        state = self._state
        if self.message_is_hidden:
            return await self.message.edit(content=content, embed=embed, embeds=embeds, components=components, suppress=suppress)
        if not self.channel:
            self.channel = self._state.add_dm_channel(data=await self._http.get_channel(self.channel_id))

        if self.deferred:
            data = await state.http.edit_interaction_response(token=self._token, interaction_id=self.id,
                                                              application_id=self._application_id, data=fields,
                                                              deferred=self.deferred)
        else:
            data = await state.http.send_interaction_response(token=self._token, interaction_id=self.id,
                                                              application_id=self._application_id, data=fields,
                                                              deferred=self.deferred,
                                                              followup=True if (self.callback_message and not
                                                                                self.callback_message.flags.loading)
                                                              else False,
                                                              use_webhook=False)

        if not isinstance(data, dict):
            self._message = msg = await self.get_original_callback()
        else:
            if self.message:
                msg = self.message._update(data)
            else:
                msg = self._message = Message(state=state, channel=self.channel, data=data)
        if not self.callback_message:
            self.callback_message = msg
        if isinstance(msg, Message) and delete_after is not None:
            await msg.delete(delay=delete_after)
        if not self.callback_message:
            self.callback_message = msg
        self.deferred = True
        return msg

    async def respond(self,
                      content: str = None, *,
                      tts: bool = False,
                      embed: Optional[Embed] = None,
                      embeds: Optional[List[Embed]] = None,
                      components: Optional[List[Union[ActionRow, List[Union[Button, SelectMenu]]]]] = None,
                      file: Optional[File] = None,
                      files: Optional[List[File]] = None,
                      delete_after: Optional[float] = None,
                      allowed_mentions: Optional[AllowedMentions] = None,
                      mention_author: bool = None,
                      suppress: bool = False,
                      hidden: bool = False
                      ) -> Union[Message, EphemeralMessage]:
        """|coro|

        Responds to an interaction by sending a message that can be made visible only to the person who performed the
         interaction by setting the `hidden` parameter to :bool:`True`.
        """
        state = self._state
        if not self.channel:
            self.channel = self._state.add_dm_channel(data=await self._http.get_channel(self.channel_id))

        data = {'tts': tts}
        if content:
            data['content'] = str(content)

        embed_list = []
        if embed is not None:
            embed_list.append(embed.to_dict())
        if embeds is not None:
            embed_list.extend([e.to_dict() for e in embeds])
        if len(embed_list) > 10:
            raise InvalidArgument(f'The maximum number of embeds that can be send with a message is 10, got: {len(embed_list)}')
        if embed_list:
            data['embeds'] = embed_list

        if components:
            _components = []
            for component in ([components] if not isinstance(components, list) else components):
                if isinstance(component, (Button, SelectMenu)):
                    _components.extend(ActionRow(component).to_dict())
                elif isinstance(component, ActionRow):
                    _components.extend(component.to_dict())
                elif isinstance(component, list):
                    _components.extend(ActionRow(*[obj for obj in component if isinstance(obj, (Button, SelectMenu))]).to_dict())
            if _components:
                data['components'] = _components

        if allowed_mentions is not None:
            if state.allowed_mentions is not None:
                allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
            else:
                allowed_mentions = allowed_mentions.to_dict()
        else:
            allowed_mentions = state.allowed_mentions and state.allowed_mentions.to_dict()


        if mention_author is not None:
            allowed_mentions = allowed_mentions or AllowedMentions().to_dict()
            allowed_mentions['replied_user'] = bool(mention_author)

        if allowed_mentions:
            data['allowed_mentions'] = allowed_mentions

        file_list = []
        if file:
            file_list.append(file)
        if files:
            file_list.extend(files)
        files = file_list
        if len(files) > 10:
            raise InvalidArgument(f'The maximum number of files that can be send with a message is 10, got: {len(files)}')

        flags = MessageFlags._from_value(0)
        if hidden:
            flags.ephemeral = True
        if suppress:
            flags.suppress_embeds = True
        if flags:
            data['flags'] = flags.value
        if self.deferred and not self.callback_message:
            method = state.http.edit_interaction_response(token=self._token, interaction_id=self.id,
                                                          application_id=self._application_id,
                                                          data=data, files=files, deferred=self.deferred)
        else:
            method = state.http.send_interaction_response(token=self._token, interaction_id=self.id,
                                                          application_id=self._application_id, data=data, files=files,
                                                          deferred=self.deferred,
                                                          followup=True if self.callback_message else False,
                                                          use_webhook=False)
        data = await method

        if not isinstance(data, dict):
            data = await self.get_original_callback()

        msg = data if isinstance(data, Message) else Message(state=self._state, channel=self.channel, data=data)
        if not hidden and delete_after is not None:
            await msg.delete(delay=delete_after)
        if hidden is True and not self.deferred:
            self.deferred_hidden = True
        if not self.callback_message:
            self.callback_message = msg
        self.deferred = True
        return msg

    async def get_original_callback(self):
        """|coro|

        Fetch the Original Callback-Message of the Interaction

        .. warning::
            This is a API-Call and should use carefully
        """
        data = await self._state.http.get_original_interaction_response(self._token, self._application_id)
        msg = Message(state=self._state, channel=self.channel, data=data)
        self.callback_message = msg
        return msg


    @property
    def created_at(self):
        """
        Returns the Interaction’s creation time in UTC.

        :return: datetime.datetime
        """
        return utils.snowflake_time(self.id)

    @property
    def author(self) -> Union[Member, User]:
        return self.member if self.member is not None else self.user

    @property
    def channel(self) -> Union[DMChannel, 'TextChannel', ThreadChannel]:
        """The channel where the interaction was invoked in."""
        return self.guild.get_channel(self.channel_id) if self.guild_id else (self._state.get_channel(self.channel_id) or PartialMessageable(id=self.channel_id, type=ChannelType.private, state=self._state))

    @property
    def guild(self) -> Optional[Guild]:
        """The guild of the interaction"""
        return self._state._get_guild(self.guild_id)

    @property
    def message_is_dm(self) -> bool:
        return not self.guild_id

    @property
    def message_is_hidden(self) -> bool:
        return self.message.flags.ephemeral

    @property
    def bot(self):
        """Returns the discord.Client/commands.Bot instance"""
        return self._state._get_client()

    @classmethod
    def from_type(cls, state, data):
        type = try_enum(InteractionType, data['type'])
        if type == InteractionType.ApplicationCommand:
            return ApplicationCommandInteraction(state=state, data=data)
        elif type == InteractionType.Component:
            return ComponentInteraction(state=state, data=data)
        elif type == InteractionType.ApplicationCommandAutocomplete:
            return AutocompleteInteraction(state=state, data=data)

class ApplicationCommandInteraction(BaseInteraction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.type.user:
            self.target = self.data.resolved.members[self.data.target_id]
        elif self.data.type.message:
            self.target = self.data.resolved.messages[self.data.target_id]
        else:
            self.target = None

    @property
    def command(self) -> Union['SlashCommand', 'MessageCommand', 'UserCommand']:
        if getattr(self, '_command', None) is not None:
            return self._command
        return self._state._get_client()._get_application_command(self.data.id) \
            if self.type == InteractionType.ApplicationCommand else None

    async def defer(self,
                    type: Union[Literal[5], InteractionCallbackType] = 5,
                    hidden: bool = False) -> Message:
        """
        Defers the interaction, the user sees a loading state

        Parameters
        ----------
        type: Union[Literal[5], :class:`InteractionCallbackType.deferred_msg_with_source`]
            Currently only one type
        hidden: Optional[:class:`bool`]
            Weather only the author of the command should see this

        Returns
        -------
        Message:
            The Message containing the loading-state
        """
        if isinstance(type, int):
            type = InteractionCallbackType.from_value(type)
        data = await super().defer(type, hidden=hidden)
        return data

class ComponentInteraction(BaseInteraction):
    @property
    def component(self) -> Union[Button, SelectMenu]:
        if self._component is None:
            custom_id = self.data.custom_id
            if custom_id:
                if custom_id.isdigit():
                    custom_id = int(custom_id)
                if self.data.component_type == ComponentType.Button:
                    self._component = utils.get(self.message.all_buttons, custom_id=custom_id)
                elif self.data.component_type == ComponentType.SelectMenu:
                    select_menu = utils.get(self.message.all_select_menus, custom_id=custom_id)
                    if select_menu:
                        setattr(select_menu, '_values', self.data.values)
                    self._component = select_menu
        return self._component


class AutocompleteInteraction(BaseInteraction):
    async def suggest(self, choices: List[SlashCommandOptionChoice]) -> None:
        if len(choices) > 25:
            raise ValueError(f'The maximum of choices is 25. Got {len(choices)}.')
        else:
            await self._http.send_autocomplete_callback(interaction_id=self.id,
                                                        interaction_token=self._token,
                                                        choices=choices)

    async def respond(self, *args, **kwargs):
       raise NotImplementedError

    async def defer(self, *args, **kwargs):
        raise NotImplementedError

class InteractionData:
    def __init__(self, *, state, data, guild=None, **kwargs):
        self._data = data
        self._state = state
        self._guild = guild
        self._channel_id = kwargs.pop('channel_id', None)
        resolved = data.get('resolved', None)
        if resolved:
            self.resolved = ResolvedData(state=state, data=resolved, guild=guild, channel_id=self._channel_id)
        options = self._data.get('options', [])
        self.options = [InteractionDataOption(state=state, data=option, guild=guild) for option in options]

    def __getitem__(self, item):
        return getattr(self, item, NotImplemented)

    @property
    def name(self):
        return self._data.get('name', None)

    @property
    def id(self):
        return int(self._data.get('id', 0))

    @property
    def type(self) -> Optional[ApplicationCommandType]:
        return try_enum(ApplicationCommandType, self._data.get('type', None))

    @property
    def component_type(self):
        return ComponentType.try_value(self._data.get('component_type', None))

    @property
    def custom_id(self):
        return self._data.get('custom_id', None)

    @property
    def target_id(self):
        return int(self._data.get('target_id', 0))

    @property
    def values(self):
        return self._data.get('values', [])


class option_str(str):
    def __new__(cls, *args, **kwargs):
        focused = kwargs.pop('focused', False)
        __self = super().__new__(cls, *args, **kwargs)
        __self.focused = focused
        return __self


class option_int(int):
    def __new__(cls, *args, **kwargs):
        focused = kwargs.pop('focused', False)
        __self = super().__new__(cls, *args, **kwargs)
        __self.focused = focused
        return __self

class option_float(float):
    def __new__(cls, *args, **kwargs):
        focused = kwargs.pop('focused', False)
        __self = super().__new__(cls, *args, **kwargs)
        __self.focused = focused
        return __self

class InteractionDataOption:
    def __init__(self, *, state, data, guild=None, **kwargs):
        self._state = state
        self._guild = guild
        self._data = data
        self._channel_id = kwargs.pop('channel_id', None)
        self.name: str = data['name']
        self.type: OptionType = OptionType.try_value(data['type'])

    @property
    def value(self) -> Optional[Union[str, int, float]]:
        value = self._data.get('value', None)
        if value:
            if isinstance(value, int):
                return option_int(value, focused=self.focused)
            elif isinstance(value, str):
                return option_str(value, focused=self.focused)
            elif isinstance(value, float):
                return option_float(value, focused=self.focused)
            return value

    @property
    def focused(self) -> bool:
        return bool(self._data.get('focused', False))

    @property
    def options(self) -> Optional[List[Any]]:
        options = self._data.get('options', [])
        return [InteractionDataOption(state=self._state, data=option, guild=self._guild) for option in options]


class ResolvedData:
    def __init__(self, *, state, data, guild=None, **kwargs):
        self._state = state
        self._data = data
        self._guild = guild
        self._channel_id = kwargs.pop('channel_id', None)
        for attr in ('users', 'members', 'channels', 'roles', 'messages'):
            setattr(self, f'_{attr}', {})
            value = data.get(attr, None)
            if value is not None:
                getattr(self, f'_{self.__class__.__name__}__handle_{attr}')(value)

    @property
    def users(self) -> Optional[Dict[int, User]]:
        return getattr(self, '_users', {})

    def __handle_users(self, value: dict):
        _users = getattr(self, '_users', {})
        for _id, u in value.items():
            _users[int(_id)] = User(state=self._state, data=u)

    @property
    def members(self) -> Optional[Dict[int, Member]]:
        return getattr(self, '_members', {})

    def __handle_members(self, value: dict):
        _members = getattr(self, '_members', {})
        for _id, m in value.items():
            m['user'] = self._data['users'][_id]
            _members[int(_id)] = Member(state=self._state, data=m, guild=self._guild)
        return _members

    @property
    def channels(self) -> Optional[Dict[int, abc.GuildChannel]]:
        return getattr(self, '_channels', {})

    def __handle_channels(self, value: dict):
        _channels = getattr(self, '_channels', {})
        for _id, c in value.items():
            channel = self._guild.get_channel(int(_id))
            if not channel:
                factory, _ch_type_ = _channel_factory(c['type'])
                channel = factory(guild=self._guild, data=c, state=self._state)
            _channels[int(_id)] = channel
    
    @property
    def roles(self) -> Optional[Dict[int, Role]]:
        return getattr(self, '_roles', {})

    def __handle_roles(self, value: dict):
        _roles: dict = getattr(self, '_roles', {})
        for _id, r in value.items():
            _roles[int(_id)] = Role(guild=self._guild, data=r, state=self._state)

    @property
    def messages(self) -> Optional[Dict[int, Message]]:
        return getattr(self, '_messages', {})

    def __handle_messages(self, value: dict):
        _messages: dict = getattr(self, '_messages', {})
        for _id, m in value.items():
            _messages[int(_id)] = Message(state=self._state, channel=self._state.get_channel(self._channel_id), data=m)
