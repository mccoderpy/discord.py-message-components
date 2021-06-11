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
from .member import Member
from .message import Message
from .errors import NotFound


class _RawReprMixin:
    def __repr__(self):
        value = ' '.join('%s=%r' % (attr, getattr(self, attr)) for attr in self.__slots__)
        return '<%s %s>' % (self.__class__.__name__, value)


class RawMessageDeleteEvent(_RawReprMixin):
    """Represents the event payload for a :func:`on_raw_message_delete` event.

    Attributes
    ------------
    channel_id: :class:`int`
        The channel ID where the deletion took place.
    guild_id: Optional[:class:`int`]
        The guild ID where the deletion took place, if applicable.
    message_id: :class:`int`
        The message ID that got deleted.
    cached_message: Optional[:class:`Message`]
        The cached message, if found in the internal message cache.
    """

    __slots__ = ('message_id', 'channel_id', 'guild_id', 'cached_message')

    def __init__(self, data):
        self.message_id = int(data['id'])
        self.channel_id = int(data['channel_id'])
        self.cached_message = None
        try:
            self.guild_id = int(data['guild_id'])
        except KeyError:
            self.guild_id = None


class RawBulkMessageDeleteEvent(_RawReprMixin):
    """Represents the event payload for a :func:`on_raw_bulk_message_delete` event.

    Attributes
    -----------
    message_ids: Set[:class:`int`]
        A :class:`set` of the message IDs that were deleted.
    channel_id: :class:`int`
        The channel ID where the message got deleted.
    guild_id: Optional[:class:`int`]
        The guild ID where the message got deleted, if applicable.
    cached_messages: List[:class:`Message`]
        The cached messages, if found in the internal message cache.
    """

    __slots__ = ('message_ids', 'channel_id', 'guild_id', 'cached_messages')

    def __init__(self, data):
        self.message_ids = {int(x) for x in data.get('ids', [])}
        self.channel_id = int(data['channel_id'])
        self.cached_messages = []

        try:
            self.guild_id = int(data['guild_id'])
        except KeyError:
            self.guild_id = None


class RawMessageUpdateEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_message_edit` event.

    Attributes
    -----------
    message_id: :class:`int`
        The message ID that got updated.
    channel_id: :class:`int`
        The channel ID where the update took place.

        .. versionadded:: 1.3
    guild_id: Optional[:class:`int`]
        The guild ID where the message got updated, if applicable.

        .. versionadded:: 1.7

    data: :class:`dict`
        The raw data given by the `gateway <https://discord.com/developers/docs/topics/gateway#message-update>`_
    cached_message: Optional[:class:`Message`]
        The cached message, if found in the internal message cache. Represents the message before
        it is modified by the data in :attr:`RawMessageUpdateEvent.data`.
    """

    __slots__ = ('message_id', 'channel_id', 'guild_id', 'data', 'cached_message')

    def __init__(self, data):
        self.message_id = int(data['id'])
        self.channel_id = int(data['channel_id'])
        self.data = data
        self.cached_message = None

        try:
            self.guild_id = int(data['guild_id'])
        except KeyError:
            self.guild_id = None


class RawReactionActionEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_reaction_add` or
    :func:`on_raw_reaction_remove` event.

    Attributes
    -----------
    message_id: :class:`int`
        The message ID that got or lost a reaction.
    user_id: :class:`int`
        The user ID who added the reaction or whose reaction was removed.
    channel_id: :class:`int`
        The channel ID where the reaction got added or removed.
    guild_id: Optional[:class:`int`]
        The guild ID where the reaction got added or removed, if applicable.
    emoji: :class:`PartialEmoji`
        The custom or unicode emoji being used.
    member: Optional[:class:`Member`]
        The member who added the reaction. Only available if `event_type` is `REACTION_ADD` and the reaction is inside a guild.

        .. versionadded:: 1.3

    event_type: :class:`str`
        The event type that triggered this action. Can be
        ``REACTION_ADD`` for reaction addition or
        ``REACTION_REMOVE`` for reaction removal.

        .. versionadded:: 1.3
    """

    __slots__ = ('message_id', 'user_id', 'channel_id', 'guild_id', 'emoji',
                 'event_type', 'member')

    def __init__(self, data, emoji, event_type):
        self.message_id = int(data['message_id'])
        self.channel_id = int(data['channel_id'])
        self.user_id = int(data['user_id'])
        self.emoji = emoji
        self.event_type = event_type
        self.member = None

        try:
            self.guild_id = int(data['guild_id'])
        except KeyError:
            self.guild_id = None


class RawReactionClearEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_reaction_clear` event.

    Attributes
    -----------
    message_id: :class:`int`
        The message ID that got its reactions cleared.
    channel_id: :class:`int`
        The channel ID where the reactions got cleared.
    guild_id: Optional[:class:`int`]
        The guild ID where the reactions got cleared.
    """

    __slots__ = ('message_id', 'channel_id', 'guild_id')

    def __init__(self, data):
        self.message_id = int(data['message_id'])
        self.channel_id = int(data['channel_id'])

        try:
            self.guild_id = int(data['guild_id'])
        except KeyError:
            self.guild_id = None


class RawReactionClearEmojiEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_reaction_clear_emoji` event.

    .. versionadded:: 1.3

    Attributes
    -----------
    message_id: :class:`int`
        The message ID that got its reactions cleared.
    channel_id: :class:`int`
        The channel ID where the reactions got cleared.
    guild_id: Optional[:class:`int`]
        The guild ID where the reactions got cleared.
    emoji: :class:`PartialEmoji`
        The custom or unicode emoji being removed.
    """

    __slots__ = ('message_id', 'channel_id', 'guild_id', 'emoji')

    def __init__(self, data, emoji):
        self.emoji = emoji
        self.message_id = int(data['message_id'])
        self.channel_id = int(data['channel_id'])

        try:
            self.guild_id = int(data['guild_id'])
        except KeyError:
            self.guild_id = None


class RawInteractionCreateEvent(_RawReprMixin):

    __slots__ = ('_data', '_member', '_message_id', '_channel_id', '_guild_id', '__token')

    def __init__(self, data, http=None):
        from .http import HTTPClient
        self.http: HTTPClient = http
        self._type = data.get('t', data.get('type', None))
        d = data.get('d', None)
        if d:
            self.__token = d.get('token', None)
            self._version = d.get('version', None)
            self._type = d.get(type, None)
            if self._type != 'INTERACTION_CREATE':
                return
        else:
            self._version = data.get('version', None)
            self._type = data.get('type', None)
            self.__token = data.get('token', None)
        self._raw = data
        self._message_id = data.get('message').get('id', None)
        self._data = data.get('data', None)
        self._member = data.get('member', None)
        self.__interaction_id = data.get('id', 0)
        self._guild_id = data.get('guild_id', 0)
        self._channel_id = data.get('channel_id', 0)
        self.__application_id = data.get('application_id', 0)
        self.guild = None
        self.channel = None
        self.member: Member = None
        self.user = None
        self._user = dict(self.member._user) if self.member else data.get('user')
        self.button = ClickEvent(self._data)
        self.message: Message = None
        self._deferred = False

    async def defer(self, ):
        """
        'Defers' the response, showing a loading state to the user
        """
        if self._deferred:
            return print("\033[91You have already responded to this Interaction!\033[0m")
        base = {"type": 6}
        try:
            await self.http.post_initial_response(_resp=base, use_webhook=False, interaction_id=self.__interaction_id, token=self.__token, application_id=self.__application_id)
        except NotFound:
            pass
        else:
            self._deferred = True

    async def edit(self, **fields):
        """
        'Defers' if it isn't yet and edit the message
        """
        if not self.message:
            self.message: Message = await self.channel.fetch_message(self._message_id)
        await self.message.edit(__is_interaction_responce=True, __deffered=self.deffered, __use_webhook=False, __interaction_id=self.__interaction_id, __interaction_token=self.__token, __application_id=self.__application_id, **fields)
        self._deferred = True

    @property
    def deffered(self):
        return self._deferred

    @property
    def token(self):
        return self.__token

    @property
    def initeraction_id(self):
        return int(self.__interaction_id)

    @property
    def guild_id(self):
        return int(self._guild_id)

    @property
    def channel_id(self):
        return int(self._channel_id)

    @property
    def message_id(self):
        return int(self._message_id)


class ClickEvent:
    def __init__(self, data):
        if data:
            self._custom_id = data.get('custom_id', None)
            self._component_type = data.get('component_type')

    def __repr__(self):
        return f"<ClickEvent {self._custom_id, self._component_type}"

    @property
    def custom_id(self):
        return self._custom_id

    @property
    def component_type(self):
        return self._component_type
