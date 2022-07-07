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

import datetime
import time
import asyncio
from typing import (
    List,
    Dict,
    Union,
    Optional,
    Callable,
    TYPE_CHECKING,
    Any
)

from .object import Object


from .permissions import Permissions
from .enums import ChannelType, try_enum, VoiceRegion, AutoArchiveDuration
from .components import Button, SelectMenu, ActionRow
from .mixins import Hashable
from . import utils, abc
from .file import File
from .mentions import AllowedMentions
from .asset import Asset
from .errors import ClientException, NoMoreItems, InvalidArgument, ThreadIsArchived, MissingPermissionsToCreateThread, \
    Forbidden, HTTPException

if TYPE_CHECKING:
    from .state import ConnectionState
    from .embeds import Embed
    from .sticker import GuildSticker
    from .member import Member
    from .message import Message, MessageReference
    from .guild import Guild


__all__ = (
    'TextChannel',
    'ThreadMember',
    'ThreadChannel',
    'VoiceChannel',
    'StageChannel',
    'DMChannel',
    'CategoryChannel',
    'GroupChannel',
    'ForumPost',
    'ForumChannel',
    'PartialMessageable',
    '_channel_factory'
)

async def _single_delete_strategy(messages):
    for m in messages:
        await m.delete()

class TextChannel(abc.Messageable, abc.GuildChannel, Hashable):
    """Represents a Discord guild text channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    topic: Optional[:class:`str`]
        The channel's topic. ``None`` if it doesn't exist.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this channel. A value of `0` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    """

    __slots__ = ('name', 'id', 'guild', 'topic', '_state', 'nsfw',
                 'category_id', 'position', 'slowmode_delay', '_overwrites',
                 '_type', 'last_message_id', '_threads', 'default_auto_archive_duration')

    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data['id'])
        self._type = data['type']
        self._update(guild, data)
        self._threads = {}

    def __repr__(self):
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('position', self.position),
            ('nsfw', self.nsfw),
            ('news', self.is_news()),
            ('category_id', self.category_id)
        ]
        return '<%s %s>' % (self.__class__.__name__, ' '.join('%s=%r' % t for t in attrs))

    def _update(self, guild, data):
        self.guild = guild
        self.name = data['name']
        self.category_id = utils._get_as_snowflake(data, 'parent_id')
        self.topic = data.get('topic')
        self.position = data['position']
        self.nsfw = data.get('nsfw', False)
        # Does this need coercion into `int`? No idea yet.
        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self._type = data.get('type', self._type)
        # self.threads = data.get('threads', self.threads)
        self.last_message_id = utils._get_as_snowflake(data, 'last_message_id')
        self.default_auto_archive_duration = try_enum(AutoArchiveDuration, data.get('default_auto_archive_duration', 1440))
        self._fill_overwrites(data)

    async def _get_channel(self):
        return self

    @property
    def type(self):
        """:class:`ChannelType`: The channel's Discord type."""
        return try_enum(ChannelType, self._type)

    @staticmethod
    def channel_type():
        return ChannelType.text

    @property
    def _sorting_bucket(self):
        return ChannelType.text.value

    def _add_thread(self, thread):
        self._threads[thread.id] = thread

    def _remove_thread(self, thread):
        return self._threads.pop(thread.id, None)

    def get_thread(self, thread_id):
        return self._threads.get(int(thread_id), None)

    @property
    def threads(self):
        return list(self._threads.values())

    @utils.copy_doc(abc.GuildChannel.permissions_for)
    def permissions_for(self, member: Member) -> Permissions:
        base = super().permissions_for(member)

        # text channels do not have voice related permissions
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base

    @property
    def members(self):
        """List[:class:`Member`]: Returns all members that can see this channel."""
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]

    def is_nsfw(self):
        """:class:`bool`: Checks if the channel is NSFW."""
        return self.nsfw

    def is_news(self):
        """:class:`bool`: Checks if the channel is a news channel."""
        return self._type == ChannelType.news.value

    @property
    def last_message(self):
        """Fetches the last message from this channel in cache.

        The message might not be valid or point to an existing message.

        .. admonition:: Reliable Fetching
            :class: helpful

            For a slightly more reliable method of fetching the
            last message, consider using either :meth:`history`
            or :meth:`fetch_message` with the :attr:`last_message_id`
            attribute.

        Returns
        ---------
        Optional[:class:`Message`]
            The last message in this channel or ``None`` if not found.
        """
        return self._state._get_message(self.last_message_id) if self.last_message_id else None

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        .. versionchanged:: 1.3
            The ``overwrites`` keyword-only parameter was added.

        .. versionchanged:: 1.4
            The ``type`` keyword-only parameter was added.

        Parameters
        ----------
        name: :class:`str`
            The new channel name.
        topic: :class:`str`
            The new channel's topic.
        position: :class:`int`
            The new channel's position.
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing
            category. Defaults to ``False``.
        category: Optional[:class:`CategoryChannel`]
            The new category for this channel. Can be ``None`` to remove the
            category.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
            A value of `0` disables slowmode. The maximum value possible is `21600`.
        type: :class:`ChannelType`
            Change the type of this text channel. Currently, only conversion between
            :attr:`ChannelType.text` and :attr:`ChannelType.news` is supported. This
            is only available to guilds that contain ``NEWS`` in :attr:`Guild.features`.
        reason: Optional[:class:`str`]
            The reason for editing this channel. Shows up on the audit log.
        overwrites: :class:`dict`
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply to the channel.

        Raises
        ------
        InvalidArgument
            If position is less than 0 or greater than the number of channels, or if
            the permission overwrite information is not in proper form.
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """
        await self._edit(options, reason=reason)

    @utils.copy_doc(abc.GuildChannel.clone)
    async def clone(self, *, name=None, reason=None):
        return await self._clone_impl({
            'topic': self.topic,
            'nsfw': self.nsfw,
            'rate_limit_per_user': self.slowmode_delay
        }, name=name, reason=reason)

    async def delete_messages(self, messages):
        """|coro|

        Deletes a list of messages. This is similar to :meth:`Message.delete`
        except it bulk deletes multiple messages.

        As a special case, if the number of messages is 0, then nothing
        is done. If the number of messages is 1 then single message
        delete is done. If it's more than two, then bulk delete is used.

        You cannot bulk delete more than 100 messages or messages that
        are older than 14 days old.

        You must have the :attr:`~Permissions.manage_messages` permission to
        use this.

        Usable only by bot accounts.

        Parameters
        -----------
        messages: Iterable[:class:`abc.Snowflake`]
            An iterable of messages denoting which ones to bulk delete.

        Raises
        ------
        ClientException
            The number of messages to delete was more than 100.
        Forbidden
            You do not have proper permissions to delete the messages or
            you're not using a bot account.
        NotFound
            If single delete, then the message was already deleted.
        HTTPException
            Deleting the messages failed.
        """
        if not isinstance(messages, (list, tuple)):
            messages = list(messages)

        if len(messages) == 0:
            return # do nothing

        if len(messages) == 1:
            message_id = messages[0].id
            await self._state.http.delete_message(self.id, message_id)
            return

        if len(messages) > 100:
            raise ClientException('Can only bulk delete messages up to 100 messages')

        message_ids = [m.id for m in messages]
        await self._state.http.delete_messages(self.id, message_ids)

    async def purge(self,
                    *,
                    limit: Optional[int] = 100,
                    check: Callable = None,
                    before: Optional[Union[abc.Snowflake, datetime.datetime]] = None,
                    after: Optional[Union[abc.Snowflake, datetime.datetime]] = None,
                    around: Optional[Union[abc.Snowflake, datetime.datetime]]=  None,
                    oldest_first: Optional[bool] = False,
                    bulk: Optional[bool] = True):
        """|coro|

        Purges a list of messages that meet the criteria given by the predicate
        ``check``. If a ``check`` is not provided then all messages are deleted
        without discrimination.

        You must have the :attr:`~Permissions.manage_messages` permission to
        delete messages even if they are your own (unless you are a user
        account). The :attr:`~Permissions.read_message_history` permission is
        also needed to retrieve message history.

        Internally, this employs a different number of strategies depending
        on the conditions met such as if a bulk delete is possible or if
        the account is a user bot or not.

        Examples
        ---------

        Deleting bot's messages ::

            def is_me(m):
                return m.author == client.user

            deleted = await channel.purge(limit=100, check=is_me)
            await channel.send('Deleted {} message(s)'.format(len(deleted)))

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of messages to search through. This is not the number
            of messages that will be deleted, though it can be.
        check: Callable[[:class:`Message`], :class:`bool`]
            The function used to check if a message should be deleted.
            It must take a :class:`Message` as its sole parameter.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``before`` in :meth:`history`.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``after`` in :meth:`history`.
        around: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``around`` in :meth:`history`.
        oldest_first: Optional[:class:`bool`]
            Same as ``oldest_first`` in :meth:`history`.
        bulk: :class:`bool`
            If ``True``, use bulk delete. Setting this to ``False`` is useful for mass-deleting
            a bot's own messages without :attr:`Permissions.manage_messages`. When ``True``, will
            fall back to single delete if current account is a user bot (now deprecated), or if messages are
            older than two weeks.

        Raises
        -------
        Forbidden
            You do not have proper permissions to do the actions required.
        HTTPException
            Purging the messages failed.

        Returns
        --------
        List[:class:`.Message`]
            The list of messages that were deleted.
        """

        if check is None:
            check = lambda m: True

        iterator = self.history(limit=limit, before=before, after=after, oldest_first=oldest_first, around=around)
        ret = []
        count = 0

        minimum_time = int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
        strategy = self.delete_messages if bulk else _single_delete_strategy

        while True:
            try:
                msg = await iterator.next()
            except NoMoreItems:
                # no more messages to poll
                if count >= 2:
                    # more than 2 messages -> bulk delete
                    to_delete = ret[-count:]
                    await strategy(to_delete)
                elif count == 1:
                    # delete a single message
                    await ret[-1].delete()

                return ret
            else:
                if count == 100:
                    # we've reached a full 'queue'
                    to_delete = ret[-100:]
                    await strategy(to_delete)
                    count = 0
                    await asyncio.sleep(1)

                if check(msg):
                    if msg.id < minimum_time:
                        # older than 14 days old
                        if count == 1:
                            await ret[-1].delete()
                        elif count >= 2:
                            to_delete = ret[-count:]
                            await strategy(to_delete)

                        count = 0
                        strategy = _single_delete_strategy

                    count += 1
                    ret.append(msg)

    async def webhooks(self):
        """|coro|

        Gets the list of webhooks from this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        Raises
        -------
        Forbidden
            You don't have permissions to get the webhooks.

        Returns
        --------
        List[:class:`Webhook`]
            The webhooks for this channel.
        """

        from .webhook import Webhook
        data = await self._state.http.channel_webhooks(self.id)
        return [Webhook.from_state(d, state=self._state) for d in data]

    async def create_webhook(self, *, name, avatar=None, reason=None):
        """|coro|

        Creates a webhook for this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        .. versionchanged:: 1.1
            Added the ``reason`` keyword-only parameter.

        Parameters
        -------------
        name: :class:`str`
            The webhook's name.
        avatar: Optional[:class:`bytes`]
            A :term:`py:bytes-like object` representing the webhook's default avatar.
            This operates similarly to :meth:`~ClientUser.edit`.
        reason: Optional[:class:`str`]
            The reason for creating this webhook. Shows up in the audit logs.

        Raises
        -------
        HTTPException
            Creating the webhook failed.
        Forbidden
            You do not have permissions to create a webhook.

        Returns
        --------
        :class:`Webhook`
            The created webhook.
        """

        from .webhook import Webhook
        if avatar is not None:
            avatar = utils._bytes_to_base64_data(avatar)

        data = await self._state.http.create_webhook(self.id, name=str(name), avatar=avatar, reason=reason)
        return Webhook.from_state(data, state=self._state)

    async def follow(self, *, destination, reason=None):
        """
        Follows a channel using a webhook.

        Only news channels can be followed.

        .. note::

            The webhook returned will not provide a token to do webhook
            actions, as Discord does not provide it.

        .. versionadded:: 1.3

        Parameters
        -----------
        destination: :class:`TextChannel`
            The channel you would like to follow from.
        reason: Optional[:class:`str`]
            The reason for following the channel. Shows up on the destination guild's audit log.

            .. versionadded:: 1.4

        Raises
        -------
        HTTPException
            Following the channel failed.
        Forbidden
            You do not have the permissions to create a webhook.

        Returns
        --------
        :class:`Webhook`
            The created webhook.
        """

        if not self.is_news():
            raise ClientException('The channel must be a news channel.')

        if not isinstance(destination, TextChannel):
            raise InvalidArgument('Expected TextChannel received {0.__name__}'.format(type(destination)))

        from .webhook import Webhook
        data = await self._state.http.follow_webhook(self.id, webhook_channel_id=destination.id, reason=reason)
        return Webhook._as_follower(data, channel=destination, user=self._state.user)

    def get_partial_message(self, message_id):
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        .. versionadded:: 1.6

        Parameters
        ------------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        ---------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage
        return PartialMessage(channel=self, id=message_id)

    async def create_thread(self,
                            name: str,
                            auto_archive_duration: AutoArchiveDuration = None,
                            private: bool = False,
                            reason: str = None):
        """|coro|

        Creates a new thread in this channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.


        """
        if private is True and not self.permissions_for(self.guild.get_member(self._state.self_id)).create_private_threads:
            raise MissingPermissionsToCreateThread(Permissions.use_private_threads, Permissions.send_messages_in_threads,
                                                   type=ChannelType.private_thread)
        elif private is False and not self.permissions_for(self.guild.get_member(self._state.self_id)).create_public_threads:
            raise MissingPermissionsToCreateThread(Permissions.create_public_threads, Permissions.send_messages_in_threads,
                                                   type=ChannelType.public_thread)
        if len(name) > 100 or len(name) < 1:
            raise AttributeError('The name of the thread must bee between 1-100 characters; got %s' % len(name))
        aad = (self.default_auto_archive_duration if not auto_archive_duration else try_enum(AutoArchiveDuration, auto_archive_duration)).value
        _type = ChannelType.private_thread if private is True else ChannelType.public_thread
        data = await self._state.http.create_thread(self.id, name=name, auto_archive_duration=aad, type=_type, reason=reason)
        thread = ThreadChannel(state=self._state, guild=self.guild, data=data)

        self._threads[thread.id] = thread
        return thread


class ThreadMember:
    def __init__(self, *, state, guild, data):
        self._state = state
        self.guild = guild
        self.thread_id = int(data.get('id', 0))
        self.guild_id = int(data.get('guild_id', guild.id))
        self.id = int(data.get('user_id', self._state.self_id))
        self.joined_at = datetime.datetime.fromisoformat(data.get('join_timestamp'))
        self.flags = int(data.get('flags'))

    @classmethod
    def _from_thread(cls, *, thread, data):
        data['user_id'] = int(data.get('user_id', thread._state.self_id))
        data['id'] = thread.id
        return cls(state=thread._state, guild=thread.guild, data=data)

    @property
    def as_guild_member(self):
        return self.guild.get_member(self.id)

    async def send(self, *args, **kwargs):
        return await self.as_guild_member.send(*args, **kwargs)

    def permissions_in(self, channel):
        return self.as_guild_member.permissions_in(channel)

    @property
    def mention(self):
        return '<@%s>' % self.id


class ThreadChannel(abc.Messageable, Hashable):
    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data['id'])
        self._type = ChannelType.try_value(data['type'])
        self._members = {}
        self._update(guild, data)

    @staticmethod
    def channel_type():
        return ChannelType.public_thread

    @property
    def _sorting_bucket(self):
        return ChannelType.public_thread.value

    def _update(self, guild, data):
        self.guild = guild
        self.parent_id = int(data['parent_id'])
        self.owner_id = int(data['owner_id'])
        if not self._members:
            self._members = {self.owner_id: self.owner}
        self.name = data['name']
        self.message_count = data.get('message_count', 0)
        self.member_count = data.get('member_count', 0)
        self.last_message_id = utils._get_as_snowflake(data, 'last_message_id')
        self.slowmode_delay = int(data.get('rate_limit_per_user', 0))
        self._thread_meta = data.get('thread_metadata', {})
        me = data.get('member', None)
        if me:
            self._members[self._state.self_id] = ThreadMember._from_thread(thread=self, data=me)
        return self

    def _sync_from_members_update(self, data):
        self.member_count = data.get('member_count', self.member_count)
        for new_member in data.get('added_members', []):
            if not self.guild.get_member(int(new_member['user_id'])):
                # This should be only the case if the ``GUILD_MEMBER`` Intent is disabled.
                # But we use the data discord send us to add him to cache.
                # NOTE: This may be removed later
                from .member import Member
                self.guild._add_member(Member(data=new_member, guild=self.guild, state=self._state))
            self._add_member(ThreadMember(state=self._state, guild=self.guild, data=new_member))
        for removed_id in data.get('removed_member_ids', []):
            member = self.get_member(int(removed_id))
            if member:
                self._remove_member(member)

    def _add_self(self, data):
        self._add_member(ThreadMember(state=self._state, guild=self.guild, data=data))

    async def _get_channel(self):
        return self

    def _add_member(self, member):
        self._members[member.id] = member

    def _remove_member(self, member):
        self._members.pop(member.id, None)

    @property
    def starter_message(self):
        original_message = self._state._get_message(self.id)
        return original_message or self.id

    @property
    def type(self):
        return try_enum(ChannelType, self._type)

    @property
    def owner(self):
        return self.guild.get_member(self.owner_id)

    @property
    def members(self):
        return list(self._members.values())

    @property
    def locked(self):
        return self._thread_meta.get('locked', False)

    @property
    def auto_archive_duration(self):
        return try_enum(AutoArchiveDuration, self._thread_meta.get('auto_archive_duration', 0))

    @property
    def archived(self):
        return self._thread_meta.get('archived', True)

    @property
    def last_update_time(self):
        return datetime.datetime.fromisoformat(self._thread_meta.get('archive_timestamp', ''))

    @property
    def me(self):
        """Optional[:class:`ThreadMember`]: The thread member of the bot, or :obj:`None` if he is not a member of the thread."""
        return self.get_member(self._state.self_id)

    @property
    def parent_channel(self) -> TextChannel:
        """:class:`TextChannel`: The parent channel of this tread"""
        return self.guild.get_channel(self.parent_id)

    @property
    def created_at(self) -> Optional[datetime.datetime]:
        """An aware timestamp of when the thread was created in UTC.

        .. note::

            This timestamp only exists for threads created after 9 January 2022, otherwise returns ``None``.

        :return: Optional[:class:`datetime.datetime`]
        """
        return datetime.datetime.fromisoformat(self._thread_meta.get('create_timestamp'))

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the thread."""
        return f'<#{self.id}>'

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the referenced thread."""
        return f'https://discord.com/channels/{self.guild.id}/{self.id}'

    def get_member(self, user_id) -> Optional[ThreadMember]:
        """:class:`ThreadMember`: Returns the member of thread with the given user_id, or :obj:`None` if he is not in this thread."""
        return self._members.get(user_id, None)

    def permissions_for(self, member) -> 'Permissions':
        """Handles permission resolution for the current :class:`~discord.Member`.

        .. note::
            threads inherit their permissions from their parent channel.

        This function takes into consideration the following cases:

        - Guild owner
        - Guild roles
        - Channel overrides
        - Member overrides

        Parameters
        ----------
        member: :class:`~discord.Member`
            The member to resolve permissions for.

        Returns
        -------
        :class:`~discord.Permissions`
            The resolved permissions for the member.
        """
        return self.parent_channel.permissions_for(member)

    def is_nsfw(self):
        """:class:`bool`: Whether the parent channel of this thread has NSFW enabled."""
        return self.parent_channel.is_nsfw()

    async def join(self):
        """|coro|

        Adds the current user to the thread.

        .. note::
            Also requires the thread is **not archived**.

        This will fire a ``thread_members_update`` event.
        """

        if self.archived:
            raise ThreadIsArchived(self.join)
        if self.me:
            raise ClientException('You\'r already a member of this thread.')

        return await self._state.http.add_thread_member(channeL_id=self.id)

    async def leave(self):
        """|coro|

        Removes the current user from the thread.

        .. note::
            Also requires the thread is **not archived**.

        This will fire a ``thread_members_update`` event.
        """

        if self.archived:
            raise ThreadIsArchived(self.leave)
        if not self.me:
            raise ClientException('You cannot leave a thread if you are not a member of it.')

        return await self._state.http.remove_thread_member(channel_id=self.id)

    async def add_member(self, member: Union['Member', int]):
        """|coro|

        Adds another member to the thread.

        .. note::
            Requires the ability to send messages in the thread.\n
            Also requires the thread is **not archived**.

        This will fire a ``thread_members_update`` event.

        Parameters
        ----------
        member: Union[:class:`discord.Member`, :class:`int`]
            The member that should be added to the thread; could be a :class:`discord.Member` or his :attr:`id` (e.g. an :class:`int`)
        """
        if self.archived:
            raise ThreadIsArchived(self.add_member)
        member_id = member if isinstance(member, int) else member.id
        if self.get_member(member_id):
            raise ClientException('The user %s is already a Member of this thread.' % member)

        return await self._state.http.add_thread_member(channeL_id=self.id, member_id=member_id)

    async def remove_member(self, member: Union['Member', int]):
        """|coro|

        Removes a member from the thread.

        .. note::
            This requires the ``MANAGE_THREADS`` permission, or to be the creator of the thread if it is a ``PRIVATE_THREAD``.\n
            Also requires the thread is **not archived**.

        This will fire a ``thread_members_update`` event.

        Parameters
        ----------
        member: Union[:class:`discord.Member`, :class:`int`]
            The member that should be removed from the thread; could be a :class:`discord.Member` or his :attr:`id` (e.g. an :class:`int`)
        """

        if self.archived:
            raise ThreadIsArchived(self.remove_member)
        member_id = member if isinstance(member, int) else member.id
        if not self.get_member(member_id):
            raise ClientException('The user %s is not a member of this thread yet, so you could not remove him.' % member)

        return await self._state.http.remove_thread_member(channel_id=self.id, member_id=member_id)

    async def _fetch_members(self):
        if not self._state._intents.members:
            raise ClientException('You need to enable the GUILD_MEMBERS Intent to use this API-call.')
        r =  await self._state.http.list_thread_members(channel_id=self.id)
        for thread_member in r:
            if not self.get_member(int(thread_member['user_id'])):
                self._add_member(ThreadMember(state=self._state, guild=self.guild, data=thread_member))
        return self.members

    async def delete(self, *, reason=None):
        """|coro|

        Deletes the thread channel.

        You must have :attr:`~Permissions.manage_channels` permission to use this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this tread.
            Shows up on the audit log.

        Raises
        -------
        ~discord.Forbidden
            You do not have proper permissions to delete the thread.
        ~discord.NotFound
            The thread was not found or was already deleted.
        ~discord.HTTPException
            Deleting the thread failed.
        """
        await self._state.http.delete_channel(self.id, reason=reason)

    async def create_invite(self, *, reason=None, **fields):
        """|coro|

        Creates an instant invite from this thread.

        You must have the :attr:`~Permissions.create_instant_invite` permission to
        do this.

        Parameters
        ------------
        max_age: :class:`int`
            How long the invite should last in seconds. If it's 0 then the invite
            doesn't expire. Defaults to ``0``.
        max_uses: :class:`int`
            How many uses the invite could be used for. If it's 0 then there
            are unlimited uses. Defaults to ``0``.
        temporary: :class:`bool`
            Denotes that the invite grants temporary membership
            (i.e. they get kicked after they disconnect). Defaults to ``False``.
        unique: :class:`bool`
            Indicates if a unique invite URL should be created. Defaults to True.
            If this is set to ``False`` then it will return a previously created
            invite.
        reason: Optional[:class:`str`]
            The reason for creating this invite. Shows up on the audit log.

        Raises
        -------
        ~discord.HTTPException
            Invite creation failed.

        Returns
        --------
        :class:`~discord.Invite`
            The invite that was created.
        """
        from .invite import Invite
        data = await self._state.http.create_invite(self.id, reason=reason, **fields)
        return Invite.from_incomplete(data=data, state=self._state)

    async def invites(self):
        """|coro|

        Returns a list of all active instant invites from this thread.

        You must have :attr:`~Permissions.manage_channels` to get this information.

        Raises
        -------
        ~discord.Forbidden
            You do not have proper permissions to get the information.
        ~discord.HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        List[:class:`~discord.Invite`]
            The list of invites that are currently active.
        """
        from .invite import Invite

        state = self._state
        data = await state.http.invites_from_channel(self.id)
        result = []

        for invite in data:
            invite['channel'] = self
            invite['guild'] = self.guild
            result.append(Invite(state=state, data=invite))

        return result


class VocalGuildChannel(abc.Connectable, abc.GuildChannel, Hashable):
    __slots__ = ('name', 'id', 'guild', 'bitrate', 'user_limit',
                 '_state', 'position', '_overwrites', 'category_id',
                 'rtc_region')

    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data['id'])
        self._update(guild, data)

    def _get_voice_client_key(self):
        return self.guild.id, 'guild_id'

    def _get_voice_state_pair(self):
        return self.guild.id, self.id

    def _update(self, guild, data):
        self.guild = guild
        self.name = data['name']
        self.rtc_region = data.get('rtc_region')
        if self.rtc_region:
            self.rtc_region = try_enum(VoiceRegion, self.rtc_region)
        self.category_id = utils._get_as_snowflake(data, 'parent_id')
        self.position = data['position']
        self.bitrate = data.get('bitrate')
        self.user_limit = data.get('user_limit')
        self._fill_overwrites(data)

    @property
    def _sorting_bucket(self):
        return ChannelType.voice.value

    @staticmethod
    def channel_type():
        return ChannelType.voice

    @property
    def members(self):
        """List[:class:`Member`]: Returns all members that are currently inside this voice channel."""
        ret = []
        for user_id, state in self.guild._voice_states.items():
            if state.channel and state.channel.id == self.id:
                member = self.guild.get_member(user_id)
                if member is not None:
                    ret.append(member)
        return ret

    @property
    def voice_states(self):
        """Returns a mapping of member IDs who have voice states in this channel.

        .. versionadded:: 1.3

        .. note::

            This function is intentionally low level to replace :attr:`members`
            when the member cache is unavailable.

        Returns
        --------
        Mapping[:class:`int`, :class:`VoiceState`]
            The mapping of member ID to a voice state.
        """
        return {key: value for key, value in self.guild._voice_states.items() if value.channel.id == self.id}

    @utils.copy_doc(abc.GuildChannel.permissions_for)
    def permissions_for(self, member):
        base = super().permissions_for(member)

        # voice channels cannot be edited by people who can't connect to them,
        # It also implicitly denies all other voice perms
        if not base.connect:
            denied = Permissions.voice()
            denied.update(manage_channels=True, manage_roles=True)
            base.value &= ~denied.value
        return base


class VoiceChannel(VocalGuildChannel, abc.Messageable):
    """Represents a Discord guild voice channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a voice channel.
    rtc_region: Optional[:class:`VoiceRegion`]
        The region for the voice channel's voice communication.
        A value of ``None`` indicates automatic voice region detection.

        .. versionadded:: 1.7
    """

    __slots__ = ('last_message_id',)

    def __repr__(self):
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('rtc_region', self.rtc_region),
            ('position', self.position),
            ('bitrate', self.bitrate),
            ('user_limit', self.user_limit),
            ('category_id', self.category_id)
        ]
        return '<%s %s>' % (self.__class__.__name__, ' '.join('%s=%r' % t for t in attrs))

    @staticmethod
    def channel_type():
        return ChannelType.voice

    async def _get_channel(self):
        return self

    @property
    def type(self):
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.voice

    @utils.copy_doc(abc.GuildChannel.clone)
    async def clone(self, *, name=None, reason=None):
        return await self._clone_impl({
            'bitrate': self.bitrate,
            'user_limit': self.user_limit
        }, name=name, reason=reason)


    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        .. versionchanged:: 1.3
            The ``overwrites`` keyword-only parameter was added.

        Parameters
        ----------
        name: :class:`str`
            The new channel's name.
        bitrate: :class:`int`
            The new channel's bitrate.
        user_limit: :class:`int`
            The new channel's user limit.
        position: :class:`int`
            The new channel's position.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing
            category. Defaults to ``False``.
        category: Optional[:class:`CategoryChannel`]
            The new category for this channel. Can be ``None`` to remove the
            category.
        reason: Optional[:class:`str`]
            The reason for editing this channel. Shows up on the audit log.
        overwrites: :class:`dict`
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply to the channel.
        rtc_region: Optional[:class:`VoiceRegion`]
            The new region for the voice channel's voice communication.
            A value of ``None`` indicates automatic voice region detection.

            .. versionadded:: 1.7

        Raises
        ------
        InvalidArgument
            If the permission overwrite information is not in proper form.
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """

        await self._edit(options, reason=reason)


