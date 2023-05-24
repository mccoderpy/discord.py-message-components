# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz & (c) 2021-present mccoderpy

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

import asyncio
from datetime import datetime
from base64 import b64decode
import re
import io

from typing import (
    TYPE_CHECKING,
    Union,
    Optional,
    Callable,
    Sequence,
    Iterator,
    List,
    Any
)

from typing_extensions import Self

from . import utils
from .reaction import Reaction
from .emoji import Emoji
from .partial_emoji import PartialEmoji
from .enums import try_enum, MessageType, ChannelType, AutoArchiveDuration, InteractionType
from .errors import InvalidArgument, HTTPException
from .components import ActionRow, Button, BaseSelect
from .embeds import Embed
from .member import Member
from .flags import MessageFlags
from .file import File
from .utils import escape_mentions
from .guild import Guild
from .mixins import Hashable
from .sticker import Sticker
from .http import handle_message_parameters
from .channel import PartialMessageable, ThreadChannel

if TYPE_CHECKING:
    from os import PathLike
    from .types.user import PartialMember as PartialMemberPayload
    from .types.message import (
        Attachment as AttachmentPayload,
        Message as MessagePayload,
        MessageReference as MessageReferencePayload,
        MessageInteraction as MessageInteractionPayload
    )
    from .user import User
    from .state import ConnectionState
    from .http import HTTPClient
    from .mentions import AllowedMentions
    from .abc import Messageable, Snowflake
    from .sticker import GuildSticker
    from .channel import TextChannel, VoiceChannel, StageChannel, TextChannel, ForumChannel, ForumPost

    MentionableChannel = Union[TextChannel, VoiceChannel, StageChannel, ThreadChannel, TextChannel, ForumChannel, ForumPost]

__all__ = (
    'Attachment',
    'MessageInteraction',
    'Message',
    'PartialMessage',
    'MessageReference',
    'DeletedReferencedMessage',
)


MISSING = utils.MISSING


def convert_emoji_reaction(emoji: Union[Reaction, Emoji, PartialEmoji, str]) -> str:
    if isinstance(emoji, Reaction):
        emoji = emoji.emoji

    if isinstance(emoji, Emoji):
        return f'{emoji.name}:{emoji.id}'
    if isinstance(emoji, PartialEmoji):
        return emoji._as_reaction()
    if isinstance(emoji, str):
        # Reactions can be in :name:id format, but not <:name:id>.
        # No existing emojis have <> in them, so this should be okay.
        return emoji.strip('<>')

    raise InvalidArgument('emoji argument must be str, Emoji, or Reaction not {.__class__.__name__}.'.format(emoji))


class Attachment(Hashable):

    """Represents an attachment from Discord.

    .. container:: operations

        .. describe:: str(x)

            Returns the URL of the attachment.

        .. describe:: x == y

            Checks if the attachment is equal to another attachment.

        .. describe:: x != y

            Checks if the attachment is not equal to another attachment.

        .. describe:: hash(x)

            Returns the hash of the attachment.

    .. versionchanged:: 1.7
        Attachment can now be cast to :class:`str` and is hashable.
    .. versionchanged:: 2.0
        The :attr:`ephemeral`, :attr:`description`, :attr:`duration` and :attr:`waveform` attributes were added.

    Attributes
    ------------
    id: :class:`int`
        The attachment ID.
    size: :class:`int`
        The attachment size in bytes.
    height: Optional[:class:`int`]
        The attachment's height, in pixels. Only applicable to images and videos.
    width: Optional[:class:`int`]
        The attachment's width, in pixels. Only applicable to images and videos.
    filename: :class:`str`
        The attachment's filename.
    url: :class:`str`
        The attachment URL. If the message this attachment was attached
        to is deleted, then this will 404.
    proxy_url: :class:`str`
        The proxy URL. This is a cached version of the :attr:`~Attachment.url` in the
        case of images. When the message is deleted, this URL might be valid for a few
        minutes or not valid at all.
    content_type: Optional[:class:`str`]
        The attachment's `media type <https://en.wikipedia.org/wiki/Media_type>`_
    ephemeral: :class:`bool`
        Whether the attachment is ephemeral (part of an ephemeral message or was provided in a slash-command option).
    description: Optional[:class:`str`]
        The description for the file.
    duration: Optional[:class:`float`]
        The duration of the audio file (currently only for voice messages).
    """

    __slots__ = ('id', 'size', 'height', 'width', 'ephemeral', 'description',
                 'filename', 'url', 'proxy_url', '_http', 'content_type', 'duration', '_waveform')

    def __init__(self, *, data: AttachmentPayload, state: ConnectionState):
        self.id: int = int(data['id'])
        self.size: int = data['size']
        self.height: Optional[int] = data.get('height')
        self.width: Optional[int] = data.get('width')
        self.ephemeral: bool = data.get('ephemeral', False)
        self.description: Optional[str] = data.get('description')
        self.filename: str = data['filename']
        self.url: str = data.get('url')
        self.proxy_url = data.get('proxy_url')
        self._http: HTTPClient = state.http
        self.content_type: str = data.get('content_type')
        self.duration: Optional[float] = data.get('duration_secs')
        self._waveform: Optional[List[int]] = data.get('waveform')

    def is_spoiler(self) -> bool:
        """:class:`bool`: Whether this attachment contains a spoiler."""
        return self.filename.startswith('SPOILER_')
    
    @property
    def waveform(self) -> Optional[bytearray]:
        """:class:`Optional[List[:class:`int`]]`: The waveform of the audio file (currently only for voice messages)."""
        return b64decode(self._waveform) if self._waveform else None

    def __repr__(self) -> str:
        return '<Attachment id={0.id} filename={0.filename!r} url={0.url!r}>'.format(self)

    def __str__(self) -> str:
        return self.url or ''

    def _to_minimal_dict(self):
        """:class:`dict`: A minimal dictionary containing the filename and description of the attachment."""
        return {'filename': self.filename, 'description': self.description}

    to_dict = _to_minimal_dict

    async def save(
            self,
            fp: Union[io.BufferedIOBase, PathLike[str], PathLike[bytes]],
            *,
            seek_begin: bool = True,
            use_cached: bool = False
    ) -> int:
        """|coro|

        Saves this attachment into a file-like object.

        Parameters
        -----------
        fp: Union[:class:`io.BufferedIOBase`, :class:`os.PathLike`]
            The file-like object to save this attachment to or the filename
            to use. If a filename is passed then a file is created with that
            filename and used instead.
        seek_begin: :class:`bool`
            Whether to seek to the beginning of the file after saving is
            successfully done.
        use_cached: :class:`bool`
            Whether to use :attr:`proxy_url` rather than :attr:`url` when downloading
            the attachment. This will allow attachments to be saved after deletion
            more often, compared to the regular URL which is generally deleted right
            after the message is deleted. Note that this can still fail to download
            deleted attachments if too much time has passed and it does not work
            on some types of attachments.

        Raises
        --------
        HTTPException
            Saving the attachment failed.
        NotFound
            The attachment was deleted.

        Returns
        --------
        :class:`int`
            The number of bytes written.
        """
        data = await self.read(use_cached=use_cached)
        if isinstance(fp, io.IOBase) and fp.writable():
            written = fp.write(data)
            if seek_begin:
                fp.seek(0)
            return written
        else:
            with open(fp, 'wb') as f:
                return f.write(data)

    async def read(self, *, use_cached: bool = False) -> bytes:
        """|coro|

        Retrieves the content of this attachment as a :class:`bytes` object.

        .. versionadded:: 1.1

        Parameters
        -----------
        use_cached: :class:`bool`
            Whether to use :attr:`proxy_url` rather than :attr:`url` when downloading
            the attachment. This will allow attachments to be saved after deletion
            more often, compared to the regular URL which is generally deleted right
            after the message is deleted. Note that this can still fail to download
            deleted attachments if too much time has passed and it does not work
            on some types of attachments.

        Raises
        ------
        HTTPException
            Downloading the attachment failed.
        Forbidden
            You do not have permissions to access this attachment
        NotFound
            The attachment was deleted.

        Returns
        -------
        :class:`bytes`
            The contents of the attachment.
        """
        url = self.proxy_url if use_cached else self.url
        return await self._http.get_from_cdn(url)

    async def to_file(
            self,
            *,
            use_cached: bool = False,
            spoiler: bool = False,
            description: Optional[str] = MISSING
    ) -> File:
        """|coro|

        Converts the attachment into a :class:`File` suitable for sending via
        :meth:`abc.Messageable.send`.

        .. versionadded:: 1.3

        Parameters
        -----------
        use_cached: :class:`bool`
            Whether to use :attr:`proxy_url` rather than :attr:`url` when downloading
            the attachment. This will allow attachments to be saved after deletion
            more often, compared to the regular URL which is generally deleted right
            after the message is deleted. Note that this can still fail to download
            deleted attachments if too much time has passed and it does not work
            on some types of attachments.

            .. versionadded:: 1.4
        spoiler: :class:`bool`
            Whether the file is a spoiler.

            .. versionadded:: 1.4
        description: :class:`bool`
            The description (*alt text*) for the file.

            This will be default to the :attr:`~discord.Attachment.description`.
            Set the value to :obj:`None` to supress this.
            .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Downloading the attachment failed.
        Forbidden
            You do not have permissions to access this attachment
        NotFound
            The attachment was deleted.

        Returns
        -------
        :class:`File`
            The attachment as a file suitable for sending.
        """

        data = await self.read(use_cached=use_cached)
        return File(
            io.BytesIO(data),
            filename=self.filename,
            spoiler=spoiler,
            description=self.description if description is MISSING else description
        )


