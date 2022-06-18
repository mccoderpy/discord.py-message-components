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
from typing_extensions import Literal
from typing import Optional, Union, TYPE_CHECKING

from datetime import datetime

from .mixins import Hashable
from .errors import InvalidArgument
from .utils import _get_as_snowflake, cached_slot_property, _bytes_to_base64_data
from .enums import PrivacyLevel, EventEntityType, EventStatus, try_enum
from .iterators import EventUsersIterator


if TYPE_CHECKING:
    from .state import ConnectionState
    from .guild import Guild
    from .user import User
    from .channel import StageChannel, VoiceChannel


class GuildScheduledEvent(Hashable):
    def __init__(self, state: 'ConnectionState', guild: 'Guild', data: dict) -> None:
        self._state: 'ConnectionState' = state
        self.id: int = int(data['id'])
        self.guild: 'Guild' = guild or self.guild
        self._update(data)

    def _update(self, data) -> None:
        state = self._state
        self.guild_id = int(data['guild_id'])
        self.channel_id: Optional[int] = _get_as_snowflake(data, 'channel_id')
        self.creator_id: Optional[int] = _get_as_snowflake(data, 'creator_id')
        self.name: str = data['name']
        self.description: Optional[str] = data.get('description', None)
        self.start_time: datetime = datetime.fromisoformat(data['scheduled_start_time'])
        self.end_time: Optional[datetime] = datetime.fromisoformat(data['scheduled_end_time']) \
            if data['scheduled_end_time'] is not None else None
        self.privacy_level: PrivacyLevel = try_enum(PrivacyLevel, data['privacy_level'])
        self.status: EventStatus = try_enum(EventStatus, data['status'])
        self.entity_type: EventEntityType = try_enum(EventEntityType, data['entity_type'])
        self.entity_id: Optional[int] = _get_as_snowflake(data, 'entity_id')
        self._entity_meta: Optional[dict] = data.get('entity_metadata', None)
        self.image: Optional[str] = data.get('image', None)
        creator = data.pop('creator', None)
        if creator:
            self.creator: Optional['User'] = state.store_user(data=creator)
        else:
            self.creator: Optional['User'] = state.get_user(self.creator_id) or None
        self.user_count: Optional[int] = data.get('user_count', None)

    @cached_slot_property
    def guild(self) -> Optional['Guild']:
        """The guild the event is scheduled in."""
        return self._state._guilds.get(self.guild_id, None)

    @property
    def location(self) -> Optional[str]:
        """The location of the event if :attr:`.entity_type` is ``external``."""
        if self._entity_meta:
            return self._entity_meta.get('location', None)

    @property
    def channel(self) -> Optional[Union['StageChannel', 'VoiceChannel']]:
        """The channel the event is scheduled in if :attr:`.entity_type` is ``stage`` or ``voice``."""
        if self.creator_id:
            return self.guild.get_channel(self.channel_id)

    @property
    def icon_url(self):
        """:class:`Asset`: Returns the event image asset."""
        return self.icon_url_as()

    def icon_url_as(self, *, format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp', size=1024):
        """Returns an :class:`Asset` for the event image.

        The format must be one of 'webp', 'jpeg', or 'png'. The
        size must be a power of 2 between 16 and 4096.

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the icon to.
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
        from discord import Asset
        return Asset._from_guild_event(self._state, self, format=format, size=size)

    async def edit(self, reason=None, **fields) -> 'GuildScheduledEvent':
        """|coro|

        Modify the event. Requires ``MANAGE_EVENTS`` permissions.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for editing the event, shows up in the audit-log.
        fields

        Returns
        -------
        :class:`GuildScheduledEvent`
            The updatet event.
        """

        try:
            entity_type: Optional[EventEntityType] = fields.pop('type')
        except KeyError:
            entity_type = self.entity_type
        else:
            if not isinstance(entity_type, EventEntityType):
                entity_type = try_enum(EventEntityType, entity_type)
                if not isinstance(entity_type, EventEntityType):
                    raise ValueError('entity_type must be a valid EventEntityType.')

            if entity_type.external and not (self.location or fields.get('location', None)):
                raise InvalidArgument('location must be provided if type is EventEntityType.external')
            fields['entity_type'] = int(entity_type)

        try:
            location: Optional[str] = fields['location']
        except KeyError:
            pass
        else:
            if 1 > len(location) > 100:
                raise ValueError(f'The length of the location must be between 1 and 100 characters long; got {len(location)}.')
            if not entity_type.external:
                entity_type = EventEntityType.external
                fields['entity_type'] = entity_type.external.value
            fields['entity_metadata'] = {'location': location}
            fields['channel_id'] = None

        try:
            channel: Optional[Union['StageChannel', 'VoiceChannel']] = fields.pop('channel')
        except KeyError:
            channel = self.channel
        else:
            from .channel import _check_channel_type
            if not _check_channel_type(channel, types=[2, 13]):
                raise TypeError(f'The new channel must be a StageChannel or VoiceChannel object, not {channel.__class__.__name__}.')
            if entity_type.external:
                entity_type = {13: EventEntityType.stage, 2: EventEntityType.voice}.get(int(channel.type))
                fields['entity_type'] = entity_type.value
            fields['channel_id'] = str(channel.id)
            fields['entity_metadata'] = None

        if not entity_type.external and not channel:
            raise InvalidArgument('channel must be provided if type is EventEntityType.stage or EventEntityType.voice.')

        try:
            name: Optional[str] = fields['name']
        except KeyError:
            pass
        else:
            if 1 > len(name) > 100:
                raise ValueError(f'The length of the name must be between 1 and 100 characters long; got {len(name)}.')

        try:
            description: Optional[str] = fields['description']
        except KeyError:
            pass
        else:
            if 1 > len(description) > 1000:
                raise ValueError(f'The length of the description must be between 1 and 1000 characters long; got {len(description)}.')

        try:
            end_time: Optional[datetime] = fields.pop('end_time')
        except KeyError:
            end_time = self.end_time
        else:
            if end_time is not None:
                if not isinstance(end_time, datetime):
                    raise TypeError(f'The end_time must be a datetime.datetime object, not {end_time.__class__.__name__}.')
                elif end_time < datetime.utcnow():
                    raise ValueError(f'The end_time could not be in the past.')
                fields['scheduled_end_time'] = end_time.isoformat()

        if entity_type == 3 and not end_time:
            raise ValueError('end_time is required for external events.')

        try:
            start_time: Optional[datetime] = fields.pop('start_time')
        except KeyError:
            start_time = self.start_time
        else:
            if start_time is not None:
                if not isinstance(start_time, datetime):
                    raise TypeError(f'The start_time must be a datetime.datetime object, not {start_time.__class__.__name__}.')
                elif start_time < datetime.utcnow():
                    raise ValueError(f'The start_time could not be in the past.')
                fields['scheduled_start_time'] = start_time.isoformat()

        if end_time and start_time > end_time:
            raise ValueError(f'The start_time could not be before the end_time.')

        try:
            status: EventStatus = fields['status']
        except KeyError:
            pass
        else:
            if not isinstance(status, EventStatus):
                raise TypeError(f'The status must be of type discord.EventStatus, not {status.__class__.__name__}.')
            current_status = self.status
            if current_status.canceled or current_status.completed:
                raise ValueError(f'The status of an completed or canceled event could not be changed.')
            elif current_status.active and not status.completed:
                raise ValueError('The status of an active event could only be changed to completed.')
            elif current_status.scheduled and not status.active or status.canceled:
                raise ValueError('The status of an scheduled event could only be changed to active or canceled.')
            fields['status']: int = status.value

        try:
            cover_image: bytes = fields.pop('cover_image')
        except KeyError:
            pass
        else:
            if cover_image is not None:
                if not isinstance(cover_image, bytes):
                    raise ValueError(f'cover_image must be of type bytes, not {cover_image.__class__.__name__}')
                cover_image = _bytes_to_base64_data(cover_image)
            fields['image'] = cover_image

        data = await self._state.http.edit_guild_event(guild_id=self.guild_id, event_id=self.id, reason=reason, **fields)
        self._update(data)
        return self

    async def users(self,
                    limit: int = 100,
                    before: Union['User', datetime] = None,
                    after: Union['User', datetime] = None,
                    with_member: bool = False) -> EventUsersIterator:
        """Returns an :class:`~discord.AsyncIterator` that enables receiving the interest users of the event.

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of users to retrieve.
            If ``None``, retrieves every user of the event.
            Note, however, that this would make it a slow operation.
        before: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve users before this user.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve users after this user.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        with_member: Optional[:class:`bool`]
            If set to ``True``, return the :class:`~discord.Member` instead of the :class:`~discord.User` if it is part of the guild the event is in.


        Examples
        ---------

        .. code-block:: python3

            # Usage

            counter = 0
            async for user in event.users(limit=200):
                if user.id > 264905529753600000:  # all accounts created before 2018
                    counter += 1

            # Flattening into a list

            users = await event.users(limit=123).flatten()
            # users is now a list of Member/User...

        Raises
        ------
        ~discord.Forbidden
            You do not have permissions to get the event users.
        ~discord.HTTPException
            The request to get event users failed.

        Yields
        -------
        Union[:class:`~discord.Member`, :class:`~discord.User`]
            The user or member.
        """
        return EventUsersIterator(event=self, limit=limit, before=before, after=after, with_member=with_member)

    async def delete(self, *, reason: str = None) -> None:
        """
        Deletes the event. Requires ``MANAGE_EVENTS`` permissions.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for deleting the event, shows up in the audit-log.
        Returns
        -------
        None
        """
        await self._state.http.delete_guild_event(guild_id=self.guild_id, event_id=self.id, reason=reason)