class StageChannel(VocalGuildChannel):
    """Represents a Discord guild stage channel.

    .. versionadded:: 1.7

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    topic: Optional[:class:`str`]
        The channel's topic. ``None`` if it isn't set.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a stage channel.
    rtc_region: Optional[:class:`VoiceRegion`]
        The region for the stage channel's voice communication.
        A value of ``None`` indicates automatic voice region detection.
    """
    __slots__ = ('topic',)

    def __repr__(self):
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('topic', self.topic),
            ('rtc_region', self.rtc_region),
            ('position', self.position),
            ('bitrate', self.bitrate),
            ('user_limit', self.user_limit),
            ('category_id', self.category_id)
        ]
        return '<%s %s>' % (self.__class__.__name__, ' '.join('%s=%r' % t for t in attrs))

    def _update(self, guild, data):
        super()._update(guild, data)
        self.topic = data.get('topic')

    @staticmethod
    def channel_type():
        return ChannelType.stage_voice

    @property
    def requesting_to_speak(self):
        """List[:class:`Member`]: A list of members who are requesting to speak in the stage channel."""
        return [member for member in self.members if member.voice.requested_to_speak_at is not None]

    @property
    def type(self):
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.stage_voice

    @utils.copy_doc(abc.GuildChannel.clone)
    async def clone(self, *, name=None, reason=None):
        return await self._clone_impl({
            'topic': self.topic,
        }, name=name, reason=reason)

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        Parameters
        ----------
        name: :class:`str`
            The new channel's name.
        topic: :class:`str`
            The new channel's topic.
        position: :class:`int`
            The new channel's position.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing
            category. Defaults to ``False``.
        category: Optional[:class:`CategoryChannel`]
            The new category for this channel. Can be ``None`` to remove the
            category.
        reason: Optional[:class:`str`]
            The reason for editing this channel. Shows up on the audit log.
        overwrites: :class:`dict`
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply to the channel.
        rtc_region: Optional[:class:`VoiceRegion`]
            The new region for the stage channel's voice communication.
            A value of ``None`` indicates automatic voice region detection.

        Raises
        ------
        InvalidArgument
            If the permission overwrite information is not in proper form.
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """

        await self._edit(options, reason=reason)

class CategoryChannel(abc.GuildChannel, Hashable):
    """Represents a Discord channel category.

    These are useful to group channels to logical compartments.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the category's hash.

        .. describe:: str(x)

            Returns the category's name.

    Attributes
    -----------
    name: :class:`str`
        The category name.
    guild: :class:`Guild`
        The guild the category belongs to.
    id: :class:`int`
        The category channel ID.
    position: :class:`int`
        The position in the category list. This is a number that starts at 0. e.g. the
        top category is position 0.
    """

    __slots__ = ('name', 'id', 'guild', 'nsfw', '_state', 'position', '_overwrites', 'category_id')

    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data['id'])
        self._update(guild, data)

    def __repr__(self):
        return '<CategoryChannel id={0.id} name={0.name!r} position={0.position} nsfw={0.nsfw}>'.format(self)

    def _update(self, guild, data):
        self.guild = guild
        self.name = data['name']
        self.category_id = utils._get_as_snowflake(data, 'parent_id')
        self.nsfw = data.get('nsfw', False)
        self.position = data['position']
        self._fill_overwrites(data)

    @staticmethod
    def channel_type():
        return ChannelType.category

    @property
    def _sorting_bucket(self):
        return ChannelType.category.value

    @property
    def type(self):
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.category

    @property
    def jump_url(self):
        """:class:`str`: Returns an empty string as you can't jump to a category."""
        return ''

    def is_nsfw(self):
        """:class:`bool`: Checks if the category is NSFW."""
        return self.nsfw

    @utils.copy_doc(abc.GuildChannel.clone)
    async def clone(self, *, name=None, reason=None):
        return await self._clone_impl({
            'nsfw': self.nsfw
        }, name=name, reason=reason)

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        .. versionchanged:: 1.3
            The ``overwrites`` keyword-only parameter was added.

        Parameters
        ----------
        name: :class:`str`
            The new category's name.
        position: :class:`int`
            The new category's position.
        nsfw: :class:`bool`
            To mark the category as NSFW or not.
        reason: Optional[:class:`str`]
            The reason for editing this category. Shows up on the audit log.
        overwrites: :class:`dict`
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply to the channel.

        Raises
        ------
        InvalidArgument
            If position is less than 0 or greater than the number of categories.
        Forbidden
            You do not have permissions to edit the category.
        HTTPException
            Editing the category failed.
        """

        await self._edit(options=options, reason=reason)

    @utils.copy_doc(abc.GuildChannel.move)
    async def move(self, **kwargs):
        kwargs.pop('category', None)
        await super().move(**kwargs)

    @property
    def channels(self):
        """List[:class:`abc.GuildChannel`]: Returns the channels that are under this category.

        These are sorted by the official Discord UI, which places voice channels below the text channels.
        """
        def comparator(channel):
            return (not isinstance(channel, TextChannel), channel.position)

        ret = [c for c in self.guild.channels if c.category_id == self.id]
        ret.sort(key=comparator)
        return ret

    @property
    def text_channels(self):
        """List[:class:`TextChannel`]: Returns the text channels that are under this category."""
        ret = [c for c in self.guild.channels
            if c.category_id == self.id
            and isinstance(c, TextChannel)]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

    @property
    def voice_channels(self):
        """List[:class:`VoiceChannel`]: Returns the voice channels that are under this category."""
        ret = [c for c in self.guild.channels
            if c.category_id == self.id
            and isinstance(c, VoiceChannel)]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

    @property
    def stage_channels(self):
        """List[:class:`StageChannel`]: Returns the voice channels that are under this category.

        .. versionadded:: 1.7
        """
        ret = [c for c in self.guild.channels
            if c.category_id == self.id
            and isinstance(c, StageChannel)]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

    async def create_text_channel(self, name, *, overwrites=None, reason=None, **options):
        """|coro|

        A shortcut method to :meth:`Guild.create_text_channel` to create a :class:`TextChannel` in the category.

        Returns
        -------
        :class:`TextChannel`
            The channel that was just created.
        """
        return await self.guild.create_text_channel(name, overwrites=overwrites, category=self, reason=reason, **options)

    async def create_voice_channel(self, name, *, overwrites=None, reason=None, **options):
        """|coro|

        A shortcut method to :meth:`Guild.create_voice_channel` to create a :class:`VoiceChannel` in the category.

        Returns
        -------
        :class:`VoiceChannel`
            The channel that was just created.
        """
        return await self.guild.create_voice_channel(name, overwrites=overwrites, category=self, reason=reason, **options)

    async def create_stage_channel(self, name, *, overwrites=None, reason=None, **options):
        """|coro|

        A shortcut method to :meth:`Guild.create_stage_channel` to create a :class:`StageChannel` in the category.

        .. versionadded:: 1.7

        Returns
        -------
        :class:`StageChannel`
            The channel that was just created.
        """
        return await self.guild.create_stage_channel(name, overwrites=overwrites, category=self, reason=reason, **options)


class DMChannel(abc.Messageable, Hashable):
    """Represents a Discord direct message channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns a string representation of the channel

    Attributes
    ----------
    recipient: :class:`User`
        The user you are participating with in the direct message channel.
    me: :class:`ClientUser`
        The user presenting yourself.
    id: :class:`int`
        The direct message channel ID.
    """

    __slots__ = ('id', 'recipient', 'last_message_id', 'me', '_state')

    def __init__(self, *, me, state, data):
        self._state = state
        self.recipient = state.store_user(data['recipients'][0])
        self.me = me
        self.id = int(data['id'])

    async def _get_channel(self):
        return self

    def __str__(self):
        return 'Direct Message with %s' % self.recipient

    def __repr__(self):
        return '<DMChannel id={0.id} recipient={0.recipient!r}>'.format(self)

    @staticmethod
    def channel_type():
        return ChannelType.private

    @property
    def type(self):
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.private

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the direct message channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def permissions_for(self, user=None):
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with other channel types.

        Actual direct messages do not really have the concept of permissions.

        This returns all the Text related permissions set to ``True`` except:

        - :attr:`~Permissions.send_tts_messages`: You cannot send TTS messages in a DM.
        - :attr:`~Permissions.manage_messages`: You cannot delete others messages in a DM.

        Parameters
        -----------
        user: :class:`User`
            The user to check permissions for. This parameter is ignored
            but kept for compatibility.

        Returns
        --------
        :class:`Permissions`
            The resolved permissions.
        """

        base = Permissions.text()
        base.send_tts_messages = False
        base.manage_messages = False
        return base

    def get_partial_message(self, message_id):
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        .. versionadded:: 1.6

        Parameters
        ------------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        ---------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage
        return PartialMessage(channel=self, id=message_id)