class MessageInteraction:
    """
    Represents the :attr:`~Message.interaction` object of a message that is a response to an interaction without an existing message.

    .. note::
        This means responses to :class:`ComponentInteraction` does not include this,
        instead including a :attr:`~Message.reference` as components *always* exist on preexisting messages.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The interaction's ID.
    type: :class:`InteractionType`
        The type of the interaction.
    name: :class:`str`
        The name of the :class:`ApplicationCommand`, **including subcommands and subcommand groups**.
    user: :class:`User`
        The user who invoked the interaction.
    """
    def __init__(self, state: ConnectionState, data: MessageInteractionPayload, guild: Optional[Guild] = None) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.type: InteractionType = try_enum(InteractionType, data['type'])
        self.name: Optional[str] = data['name']
        self.user: User = state.store_user(data['user'])
        try:
            member = data['member']
        except KeyError:
            self.member: Optional[Member] = None
        else:
            member['user'] = data['user']
            if guild:  # can be None when cache is not filled yet 
                self.member: Optional[Member] = guild.get_member(self.user.id) or Member(data=member, state=state, guild=guild)
            else:
                self.member: Optional[Member] = None
    
    def __repr__(self) -> str:
        return f'<MessageInteraction command={self.name} user={self.user} interaction_id={self.id}>'


class DeletedReferencedMessage:
    """A special sentinel type that denotes whether the
    resolved message referenced message had since been deleted.

    The purpose of this class is to separate referenced messages that could not be
    fetched and those that were previously fetched but have since been deleted.

    .. versionadded:: 1.6
    """

    __slots__ = ('_parent')

    def __init__(self, parent: Message) -> None:
        self._parent = parent

    @property
    def id(self) -> int:
        """:class:`int`: The message ID of the deleted referenced message."""
        return self._parent.message_id

    @property
    def channel_id(self) -> int:
        """:class:`int`: The channel ID of the deleted referenced message."""
        return self._parent.channel_id

    @property
    def guild_id(self) -> int:
        """Optional[:class:`int`]: The guild ID of the deleted referenced message."""
        return self._parent.guild_id