class GroupChannel(abc.Messageable, Hashable):
    """Represents a Discord group channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns a string representation of the channel

    Attributes
    ----------
    recipients: List[:class:`User`]
        The users you are participating with in the group channel.
    me: :class:`ClientUser`
        The user presenting yourself.
    id: :class:`int`
        The group channel ID.
    owner: :class:`User`
        The user that owns the group channel.
    icon: Optional[:class:`str`]
        The group channel's icon hash if provided.
    name: Optional[:class:`str`]
        The group channel's name if provided.
    """

    __slots__ = ('id', 'recipients', 'owner', 'icon', 'name', 'last_message_id', 'me', '_state')

    def __init__(self, *, me, state, data):
        self._state = state
        self.id = int(data['id'])
        self.me = me
        self._update_group(data)

    def _update_group(self, data):
        owner_id = utils._get_as_snowflake(data, 'owner_id')
        self.icon = data.get('icon')
        self.name = data.get('name')

        try:
            self.recipients = [self._state.store_user(u) for u in data['recipients']]
        except KeyError:
            pass

        if owner_id == self.me.id:
            self.owner = self.me
        else:
            self.owner = utils.find(lambda u: u.id == owner_id, self.recipients)

    async def _get_channel(self):
        return self

    def __str__(self):
        if self.name:
            return self.name

        if len(self.recipients) == 0:
            return 'Unnamed'

        return ', '.join(map(lambda x: x.name, self.recipients))

    def __repr__(self):
        return '<GroupChannel id={0.id} name={0.name!r}>'.format(self)

    @staticmethod
    def channel_type():
        return ChannelType.group

    @property
    def type(self):
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.group

    @property
    def icon_url(self):
        """:class:`Asset`: Returns the channel's icon asset if available.

        This is equivalent to calling :meth:`icon_url_as` with
        the default parameters ('webp' format and a size of 1024).
        """
        return self.icon_url_as()

    def icon_url_as(self, *, format='webp', size=1024):
        """Returns an :class:`Asset` for the icon the channel has.

        The format must be one of 'webp', 'jpeg', 'jpg' or 'png'.
        The size must be a power of 2 between 16 and 4096.

        .. versionadded:: 2.0

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the icon to. Defaults to 'webp'.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_icon(self._state, self, 'channel', format=format, size=size)

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def permissions_for(self, user):
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with other channel types.

        Actual direct messages do not really have the concept of permissions.

        This returns all the Text related permissions set to ``True`` except:

        - :attr:`~Permissions.send_tts_messages`: You cannot send TTS messages in a DM.
        - :attr:`~Permissions.manage_messages`: You cannot delete others messages in a DM.

        This also checks the kick_members permission if the user is the owner.

        Parameters
        -----------
        user: :class:`User`
            The user to check permissions for.

        Returns
        --------
        :class:`Permissions`
            The resolved permissions for the user.
        """

        base = Permissions.text()
        base.send_tts_messages = False
        base.manage_messages = False
        base.mention_everyone = True

        if user.id == self.owner.id:
            base.kick_members = True

        return base

    @utils.deprecated()
    async def add_recipients(self, *recipients):
        r"""|coro|

        Adds recipients to this group.

        A group can only have a maximum of 10 members.
        Attempting to add more ends up in an exception. To
        add a recipient to the group, you must have a relationship
        with the user of type :attr:`RelationshipType.friend`.

        .. deprecated:: 1.7

        Parameters
        -----------
        \*recipients: :class:`User`
            An argument list of users to add to this group.

        Raises
        -------
        HTTPException
            Adding a recipient to this group failed.
        """

        # TODO: wait for the corresponding WS event

        req = self._state.http.add_group_recipient
        for recipient in recipients:
            await req(self.id, recipient.id)

    @utils.deprecated()
    async def remove_recipients(self, *recipients):
        r"""|coro|

        Removes recipients from this group.

        .. deprecated:: 1.7

        Parameters
        -----------
        \*recipients: :class:`User`
            An argument list of users to remove from this group.

        Raises
        -------
        HTTPException
            Removing a recipient from this group failed.
        """

        # TODO: wait for the corresponding WS event

        req = self._state.http.remove_group_recipient
        for recipient in recipients:
            await req(self.id, recipient.id)

    @utils.deprecated()
    async def edit(self, **fields):
        """|coro|

        Edits the group.

        .. deprecated:: 1.7

        Parameters
        -----------
        name: Optional[:class:`str`]
            The new name to change the group to.
            Could be ``None`` to remove the name.
        icon: Optional[:class:`bytes`]
            A :term:`py:bytes-like object` representing the new icon.
            Could be ``None`` to remove the icon.

        Raises
        -------
        HTTPException
            Editing the group failed.
        """

        try:
            icon_bytes = fields['icon']
        except KeyError:
            pass
        else:
            if icon_bytes is not None:
                fields['icon'] = utils._bytes_to_base64_data(icon_bytes)

        data = await self._state.http.edit_group(self.id, **fields)
        self._update_group(data)

    async def leave(self):
        """|coro|

        Leave the group.

        If you are the only one in the group, this deletes it as well.

        Raises
        -------
        HTTPException
            Leaving the group failed.
        """

        await self._state.http.leave_group(self.id)


class ForumPost(ThreadChannel):
    def __init__(self, *, state, guild, data: dict) -> None:
        self._state = state
        self.guild = guild
        self.id = int(data['id'])
        self._applied_tags: utils.SnowflakeList = utils.SnowflakeList(map(int, data.get("applied_tags",[])))
        super().__init__(state=self._state, guild=self.guild, data=data)

    def get_tags(self) -> List[ForumTag]:
        # TODO: implement this to get the tags from the parent and return them
        return self._applied_tags


class ForumTag(Hashable):
    def __init__(self, *, state, guild, data):
        self._state = state
        self.guild = guild
        self.id = int(data['id'])
        self.emoji_id = data.get("emoji_id")
        self.emoji_name = data.get("emoji_name")
        self.moderated = data.get("moderated")
        self.name = data.get("name")

    def __repr__(self):
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('emoji_id', self.emoji_id),
            ('emoji_name', self.emoji_name),
            ('moderated', self.moderated)
        ]
        return '<%s %s>' % (self.__class__.__name__, ' '.join('%s=%r' % t for t in attrs))

    def __str__(self):
        return self.__repr__()


class ForumChannel(abc.GuildChannel, Hashable):
    """Represents a Discord guild forum channel.

        .. container:: operations

            .. describe:: x == y

                Checks if two channels are equal.

            .. describe:: x != y

                Checks if two channels are not equal.

            .. describe:: hash(x)

                Returns the channel's hash.

            .. describe:: str(x)

                Returns the channel's name.

        Attributes
        -----------
        name: :class:`str`
            The channel name.
        guild: :class:`Guild`
            The guild the channel belongs to.
        id: :class:`int`
            The channel ID.
        category_id: Optional[:class:`int`]
            The category channel ID this channel belongs to, if applicable.
        topic: Optional[:class:`str`]
            The channel's topic. ``None`` if it doesn't exist.
        position: :class:`int`
            The position in the channel list. This is a number that starts at 0. e.g. the
            top channel is position 0.
        last_post_id: Optional[:class:`int`]
            The ID of the last post that was createt in this forum, this may
            *not* point to an existing or valid post.
        slowmode_delay: :class:`int`
            The number of seconds a member must wait between sending messages
            in posts inside this channel. A value of `0` denotes that it is disabled.
            Bots and users with :attr:`~Permissions.manage_channels` or
            :attr:`~Permissions.manage_messages` bypass slowmode.
        """

    __slots__ = ('name', 'id', 'guild', 'topic', '_state', 'nsfw',
                 'category_id', 'position', 'slowmode_delay', '_overwrites',
                 '_type', 'last_message_id', '_threads', 'default_auto_archive_duration',
                 '_posts', '_tags', 'last_post_id')


    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data['id'])
        self._type = data["type"]
        self._posts: Dict[int, ForumPost] = {}
        self._tags: Dict[int, ForumTag] = {}
        self.last_post_id: Optional[int] = None
        self._update(guild, data)

    def __repr__(self):
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('position', self.position),
            ('nsfw', self.nsfw),
            ('category_id', self.category_id)
        ]
        return '<%s %s>' % (self.__class__.__name__, ' '.join('%s=%r' % t for t in attrs))

    def _update(self, guild, data):
        self.guild = guild
        self.name = data['name']
        self.category_id = utils._get_as_snowflake(data, 'parent_id')
        self.topic = data.get('topic')
        self.position = data['position']
        self.nsfw = data.get('nsfw', False)
        # Does this need coercion into `int`? No idea yet.
        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self._type = data.get('type', self._type)
        self.last_post_id = utils._get_as_snowflake(data, 'last_message_id')
        self.default_auto_archive_duration = try_enum(AutoArchiveDuration,
                                                      data.get('default_auto_archive_duration', 1440))
        self._fill_overwrites(data)
        self._fill_tags(data)

    def _fill_tags(self, data: Dict[str, Any]) -> None:
        tags = data.get('available_tags', [])
        guild = self.guild
        state = self._state
        for t in tags:
            self._tags[int(t['id'])] = ForumTag(state=state, guild=guild, data=t)

    async def _get_channel(self):
        return self

    @property
    def type(self) -> ChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return try_enum(ChannelType, self._type)

    @staticmethod
    def channel_type() -> ChannelType.forum_channel:
        return ChannelType.forum_channel

    @property
    def _sorting_bucket(self):
        return ChannelType.forum_channel.value

    def _add_post(self, post: ForumPost) -> None:
        self._posts[post.id] = post

    def _remove_post(self, post: ForumPost) -> Optional[ForumPost]:
        return self._posts.pop(post.id, None)

    def get_post(self, post_id: int) -> Optional[ForumPost]:
        return self._posts.get(int(post_id), None)

    @property
    def posts(self) -> List[ForumPost]:
        return list(self._posts.values())

    def _add_tag(self, tag: ForumTag) -> None:
        self._tags[tag.id] = tag

    def _remove_tag(self, tag: ForumTag) -> None:
        return self._tags.pop(tag.id, None)

    def get_tag(self, tag_id: int) -> Optional[ForumTag]:
        return self._tags.get(tag_id, None)

    @property
    def available_tags(self) -> List[ForumTag]:
        return list(self._tags.values())

    @utils.copy_doc(abc.GuildChannel.permissions_for)
    def permissions_for(self, member: Member) -> Permissions:
        base = super().permissions_for(member)

        # forum channels do not have voice related permissions
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base

    @property
    def members(self):
        """List[:class:`Member`]: Returns all members that can see this channel."""
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]

    def is_nsfw(self) -> bool:
        """:class:`bool`: Checks if the channel is NSFW."""
        return self.nsfw

    @property
    def last_post(self) -> Optional[ForumPost]:
        """Fetches the last post from this channel in cache.

        The post might not be valid or point to an existing post.

        Returns
        ---------
        Optional[:class:`ForumPost`]
            The last post in this channel or ``None`` if not found.
        """
        return self._posts.get(self.last_post_id) if self.last_post_id else None

    async def edit(self, *, reason=None, **options) -> None:
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        Parameters
        ----------
        name: :class:`str`
            The new channel name.
        topic: :class:`str`
            The new channel's topic.
        position: :class:`int`
            The new channel's position.
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing
            category. Defaults to ``False``.
        category: Optional[:class:`CategoryChannel`]
            The new category for this channel. Can be ``None`` to remove the
            category.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
            A value of `0` disables slowmode. The maximum value possible is `21600`.
        type: :class:`ChannelType`
            Change the type of this text channel. Currently, only conversion between
            :attr:`ChannelType.text` and :attr:`ChannelType.news` is supported. This
            is only available to guilds that contain ``NEWS`` in :attr:`Guild.features`.
        reason: Optional[:class:`str`]
            The reason for editing this channel. Shows up on the audit log.
        overwrites: :class:`dict`
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply to the channel.

        Raises
        ------
        InvalidArgument
            If position is less than 0 or greater than the number of channels, or if
            the permission overwrite information is not in proper form.
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """
        await self._edit(options, reason=reason)

    @utils.copy_doc(abc.GuildChannel.clone)
    async def clone(self, *, name=None, reason=None) -> ForumChannel:
        return await self._clone_impl({
            'topic': self.topic,
            'nsfw': self.nsfw,
            'rate_limit_per_user': self.slowmode_delay
        }, name=name, reason=reason)

    async def webhooks(self):
        """|coro|

        Gets the list of webhooks from this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        Raises
        -------
        Forbidden
            You don't have permissions to get the webhooks.

        Returns
        --------
        List[:class:`Webhook`]
            The webhooks for this channel.
        """


        data = await self._state.http.channel_webhooks(self.id)
        return [discord.Webhook.from_state(d, state=self._state) for d in data]

    async def create_webhook(self, *, name, avatar=None, reason=None):
        """|coro|

        Creates a webhook for this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        .. versionchanged:: 1.1
            Added the ``reason`` keyword-only parameter.

        Parameters
        -------------
        name: :class:`str`
            The webhook's name.
        avatar: Optional[:class:`bytes`]
            A :term:`py:bytes-like object` representing the webhook's default avatar.
            This operates similarly to :meth:`~ClientUser.edit`.
        reason: Optional[:class:`str`]
            The reason for creating this webhook. Shows up in the audit logs.

        Raises
        -------
        HTTPException
            Creating the webhook failed.
        Forbidden
            You do not have permissions to create a webhook.

        Returns
        --------
        :class:`Webhook`
            The created webhook.
        """

        from .webhook import Webhook
        if avatar is not None:
            avatar = utils._bytes_to_base64_data(avatar)

        data = await self._state.http.create_webhook(self.id, name=str(name), avatar=avatar, reason=reason)
        return Webhook.from_state(data, state=self._state)

    async def create_post(self,
                            name: str,
                            content: Any = None,
                            embed: Optional[Embed] = None,
                            embeds: Optional[List[Embed]] = None,
                            components: Optional[List[Union[ActionRow, List[Union[Button, SelectMenu]]]]] = None,
                            file: Optional[File] = None,
                            files: Optional[List[File]] = None,
                            stickers: Optional[List[GuildSticker]] = None,
                            allowed_mentions: Optional[AllowedMentions] = None,
                            supress: bool = False,
                            auto_archive_duration: AutoArchiveDuration = None,
                            reason: str = None) -> ForumPost:
        """|coro|

        Creates a new post in this forum.

        You must have the :attr:`~Permissions.create_posts` permission to
        use this.


        """

        state = self._state

        content = str(content) if content is not None else None
        embed_list = []

        if embed is not None:
            embed_list.append(embed.to_dict())

        if embeds:
            embed_list.extend([e.to_dict() for e in embeds])

        embeds = embed_list

        if len(embeds) > 10:
            raise InvalidArgument(f'The maximum number of embeds that can be send with a message is 10, got: {len(embeds)}')

        if components:
            _components = []
            for component in ([components] if not isinstance(components, list) else components):
                if isinstance(component, (Button, SelectMenu)):
                    _components.extend(ActionRow(component).to_dict())
                elif isinstance(component, ActionRow):
                    _components.extend(component.to_dict())
                elif isinstance(component, list):
                    _components.extend(ActionRow(*[obj for obj in component if isinstance(obj, (Button, SelectMenu))]).to_dict())
            components = _components

        if allowed_mentions is not None:
            if state.allowed_mentions is not None:
                allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
            else:
                allowed_mentions = allowed_mentions.to_dict()
        else:
            allowed_mentions = state.allowed_mentions and state.allowed_mentions.to_dict()

        if file is not None and files is not None:
            raise InvalidArgument('cannot pass both file and files parameter to send()')

        message = {
            'content': content,
            'embeds': embeds,
            'allowed_mentions': allowed_mentions,
            'components' : components,
            'sticker_ids': [str(sticker.id) for sticker in stickers] if stickers else None,
            'attachments': [{'id': index,
                             'description': file.description,
                             'filename': file.filename
                             } for index, file in enumerate(files)] if files and len(files) else None,
            'flags': 4 if supress else None
        }

        if len(name) > 100 or len(name) < 1:
            raise AttributeError('The name of the thread must bee between 1-100 characters; got %s' % len(name))
        aad = (self.default_auto_archive_duration if not auto_archive_duration else try_enum(AutoArchiveDuration,
                                                                                             auto_archive_duration)).value
        _type = ChannelType.public_thread
        data = await self._state.http.create_post(self.id, name=name, message = message, auto_archive_duration=aad,
                                                    reason=reason)
        post = ForumPost(state=self._state, guild=self.guild, data=data)

        self._posts[post.id] = post
        # TODO: wait for ws event
        return post

    def _remove_thread(self, thread: ThreadChannel) -> None:
        self._posts.pop(thread.id, None)


class PartialMessageable(abc.Messageable, Hashable):
    """Represents a partial messageable to aid with working messageable channels when
    only a channel ID are present.
    The only way to construct this class is through :meth:`Client.get_partial_messageable`.
    Note that this class is trimmed down and has no rich attributes.
    .. container:: operations
        .. describe:: x == y
            Checks if two partial messageables are equal.
        .. describe:: x != y
            Checks if two partial messageables are not equal.
        .. describe:: hash(x)
            Returns the partial messageable's hash.
    Attributes
    -----------
    id: :class:`int`
        The channel ID associated with this partial messageable.
    type: Optional[:class:`ChannelType`]
        The channel type associated with this partial messageable, if given.
    """

    def __init__(self, state: 'ConnectionState', id: int, type: Optional[ChannelType] = None, *, guild_id: int = None):
        self._state: 'ConnectionState' = state
        self.id: int = id
        self.guild_id: Optional[int] = guild_id
        self.type: Optional[ChannelType] = type
    
    def __repr__(self) -> str:
        return f'<PartialMessageable id={self.id} type={self.type!r}{f" guild_id={self.guild_id}" if self.guild_id else ""}>'

    async def _get_channel(self) -> 'PartialMessageable':
        return self

    @property
    def guild(self) -> Optional['Guild']:
        """Optional[:class:`~discord.Guild`]: The guild this partial messageable belongs to if any."""
        return self._state._get_guild(self.guild_id)

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns an url that allows the client to jump to the partial messageable (channel)"""
        if self.guild_id:
            return f'https://discord.com/channels/{self.guild_id}/{self.id}'
        return f'https://discord.com/channels/@me/{self.id}'

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def permissions_for(self, obj: Any = None) -> Permissions:
        """Handles permission resolution for a :class:`User`.
        This function is there for compatibility with other channel types.
        Since partial messageables cannot reasonably have the concept of
        permissions, this will always return :meth:`Permissions.none`.

        Parameters
        -----------
        obj: :class:`User`
            The user to check permissions for. This parameter is ignored
            but kept for compatibility with other ``permissions_for`` methods.

        Returns
        --------
        :class:`Permissions`
            The resolved permissions.
        """

        return Permissions.none()

    def get_partial_message(self, message_id: int) -> 'PartialMessageable':
        """Creates a :class:`PartialMessage` from the message ID.
        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        Parameters
        ------------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        ---------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)

def _channel_factory(channel_type):
    value = try_enum(ChannelType, channel_type)
    if value is ChannelType.text:
        return TextChannel, value
    elif value is ChannelType.voice:
        return VoiceChannel, value
    elif value is ChannelType.private:
        return DMChannel, value
    elif value is ChannelType.category:
        return CategoryChannel, value
    elif value is ChannelType.group:
        return GroupChannel, value
    elif value is ChannelType.news:
        return TextChannel, value
    elif value is ChannelType.stage_voice:
        return StageChannel, value
    elif value is ChannelType.public_thread:
        return ThreadChannel, value
    elif value is ChannelType.private_thread:
        return ThreadChannel, value
    elif value is ChannelType.forum_channel:
        return ForumChannel, value
    else:
        return None, value

def _check_channel_type(obj, types) -> bool:
    """Just something to check channel instances without circular imports."""
    types = tuple([_channel_factory(t)[0] for t in types])
    return isinstance(obj, types)