class MessageReference:

    """Represents a reference to a :class:`~discord.Message`.

    .. versionadded:: 1.5

    .. versionchanged:: 1.6
        This class can now be constructed by users.

    Attributes
    -----------
    message_id: Optional[:class:`int`]
        The id of the message referenced.
    channel_id: :class:`int`
        The channel id of the message referenced.
    guild_id: Optional[:class:`int`]
        The guild id of the message referenced.
    fail_if_not_exists: :class:`bool`
        Whether replying to the referenced message should raise :class:`HTTPException`
        if the message no longer exists or Discord could not fetch the message.

        .. versionadded:: 1.7

    resolved: Optional[Union[:class:`Message`, :class:`DeletedReferencedMessage`]]
        The message that this reference resolved to. If this is ``None``
        then the original message was not fetched either due to the Discord API
        not attempting to resolve it or it not being available at the time of creation.
        If the message was resolved at a prior point but has since been deleted then
        this will be of type :class:`DeletedReferencedMessage`.

        Currently, this is mainly the replied to message when a user replies to a message.

        .. versionadded:: 1.6
    """

    __slots__ = ('message_id', 'channel_id', 'guild_id', 'fail_if_not_exists', 'resolved', '_state')

    def __init__(self, *, message_id: int, channel_id: int, guild_id: Optional[int] = None, fail_if_not_exists: bool = True) -> None:
        self._state: Optional[ConnectionState] = None
        self.resolved: Optional[Union[Message, DeletedReferencedMessage]] = None
        self.message_id = message_id
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.fail_if_not_exists = fail_if_not_exists

    @classmethod
    def with_state(cls, state: ConnectionState, data: MessageReferencePayload) -> MessageReference:
        self = cls.__new__(cls)
        self.message_id = utils._get_as_snowflake(data, 'message_id')
        self.channel_id = int(data.pop('channel_id'))
        self.guild_id = utils._get_as_snowflake(data, 'guild_id')
        self.fail_if_not_exists = data.get('fail_if_not_exists', True)
        self._state = state
        self.resolved = None
        return self

    @classmethod
    def from_message(cls, message: Message, *, fail_if_not_exists: bool = True) -> MessageReference:
        """Creates a :class:`MessageReference` from an existing :class:`~discord.Message`.

        .. versionadded:: 1.6

        Parameters
        ----------
        message: :class:`~discord.Message`
            The message to be converted into a reference.
        fail_if_not_exists: :class:`bool`
            Whether replying to the referenced message should raise :class:`HTTPException`
            if the message no longer exists or Discord could not fetch the message.

            .. versionadded:: 1.7

        Returns
        -------
        :class:`MessageReference`
            A reference to the message.
        """
        self = cls(message_id=message.id, channel_id=message.channel.id, guild_id=getattr(message.guild, 'id', None), fail_if_not_exists=fail_if_not_exists)
        self._state = message._state
        return self

    @property
    def cached_message(self) -> Optional[Message]:
        """Optional[:class:`~discord.Message`]: The cached message, if found in the internal message cache."""
        return self._state._get_message(self.message_id)

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the referenced message.

        .. versionadded:: 1.7
        """
        guild_id = self.guild_id if self.guild_id is not None else '@me'
        return 'https://discord.com/channels/{0}/{1.channel_id}/{1.message_id}'.format(guild_id, self)

    def __repr__(self) -> str:
        return '<MessageReference message_id={0.message_id!r} channel_id={0.channel_id!r} guild_id={0.guild_id!r}>'.format(self)

    def to_dict(self) -> MessageReferencePayload:
        result = {'message_id': self.message_id} if self.message_id is not None else {}
        result['channel_id'] = self.channel_id
        if self.guild_id is not None:
            result['guild_id'] = self.guild_id
        if self.fail_if_not_exists is not None:
            result['fail_if_not_exists'] = self.fail_if_not_exists
        return result

    to_message_reference_dict = to_dict


def flatten_handlers(cls):
    prefix = len('_handle_')
    handlers = [
        (key[prefix:], value)
        for key, value in cls.__dict__.items()
        if key.startswith('_handle_') and key != '_handle_member'
    ]

    # store _handle_member last
    handlers.append(('member', cls._handle_member))
    cls._HANDLERS = handlers
    cls._CACHED_SLOTS = [
        attr for attr in cls.__slots__ if attr.startswith('_cs_')
    ]
    return cls


@flatten_handlers
class Message(Hashable):
    r"""Represents a message from Discord.

    .. container:: operations

        .. describe:: x == y

            Checks if two messages are equal.

        .. describe:: x != y

            Checks if two messages are not equal.

        .. describe:: hash(x)

            Returns the message's hash.

    Attributes
    -----------
    tts: :class:`bool`
        Specifies if the message was done with text-to-speech.
        This can only be accurately received in :func:`on_message` due to
        a discord limitation.
    type: :class:`MessageType`
        The type of message. In most cases this should not be checked, but it is helpful
        in cases where it might be a system message for :attr:`system_content`.
    author: :class:`abc.User`
        A :class:`Member` that sent the message. If :attr:`channel` is a
        private channel or the user has left the guild, then it is a :class:`User` instead.
    content: :class:`str`
        The actual contents of the message.
    nonce
        The value used by the discord guild and the client to verify that the message is successfully sent.
        This is not stored long term within Discord's servers and is only used ephemerally.
    embeds: List[:class:`Embed`]
        A list of embeds the message has.
    components: List[:class:`~discord.ActionRow`]:
        A list of components the message has.
    channel: Union[:class:`abc.Messageable`, :class:`~discord.ThreadChannel`]
        The :class:`TextChannel`, :class:`~discord.ThreadChannel` or :class:`VoiceChannel` that the message was sent from.
        Could be a :class:`DMChannel` or :class:`GroupChannel` if it's a private message.
    reference: Optional[:class:`~discord.MessageReference`]
        The message that this message references. This is only applicable to messages of
        type :attr:`MessageType.pins_add`, crossposted messages created by a
        followed channel integration, or message replies.

        .. versionadded:: 1.5

    mention_everyone: :class:`bool`
        Specifies if the message mentions everyone.

        .. note::

            This does not check if the ``@everyone`` or the ``@here`` text is in the message itself.
            Rather this boolean indicates if either the ``@everyone`` or the ``@here`` text is in the message
            **and** it did end up mentioning.
    mentions: List[:class:`abc.User`]
        A list of :class:`Member` that were mentioned. If the message is in a private message
        then the list will be of :class:`User` instead. For messages that are not of type
        :attr:`MessageType.default`\, this array can be used to aid in system messages.
        For more information, see :attr:`system_content`.

        .. warning::

            The order of the mentions list is not in any particular order so you should
            not rely on it. This is a Discord limitation, not one with the library.
    channel_mentions: List[:class:`abc.GuildChannel`]
        A list of :class:`abc.GuildChannel` that were mentioned. If the message is in a private message
        then the list is always empty.
    role_mentions: List[:class:`Role`]
        A list of :class:`Role` that were mentioned. If the message is in a private message
        then the list is always empty.
    id: :class:`int`
        The message ID.
    webhook_id: Optional[:class:`int`]
        If this message was sent by a webhook, then this is the webhook ID's that sent this
        message.
    attachments: List[:class:`Attachment`]
        A list of attachments given to a message.
    pinned: :class:`bool`
        Specifies if the message is currently pinned.
    flags: :class:`MessageFlags`
        Extra features of the message.

        .. versionadded:: 1.3
    reactions : List[:class:`Reaction`]
        Reactions to a message. Reactions can be either custom emoji or standard unicode emoji.
    activity: Optional[:class:`dict`]
        The activity associated with this message. Sent with Rich-Presence related messages that for
        example, request joining, spectating, or listening to or with another member.

        It is a dictionary with the following optional keys:

        - ``type``: An integer denoting the type of message activity being requested.
        - ``party_id``: The party ID associated with the party.
    application: Optional[:class:`dict`]
        The rich presence enabled application associated with this message.

        It is a dictionary with the following keys:

        - ``id``: A string representing the application's ID.
        - ``name``: A string representing the application's name.
        - ``description``: A string representing the application's description.
        - ``icon``: A string representing the icon ID of the application.
        - ``cover_image``: A string representing the embed's image asset ID.
    stickers: List[:class:`Sticker`]
        A list of stickers given to the message.

        .. versionadded:: 1.6
    interaction: Optional[:class:`MessageInteraction`]
        The interaction associated with this message if any.
    """

    __slots__ = ('_edited_timestamp', 'tts', 'content', 'channel', 'webhook_id',
                 'mention_everyone', 'embeds', 'components', 'id', 'mentions', 'author',
                 '_cs_channel_mentions', '_cs_raw_mentions', 'attachments',
                 '_cs_clean_content', '_cs_raw_channel_mentions', 'nonce', 'pinned',
                 'role_mentions', '_cs_raw_role_mentions', 'type', 'flags',
                 '_cs_system_content', '_cs_guild', '_state', 'reactions', 'reference',
                 'application', 'activity', 'stickers', '_thread', 'interaction')

    def __init__(self, *, state: ConnectionState, channel, data: MessagePayload):
        self._state: ConnectionState = state
        self.id: int = utils._get_as_snowflake(data, 'id')
        self.webhook_id: Optional[int] = utils._get_as_snowflake(data, 'webhook_id')
        self.reactions: List[Reaction] = [Reaction(message=self, data=d) for d in data.get('reactions', [])]
        self.attachments: List[Attachment] = [Attachment(data=a, state=self._state) for a in data.get('attachments', [])]
        self.embeds: List[Embed] = [Embed.from_dict(a) for a in data.get('embeds', [])]
        self.components: List[ActionRow] = [ActionRow.from_dict(d) for d in data.get('components', [])]
        self.application = data.get('application')  # TODO: make this a class
        self.activity = data.get('activity')  # TODO: make this a class
        self.channel: Messageable = channel
        interaction = data.get('interaction')
        self.interaction: Optional[MessageInteraction] = MessageInteraction(
            state=state,
            data=interaction,
            guild=self.guild
        ) if interaction else None
        self._edited_timestamp: datetime = utils.parse_time(data['edited_timestamp'])
        self.type: MessageType = try_enum(MessageType, data['type'])
        self.pinned: bool = data['pinned']
        self.mention_everyone: bool = data['mention_everyone']
        self.tts: bool = data['tts']
        self.content: Optional[str] = data['content']
        self.nonce: Optional[str] = data.get('nonce')
        self.stickers: List[Union[Sticker, GuildSticker]] = [Sticker(data=data, state=state) for data in data.get('sticker_items', [])]

        try:
            ref = data['message_reference']
        except KeyError:
            self.reference: Optional[Union[MessageReference, DeletedReferencedMessage]] = None
        else:
            self.reference = ref = MessageReference.with_state(state, ref)
            try:
                resolved = data['referenced_message']
            except KeyError:
                pass
            else:
                if resolved is None:
                    ref.resolved = DeletedReferencedMessage(ref)
                else:
                    # Right now the channel IDs match but maybe in the future they won't.
                    if ref.channel_id == channel.id:
                        chan = channel
                    else:
                        chan, _ = state._get_guild_channel(resolved)

                    ref.resolved = self.__class__(channel=chan, data=resolved, state=state)

        for handler in ('author', 'member', 'mentions', 'mention_roles', 'flags', 'thread'):
            try:
                getattr(self, f'_handle_{handler}')(data[handler])
            except KeyError:
                continue

    def __repr__(self) -> str:
        return '<Message id={0.id} channel={0.channel!r} type={0.type!r} author={0.author!r} flags={0.flags!r}>'.format(self)

    def __remove_from_cache__(self, _):
        self._state._messages.remove(self)

    def _try_patch(self, data: MessagePayload, key: str, transform: Optional[Callable[..., Any]] = None) -> None:
        try:
            value = data[key]
        except KeyError:
            pass
        else:
            if transform is None:
                setattr(self, key, value)
            else:
                setattr(self, key, transform(value))

    def _add_reaction(self, data, emoji, user_id):
        reaction = utils.find(lambda r: r.emoji == emoji, self.reactions)
        is_me = data['me'] = user_id == self._state.self_id

        if reaction is None:
            reaction = Reaction(message=self, data=data, emoji=emoji)
            self.reactions.append(reaction)
        else:
            reaction.count += 1
            if is_me:
                reaction.me = is_me

        return reaction

    def _remove_reaction(self, data, emoji, user_id):
        reaction = utils.find(lambda r: r.emoji == emoji, self.reactions)

        if reaction is None:
            # already removed?
            raise ValueError('Emoji already removed?')

        # if reaction isn't in the list, we crash. This means discord
        # sent bad data, or we stored improperly
        reaction.count -= 1

        if user_id == self._state.self_id:
            reaction.me = False
        if reaction.count == 0:
            # this raises ValueError if something went wrong as well.
            self.reactions.remove(reaction)

        return reaction

    def _clear_emoji(self, emoji: Union[Emoji, PartialEmoji, str]):
        to_check = str(emoji)
        for index, reaction in enumerate(self.reactions):
            if str(reaction.emoji) == to_check:
                break
        else:
            # didn't find anything so just return
            return

        del self.reactions[index]
        return reaction

    def _update(self: Self, data: MessagePayload) -> Self:
        # In an update scheme, 'author' key has to be handled before 'member'
        # otherwise they overwrite each other which is undesirable.
        # Since there's no good way to do this we have to iterate over every
        # handler rather than iterating over the keys which is a little slower
        for key, handler in self._HANDLERS:
            try:
                value = data[key]
            except KeyError:
                continue
            else:
                handler(self, value)

        # clear the cached properties
        for attr in self._CACHED_SLOTS:
            try:
                delattr(self, attr)
            except AttributeError:
                pass
        return self

    def _handle_edited_timestamp(self, value):
        self._edited_timestamp = utils.parse_time(value)

    def _handle_pinned(self, value):
        self.pinned = value

    def _handle_flags(self, value):
        self.flags: MessageFlags = MessageFlags._from_value(value)

    def _handle_application(self, value):
        self.application = value

    def _handle_activity(self, value):
        self.activity = value

    def _handle_mention_everyone(self, value):
        self.mention_everyone: bool = value

    def _handle_tts(self, value):
        self.tts = value

    def _handle_type(self, value):
        self.type = try_enum(MessageType, value)

    def _handle_content(self, value):
        self.content: str = value

    def _handle_attachments(self, value):
        self.attachments: List[Attachment] = [Attachment(data=a, state=self._state) for a in value]

    def _handle_embeds(self, value):
        self.embeds: List[Embed] = [Embed.from_dict(data) for data in value]

    def _handle_interaction(self, value):
        self.interaction = MessageInteraction(state=self._state, data=value)

    def _handle_thread(self, value):
        if thread := self.guild.get_channel(self.id):
            self._thread = thread._update(self.guild, value)
        else:
            self._thread = ThreadChannel(state=self._state, guild=self.channel.guild, data=value)
            self.channel.guild._add_thread(self._thread)

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

    def _rebind_channel_reference(self, new_channel):
        self.channel = new_channel

        try:
            del self._cs_guild
        except AttributeError:
            pass

    @utils.cached_slot_property('_cs_guild')
    def guild(self) -> Guild:
        """Optional[:class:`Guild`]: The guild that the message belongs to, if applicable."""
        return getattr(self.channel, 'guild', None)

    @utils.cached_slot_property('_cs_raw_mentions')
    def raw_mentions(self) -> List[int]:
        """List[:class:`int`]: A property that returns an array of user IDs matched with
        the syntax of ``<@user_id>`` in the message content.

        This allows you to receive the user IDs of mentioned users
        even in a private message context.
        """
        return [int(x) for x in re.findall(r'<@!?([0-9]+)>', self.content)]

    @utils.cached_slot_property('_cs_raw_channel_mentions')
    def raw_channel_mentions(self) -> List[int]:
        """List[:class:`int`]: A property that returns an array of channel IDs matched with
        the syntax of ``<#channel_id>`` in the message content.
        """
        return [int(x) for x in re.findall(r'<#([0-9]+)>', self.content)]

    @utils.cached_slot_property('_cs_raw_role_mentions')
    def raw_role_mentions(self) -> List[int]:
        """List[:class:`int`]: A property that returns an array of role IDs matched with
        the syntax of ``<@&role_id>`` in the message content.
        """
        return [int(x) for x in re.findall(r'<@&([0-9]+)>', self.content)]

    @utils.cached_slot_property('_cs_channel_mentions')
    def channel_mentions(self) -> List[MentionableChannel]:
        if self.guild is None:
            return []
        it = filter(None, map(self.guild.get_channel, self.raw_channel_mentions))
        return utils._unique(it)

    @utils.cached_slot_property('_cs_clean_content')
    def clean_content(self) -> str:
        """:class:`str`: A property that returns the content in a "cleaned up"
        manner. This basically means that mentions are transformed
        into the way the client shows it. e.g. ``<#id>`` will transform
        into ``#name``.

        This will also transform @everyone and @here mentions into
        non-mentions.

        .. note::

            This *does not* affect markdown. If you want to escape
            or remove markdown then use :func:`utils.escape_markdown` or :func:`utils.remove_markdown`
            respectively, along with this function.
        """

        transformations = {
            re.escape(f'<#{channel.id}>'): f'#{channel.name}'
            for channel in self.channel_mentions
        }

        mention_transforms = {
            re.escape(f'<@{member.id}>'): f'@{member.display_name}'
            for member in self.mentions
        }

        # add the <@!user_id> cases as well..
        second_mention_transforms = {
            re.escape(f'<@!{member.id}>'): f'@{member.display_name}'
            for member in self.mentions
        }

        transformations.update(mention_transforms)
        transformations.update(second_mention_transforms)

        if self.guild is not None:
            role_transforms = {
                re.escape(f'<@&{role.id}>'): f'@{role.name}'
                for role in self.role_mentions
            }
            transformations.update(role_transforms)

        def repl(obj):
            return transformations.get(re.escape(obj.group(0)), '')

        pattern = re.compile('|'.join(transformations.keys()))
        result = pattern.sub(repl, self.content)
        return escape_mentions(result)

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: The message's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def edited_at(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: A naive UTC datetime object containing the edited time of the message."""
        return self._edited_timestamp

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to this message."""
        guild_id = getattr(self.guild, 'id', '@me')
        return 'https://discord.com/channels/{0}/{1.channel.id}/{1.id}'.format(guild_id, self)

    def is_system(self) -> bool:
        """:class:`bool`: Whether the message is a system message.

        .. versionadded:: 1.3
        """
        return self.type is not MessageType.default

    @utils.cached_slot_property('_cs_system_content')
    def system_content(self) -> str:
        r""":class:`str`: A property that returns the content that is rendered
        regardless of the :attr:`Message.type`.

        In the case of :attr:`MessageType.default`\, this just returns the
        regular :attr:`Message.content`. Otherwise this returns an English
        message denoting the contents of the system message.
        """

        if self.type is MessageType.default:
            return self.content

        if self.type is MessageType.pins_add:
            return '{0.name} pinned a message to this channel.'.format(self.author)

        if self.type is MessageType.recipient_add:
            return '{0.name} added {1.name} to the group.'.format(self.author, self.mentions[0])

        if self.type is MessageType.recipient_remove:
            return '{0.name} removed {1.name} from the group.'.format(self.author, self.mentions[0])

        if self.type is MessageType.channel_name_change:
            return '{0.author.name} changed the channel name: {0.content}'.format(self)

        if self.type is MessageType.channel_icon_change:
            return '{0.author.name} changed the channel icon.'.format(self)

        if self.type is MessageType.new_member:
            formats = [
                "{0} joined the party.",
                "{0} is here.",
                "Welcome, {0}. We hope you brought pizza.",
                "A wild {0} appeared.",
                "{0} just landed.",
                "{0} just slid into the server.",
                "{0} just showed up!",
                "Welcome {0}. Say hi!",
                "{0} hopped into the server.",
                "Everyone welcome {0}!",
                "Glad you're here, {0}.",
                "Good to see you, {0}.",
                "Yay you made it, {0}!",
            ]

            # manually reconstruct the epoch with millisecond precision, because
            # datetime.datetime.timestamp() doesn't return the exact posix
            # timestamp with the precision that we need
            created_at_ms = int((self.created_at - datetime(1970, 1, 1)).total_seconds() * 1000)
            return formats[created_at_ms % len(formats)].format(self.author.name)

        if self.type is MessageType.call:
            # we're at the call message type now, which is a bit more complicated.
            # we can make the assumption that Message.channel is a PrivateChannel
            # with the type ChannelType.group or ChannelType.private
            call_ended = self.call.ended_timestamp is not None

            if self.channel.me in self.call.participants:
                return '{0.author.name} started a call.'.format(self)
            elif call_ended:
                return 'You missed a call from {0.author.name}'.format(self)
            else:
                return '{0.author.name} started a call \N{EM DASH} Join the call.'.format(self)

        if self.type is MessageType.premium_guild_subscription:
            return '{0.author.name} just boosted the server!'.format(self)

        if self.type is MessageType.premium_guild_tier_1:
            return '{0.author.name} just boosted the server! {0.guild} has achieved **Level 1!**'.format(self)

        if self.type is MessageType.premium_guild_tier_2:
            return '{0.author.name} just boosted the server! {0.guild} has achieved **Level 2!**'.format(self)

        if self.type is MessageType.premium_guild_tier_3:
            return '{0.author.name} just boosted the server! {0.guild} has achieved **Level 3!**'.format(self)

        if self.type is MessageType.channel_follow_add:
            return '{0.author.name} has added {0.content} to this channel'.format(self)

        if self.type is MessageType.guild_stream:
            return '{0.author.name} is live! Now streaming {0.author.activity.name}'.format(self)

        if self.type is MessageType.guild_discovery_disqualified:
            return 'This server has been removed from Server Discovery because it no longer passes all the requirements. Check Server Settings for more details.'

        if self.type is MessageType.guild_discovery_requalified:
            return 'This server is eligible for Server Discovery again and has been automatically relisted!'

        if self.type is MessageType.guild_discovery_grace_period_initial_warning:
            return 'This server has failed Discovery activity requirements for 1 week. If this server fails for 4 weeks in a row, it will be automatically removed from Discovery.'

        if self.type is MessageType.guild_discovery_grace_period_final_warning:
            return 'This server has failed Discovery activity requirements for 3 weeks in a row. If this server fails for 1 more week, it will be removed from Discovery.'

    @property
    def all_components(self) -> Iterator[Union[Button, BaseSelect]]:
        """Returns all :class:`Button`'s and :class:`SelectMenu`'s that are contained in the message"""
        for action_row in self.components:
            yield from action_row

    @property
    def all_buttons(self) -> Iterator[Button]:
        """Returns all :class:`Button`'s that are contained in the message"""
        for action_row in self.components:
            for component in action_row:
                if isinstance(component, Button):
                    yield component

    @property
    def all_select_menus(self) -> Iterator[BaseSelect]:
        """Returns all :class:`SelectMenu`'s that are contained in the message"""
        for action_row in self.components:
            for component in action_row:
                if int(component.type) in {3, 5, 6, 7, 8}:
                    yield component

    @property
    def thread(self) -> Optional[ThreadChannel]:
        """Optional[:class:`ThreadChannel`]: The thread that belongs to this message, if there is one"""
        return getattr(self, '_thread', None)

    async def delete(self, *, delay: Optional[float] = None):
        """|coro|

        Deletes the message.

        Your own messages could be deleted without any proper permissions. However, to
        delete other people's messages, you need the :attr:`~Permissions.manage_messages`
        permission.

        .. versionchanged:: 1.1
            Added the new ``delay`` keyword-only parameter.

        Parameters
        -----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message. If the deletion fails then it is silently ignored.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the message.
        NotFound
            The message was deleted already
        HTTPException
            Deleting the message failed.
        """
        if delay is not None:
            async def delete():
                await asyncio.sleep(delay)
                try:
                    await self._state.http.delete_message(self.channel.id, self.id)
                except HTTPException:
                    pass

            asyncio.ensure_future(delete(), loop=self._state.loop)
        else:
            await self._state.http.delete_message(self.channel.id, self.id)

    async def edit(
            self,
            *,
            content: Any = MISSING,
            embed: Optional[Embed] = MISSING,
            embeds: Sequence[Embed] = MISSING,
            components: List[Union[ActionRow, List[Union[Button, BaseSelect]]]] = MISSING,
            attachments: Sequence[Union[Attachment, File]] = MISSING,
            keep_existing_attachments: bool = False,
            delete_after: Optional[float] = None,
            allowed_mentions: Optional[AllowedMentions] = MISSING,
            suppress_embeds: Optional[bool] = MISSING
    ) -> Message:
        """|coro|

        Edits the message.

        The content must be able to be transformed into a string via ``str(content)``.
        
        .. warning::
            Since API v10, the ``attachments`` **must contain all attachments** that should be present after edit,
            **including retained** and new attachments.
        
        .. versionchanged:: 1.3
            The ``suppress`` keyword-only parameter was added.
        .. versionchanged:: 2.0
            The ``suppress`` keyword-only parameter was renamed to ``suppress_embeds``.
        .. versionchanged:: 2.0
            The ``components`, ``attachments`` and ``keep_existing_attachments`` keyword-only parameters were added.

        Parameters
        -----------
        content: Optional[:class:`str`]
            The new content to replace the message with.
            Could be ``None`` to remove the content.
        embed: Optional[:class:`Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove all embeds.
        embeds: Optional[List[:class:`Embed`]]
            A list containing up to 10 embeds`to send.
            If ``None`` or empty, all embeds will be removed.
            
            If passed, ``embed`` does also count towards the limit of 10 embeds.
        components: List[Union[:class:`~discord.ActionRow`, List[Union[:class:`~discord.Button`, :class:`~discord.BaseSelect`]]]]
            A list of up to five :class:`~discord.ActionRow`s/:class:`list`s
            Each containing up to five :class:`~discord.Button`'s or one :class:`~discord.BaseSelect` like object.
        attachments: List[Union[:class:`Attachment`, :class:`File`]]
            A list containing previous attachments to keep as well as new files to upload.
            You can use ``keep_existing_attachments`` to auto-add the existing attachments to the list.
            If ``None`` or empty, all attachments will be removed.
            
            .. note::
                
                New files will always appear under existing ones.
        keep_existing_attachments: :class:`bool`
            Whether to auto-add existing attachments to ``attachments``, defaults to :obj:`False`.

            .. note::

                Only needed when ``attachments`` are passed, otherwise will be ignored.
        suppress_embeds: :class:`bool`
            Whether to suppress embeds for the message. This removes
            all the embeds if set to ``True``. If set to ``False``
            this brings the embeds back if they were suppressed.
            Requires :attr:`~.Permissions.manage_messages` permissions for messages that aren't from the bot.
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just edited. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.

            .. versionadded:: 1.4

        Raises
        -------
        HTTPException
            Editing the message failed.
        Forbidden
            Tried to suppress a message without permissions or
            edited a message's content or embed that isn't yours.
        """

        if content is not MISSING:
            previous_allowed_mentions = self._state.allowed_mentions
        else:
            previous_allowed_mentions = None

        if keep_existing_attachments and attachments is not MISSING:
            attachments = [*self.attachments, *attachments]

        if suppress_embeds is not MISSING:
            flags = MessageFlags._from_value(self.flags.value)
            flags.suppress_embeds = suppress_embeds
        else:
            flags = MISSING

        with handle_message_parameters(
                content=content,
                flags=flags,
                embed=embed if embed is not None else MISSING,
                embeds=embeds if embeds is not None else MISSING,
                attachments=attachments,
                components=components,
                allowed_mentions=allowed_mentions,
                previous_allowed_mentions=previous_allowed_mentions
        ) as params:
            data = await self._state.http.edit_message(self.channel.id, self.id, params=params)
        self._update(data)

        if delete_after is not None:
            await self.delete(delay=delete_after)
        return self

    @property
    def dict(self):
        return {s: self.__getattribute__(s) for s in self.__slots__ if not s.startswith('_')}

    async def publish(self) -> None:
        """|coro|

        Publishes this message to your announcement channel.

        If the message is not your own then the :attr:`~Permissions.manage_messages`
        permission is needed.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to publish this message.
        HTTPException
            Publishing the message failed.
        """

        await self._state.http.publish_message(self.channel.id, self.id)

    async def pin(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Pins the message.

        You must have the :attr:`~Permissions.manage_messages` permission to do
        this in a non-private channel context.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for pinning the message. Shows up on the audit log.

            .. versionadded:: 1.4

        Raises
        -------
        Forbidden
            You do not have permissions to pin the message.
        NotFound
            The message or channel was not found or deleted.
        HTTPException
            Pinning the message failed, probably due to the channel
            having more than 50 pinned messages.
        """

        await self._state.http.pin_message(self.channel.id, self.id, reason=reason)
        self.pinned = True

    async def unpin(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Unpins the message.

        You must have the :attr:`~Permissions.manage_messages` permission to do
        this in a non-private channel context.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for unpinning the message. Shows up on the audit log.

            .. versionadded:: 1.4

        Raises
        -------
        Forbidden
            You do not have permissions to unpin the message.
        NotFound
            The message or channel was not found or deleted.
        HTTPException
            Unpinning the message failed.
        """

        await self._state.http.unpin_message(self.channel.id, self.id, reason=reason)
        self.pinned = False

    async def add_reaction(self, emoji: Union[Emoji, Reaction, PartialEmoji, str]) -> None:
        """|coro|

        Add a reaction to the message.

        The emoji may be a unicode emoji or a custom guild :class:`Emoji`.

        You must have the :attr:`~Permissions.read_message_history` permission
        to use this. If nobody else has reacted to the message using this
        emoji, the :attr:`~Permissions.add_reactions` permission is required.

        Parameters
        ------------
        emoji: Union[:class:`Emoji`, :class:`Reaction`, :class:`PartialEmoji`, :class:`str`]
            The emoji to react with.

        Raises
        --------
        HTTPException
            Adding the reaction failed.
        Forbidden
            You do not have the proper permissions to react to the message.
        NotFound
            The emoji you specified was not found.
        InvalidArgument
            The emoji parameter is invalid.
        """

        emoji = convert_emoji_reaction(emoji)
        await self._state.http.add_reaction(self.channel.id, self.id, emoji)

    async def remove_reaction(self, emoji: Union[Emoji, Reaction, PartialEmoji, str], member: Snowflake) -> None:
        """|coro|

        Remove a reaction by the member from the message.

        The emoji may be a unicode emoji or a custom guild :class:`Emoji`.

        If the reaction is not your own (i.e. ``member`` parameter is not you) then
        the :attr:`~Permissions.manage_messages` permission is needed.

        The ``member`` parameter must represent a member and meet
        the :class:`abc.Snowflake` abc.

        Parameters
        ------------
        emoji: Union[:class:`Emoji`, :class:`Reaction`, :class:`PartialEmoji`, :class:`str`]
            The emoji to remove.
        member: :class:`abc.Snowflake`
            The member for which to remove the reaction.

        Raises
        --------
        HTTPException
            Removing the reaction failed.
        Forbidden
            You do not have the proper permissions to remove the reaction.
        NotFound
            The member or emoji you specified was not found.
        InvalidArgument
            The emoji parameter is invalid.
        """

        emoji = convert_emoji_reaction(emoji)

        if member.id == self._state.self_id:
            await self._state.http.remove_own_reaction(self.channel.id, self.id, emoji)
        else:
            await self._state.http.remove_reaction(self.channel.id, self.id, emoji, member.id)

    async def clear_reaction(self, emoji: Union[Emoji, Reaction, PartialEmoji, str]) -> None:
        """|coro|

        Clears a specific reaction from the message.

        The emoji may be a unicode emoji or a custom guild :class:`Emoji`.

        You need the :attr:`~Permissions.manage_messages` permission to use this.

        .. versionadded:: 1.3

        Parameters
        -----------
        emoji: Union[:class:`Emoji`, :class:`Reaction`, :class:`PartialEmoji`, :class:`str`]
            The emoji to clear.

        Raises
        --------
        HTTPException
            Clearing the reaction failed.
        Forbidden
            You do not have the proper permissions to clear the reaction.
        NotFound
            The emoji you specified was not found.
        InvalidArgument
            The emoji parameter is invalid.
        """

        emoji = convert_emoji_reaction(emoji)
        await self._state.http.clear_single_reaction(self.channel.id, self.id, emoji)

    async def clear_reactions(self) -> None:
        """|coro|

        Removes all the reactions from the message.

        You need the :attr:`~Permissions.manage_messages` permission to use this.

        Raises
        --------
        HTTPException
            Removing the reactions failed.
        Forbidden
            You do not have the proper permissions to remove all the reactions.
        """
        await self._state.http.clear_reactions(self.channel.id, self.id)

    async def reply(
            self,
            content=None,
            tts: bool = False,
            embed: Optional[Embed] = None,
            embeds: Optional[List[Embed]] = None,
            components: Optional[List[Union[ActionRow, List[Union[Button, BaseSelect]]]]] = None,
            file: Optional[File] = None,
            files: Optional[List[File]] = None,
            stickers: Optional[List[GuildSticker]] = None,
            delete_after: Optional[float] = None,
            nonce: Optional[int] = None,
            allowed_mentions: Optional[AllowedMentions] = None,
            mention_author: Optional[bool] = None,
            suppress_embeds: bool = False,
            suppress_notifications: bool = False
    ) -> Message:
        """|coro|

        A shortcut method to :meth:`.abc.Messageable.send` to reply to the
        :class:`.Message`.

        .. versionadded:: 1.6

        Raises
        --------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message.
        ~discord.InvalidArgument
            The ``files`` list is not of the appropriate size or
            you specified both ``file`` and ``files``.

        Returns
        ---------
        :class:`.Message`
            The message that was sent.
        """

        return await self.channel.send(
            content,
            reference=self,
            tts=tts,
            embed=embed,
            embeds=embeds,
            components=components,
            file=file,
            files=files,
            stickers=stickers,
            delete_after=delete_after,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            mention_author=mention_author,
            suppress_embeds=suppress_embeds,
            suppress_notifications=suppress_notifications
        )

    async def create_thread(
            self,
            name: str,
            auto_archive_duration: Optional[AutoArchiveDuration] = None,
            slowmode_delay: int = 0,
            reason: Optional[str] = None
    ) -> ThreadChannel:
        """|coro|

        Creates a new thread in the channel of the message with this message as the :attr:`~ThreadChannel.starter_message`.

        Parameters
        ----------
        name: :class:`str`
            The name of the thread.
        auto_archive_duration: Optional[:class:`AutoArchiveDuration`]
            Amount of time after that the thread will auto-hide from the channel list
        slowmode_delay: :class:`int`
            Amount of seconds a user has to wait before sending another message (0-21600)
        reason: Optional[:class:`str`]
            The reason for creating the thread. Shows up in the audit log.

        Raises
        ------
        :exc:`TypeError`
            The channel of the message is not a text or news channel,
            or the message has already a thread,
            or ``auto_archive_duration`` is not a valid member of :class:`AutoArchiveDuration`
        :exc:`ValueError`
            The ``name`` is of invalid length
        :exc:`Forbidden`
            The bot is missing permissions to create threads in this channel
        :exc:`HTTPException`
            Creating the thread failed

        Returns
        -------
        :class:`ThreadChannel`
            The created thread on success
        """
        if self.channel.type not in (ChannelType.text, ChannelType.news):
            raise TypeError(
                f'You could not create a thread inside a {self.channel.__class__.__name__}.'
            )
        if self.thread:
            raise TypeError('There is already a thread associated with this message')

        if len(name) > 100 or not name:
            raise ValueError(
                f'The name of the thread must bee between 1-100 characters; got {len(name)}'
            )

        payload = {
            'name': name
        }

        if auto_archive_duration:
            auto_archive_duration = try_enum(
                AutoArchiveDuration, auto_archive_duration
            )  # for the case someone pass a number
            if not isinstance(auto_archive_duration, AutoArchiveDuration):
                raise TypeError(
                    f'auto_archive_duration must be a member of discord.AutoArchiveDuration, not {auto_archive_duration.__class__.__name__!r}'
                )
            payload['auto_archive_duration'] = auto_archive_duration.value

        if slowmode_delay:
            payload['rate_limit_per_user'] = slowmode_delay

        data = await self._state.http.create_thread(self.channel.id, message_id=self.id, payload=payload, reason=reason)
        thread = ThreadChannel(state=self._state, guild=self.guild, data=data)
        self.channel.guild._add_thread(thread)
        self._thread = thread
        return thread

    def to_reference(self, *, fail_if_not_exists: bool = True):
        """Creates a :class:`~discord.MessageReference` from the current message.

        .. versionadded:: 1.6

        Parameters
        ----------
        fail_if_not_exists: :class:`bool`
            Whether replying using the message reference should raise :class:`HTTPException`
            if the message no longer exists or Discord could not fetch the message.

            .. versionadded:: 1.7

        Returns
        ---------
        :class:`~discord.MessageReference`
            The reference to this message.
        """

        return MessageReference.from_message(self, fail_if_not_exists=fail_if_not_exists)

    def to_message_reference_dict(self) -> MessageReference:
        data = {
            'message_id': self.id,
            'channel_id': self.channel.id,
        }

        if self.guild is not None:
            data['guild_id'] = self.guild.id

        return data


def implement_partial_methods(cls):
    msg = Message
    for name in cls._exported_names:
        func = getattr(msg, name)
        setattr(cls, name, func)
    return cls


@implement_partial_methods
class PartialMessage(Hashable):

    """Represents a partial message to aid with working messages when only
    a message and channel ID are present.

    There are two ways to construct this class. The first one is through
    the constructor itself, and the second is via
    :meth:`TextChannel.get_partial_message` or :meth:`DMChannel.get_partial_message`.

    Note that this class is trimmed down and has no rich attributes.

    .. versionadded:: 1.6

    .. container:: operations

        .. describe:: x == y

            Checks if two partial messages are equal.

        .. describe:: x != y

            Checks if two partial messages are not equal.

        .. describe:: hash(x)

            Returns the partial message's hash.

    Attributes
    -----------
    channel: Union[:class:`TextChannel`, :class:`~discord.ThreadChannel`, :class:`DMChannel`]
        The channel associated with this partial message.
    id: :class:`int`
        The message ID.
    """

    __slots__ = ('channel', 'id', '_cs_guild', '_state')

    _exported_names = (
        'jump_url',
        'delete',
        'publish',
        'pin',
        'unpin',
        'add_reaction',
        'remove_reaction',
        'clear_reaction',
        'clear_reactions',
        'reply',
        'create_thread',
        'to_reference',
        'to_message_reference_dict',
    )

    def __init__(self, *, channel: Union[PartialMessageable, Messageable], id: int) -> None:
        if not isinstance(channel, PartialMessageable) and int(channel.type) not in {0, 1, 2, 3, 5, 10, 11, 12, 15}:
            raise TypeError('Expected TextChannel, VoiceChannel, ThreadChannel or DMChannel not %r' % type(channel))

        self.channel: Messageable = channel
        self._state: ConnectionState = channel._state
        self.id = id

    def _update(self, data):
        # This is used for duck typing purposes.
        # Just do nothing with the data.
        pass

    # Also needed for duck typing purposes
    # n.b. not exposed
    pinned = property(None, lambda x, y: ...)

    def __repr__(self) -> str:
        return '<PartialMessage id={0.id} channel={0.channel!r}>'.format(self)

    @property
    def created_at(self):
        """:class:`datetime.datetime`: The partial message's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @utils.cached_slot_property('_cs_guild')
    def guild(self):
        """Optional[:class:`Guild`]: The guild that the partial message belongs to, if applicable."""
        return getattr(self.channel, 'guild', None)

    async def fetch(self) -> Message:
        """|coro|

        Fetches the partial message to a full :class:`Message`.

        Raises
        --------
        NotFound
            The message was not found.
        Forbidden
            You do not have the permissions required to get a message.
        HTTPException
            Retrieving the message failed.

        Returns
        --------
        :class:`Message`
            The full message.
        """

        data = await self._state.http.get_message(self.channel.id, self.id)
        return self._state.create_message(channel=self.channel, data=data)

    async def edit(
            self,
            *,
            content: Any = MISSING,
            embed: Optional[Embed] = MISSING,
            embeds: Sequence[Embed] = MISSING,
            components: List[Union[ActionRow, List[Union[Button, BaseSelect]]]] = MISSING,
            attachments: Sequence[Union[Attachment, File]] = MISSING,
            delete_after: Optional[float] = None,
            allowed_mentions: Optional[AllowedMentions] = MISSING,
            suppress_embeds: bool = MISSING
    ) -> Optional[Message]:
        """|coro|

        Edits the message.

        The content must be able to be transformed into a string via ``str(content)``.

        .. versionchanged:: 1.3
            The ``suppress`` keyword-only parameter was added.
        .. versionchanged:: 2.0
            The ``components`` and ``attachments`` parameters were added.
        .. versionchanged:: 2.0
            The ``suppress`` keyword-only parameter was renamed to ``suppress_embeds``.
        
        .. warning::
            Since API v10, the ``attachments`` (when passed) **must contain all attachments** that should be present after edit,
            **including retained** and new attachments.
            
            As this requires to know the current attachments consider either storing the attachments that were sent with a message or
            using a fetched version of the message to edit it.
        
        Parameters
        -----------
        content: Optional[:class:`str`]
            The new content to replace the message with.
            Could be ``None`` to remove the content.
        embed: Optional[:class:`Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove all embeds.
        embeds: Optional[List[:class:`Embed`]]
            A list containing up to 10 embeds`to send.
            If ``None`` or empty, all embeds will be removed.
            
            If passed, ``embed`` does also count towards the limit of 10 embeds.
        components: List[Union[:class:`~discord.ActionRow`, List[Union[:class:`~discord.Button`, :class:`~discord.BaseSelect`]]]]
            A list of up to five :class:`~discord.ActionRow`s/:class:`list`s
            Each containing up to five :class:`~discord.Button`'s or one :class:`~discord.BaseSelect` like object.
        attachments: List[Union[:class:`Attachment`, :class:`File`]]
            A list containing previous attachments to keep as well as new files to upload.
            
            When  ``None`` or empty, all attachment will be removed.

            .. note::

                New files will always appear under existing ones.
        suppress_embeds: :class:`bool`
            Whether to suppress embeds for the message. This removes
            all the embeds if set to ``True``. If set to ``False``
            this brings the embeds back if they were suppressed.
            Requires :attr:`~.Permissions.manage_messages` for messages that aren't from the bot.
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just edited. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.

        Raises
        -------
        NotFound
            The message was not found.
        HTTPException
            Editing the message failed.
        Forbidden
            Tried to suppress the embeds a message without permissions or
            edited a message's content or embed that isn't yours.

        Returns
        ---------
        Optional[:class:`Message`]
            The message that was edited.
        """

        if content is not MISSING:
            previous_allowed_mentions = self._state.allowed_mentions
        else:
            previous_allowed_mentions = None

        if suppress_embeds is not MISSING:
            flags = MessageFlags._from_value(0)
            flags.suppress_embeds = suppress_embeds
        else:
            flags = MISSING

        with handle_message_parameters(
                content=content,
                flags=flags,
                embed=embed if embed is not None else MISSING,
                embeds=embeds if embeds is not None else MISSING,
                attachments=attachments,
                components=components,
                allowed_mentions=allowed_mentions,
                previous_allowed_mentions=previous_allowed_mentions
        ) as params:
            data = await self._state.http.edit_message(self.channel.id, self.id, params=params)

        if delete_after is not None:
            await self.delete(delay=delete_after)

        if data is not None:
            return self._state.create_message(channel=self.channel, data=data)
