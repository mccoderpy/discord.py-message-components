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
from __future__ import annotations

from typing_extensions import Literal
from typing import Any, Optional, Union, Dict, TYPE_CHECKING

from datetime import datetime

from .mixins import Hashable
from .errors import InvalidArgument
from .utils import _get_as_snowflake, cached_slot_property, _bytes_to_base64_data, utcnow, MISSING
from .enums import PrivacyLevel, EventEntityType, EventStatus, try_enum
from .iterators import EventUsersIterator


if TYPE_CHECKING:
    from .types.guild import (
        ScheduledEventEntityMetadata as ScheduledEventEntityMetadataData,
        ScheduledEvent as ScheduledEventData,
    )
    from .state import ConnectionState
    from .asset import Asset
    from .guild import Guild
    from .user import User
    from .channel import StageChannel, VoiceChannel

__all__ = (
    'GuildScheduledEvent',
)


class GuildScheduledEvent(Hashable):
    """
    Represents a scheduled event in a guild

    .. warning::
        Do not initialize this class manually. Use :meth:`~discord.Guild.fetch_event`/:meth:`~discord.Guild.fetch_events`
        or to create one :meth:`~discord.Guild.create_scheduled_event` instead.

    Attributes
    -----------
    id: :class:`int`
        The id of the event
    name: :class:`str`
        The name of the event
    description: :class:`str`
        The description of the event
    start_time: :class:`datetime.datetime`
        When the event will start
    end_time: Optional[:class:`datetime.datetime`]
        Optional, when the event will end
    creator: :class:`~discord.User`
        The creator of the event
    status: :class:`EventStatus`
        The status of the event
    entity_type: :class:`EventEntityType`
        The type of the scheduled event
    image: Optional[:class:`str`]
        Optional, the image hash of the event
    broadcast_to_directory_channels: :class:`bool`
        Whether the event will be broadcasted to directory channels

        .. note::
            This is only possible when the guild the event belongs to is part of a student hub.
    """
    if TYPE_CHECKING:
        name: str
        guild_id: int
        status: EventStatus
        entity_type: EventEntityType
        privacy_level: PrivacyLevel
        channel_id: Optional[int]
        creator_id: Optional[int]
        description: Optional[str]
        start_time: datetime
        end_time: Optional[datetime]
        entity_id: Optional[int]
        image: Optional[str]
        creator: Optional[User]
        user_count: Optional[int]
        broadcast_to_directory_channels: bool
        _entity_meta: Optional[ScheduledEventEntityMetadataData]

    def __init__(self, state: ConnectionState, guild: Guild, data: ScheduledEventData) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.guild: Guild = guild or self.guild
        self._update(data)

    def _update(self, data: ScheduledEventData) -> None:
        state = self._state
        self.name = data['name']
        self.guild_id = int(data['guild_id'])
        self.channel_id = _get_as_snowflake(data, 'channel_id')
        self.creator_id = _get_as_snowflake(data, 'creator_id')
        self.description = data.get('description')
        self.start_time = datetime.fromisoformat(data['scheduled_start_time'])
        self.end_time = datetime.fromisoformat(data['scheduled_end_time']) \
            if data['scheduled_end_time'] is not None else None
        self.privacy_level = try_enum(PrivacyLevel, data['privacy_level'])
        self.status = try_enum(EventStatus, data['status'])
        self.entity_type = try_enum(EventEntityType, data['entity_type'])
        self.entity_id = _get_as_snowflake(data, 'entity_id')
        self._entity_meta = data.get('entity_metadata')
        self.image = data.get('image')
        creator = data.pop('creator', None)
        if creator:
            self.creator = state.store_user(data=creator)
        else:
            self.creator = state.get_user(self.creator_id) or None
        self.user_count = data.get('user_count')
        self.broadcast_to_directory_channels = data.get('broadcast_to_directory_channels', False)

    @cached_slot_property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild the event is scheduled in, if cached."""
        return self._state._get_guild(self.guild_id)

    @property
    def location(self) -> Optional[str]:
        """Optional[:class:`str`]: The location of the event if :attr:`.entity_type` is ``external``."""
        if self._entity_meta:
            return self._entity_meta.get('location', None)

    @property
    def channel(self) -> Optional[Union[StageChannel, VoiceChannel]]:
        """Optional[Union[:class:`StageChannel`, :class:`VoiceChannel`]]:
        The channel the event is scheduled in if :attr:`.entity_type` is ``stage`` or ``voice``.
        """
        if self.creator_id:
            return self.guild.get_channel(self.channel_id)

    @property
    def icon_url(self) -> Asset:
        """:class:`Asset`: Returns the event image asset."""
        return self.icon_url_as()

    def icon_url_as(
        self,
        *,
        format: Literal['jpeg', 'jpg', 'webp', 'png'] = 'webp',
        size: int = 1024
    ) -> Asset:
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

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
        start_time: datetime = MISSING,
        end_time: Optional[datetime] = MISSING,
        status: EventStatus = MISSING,
        entity_type: EventEntityType = MISSING,
        location: str = MISSING,
        channel: Optional[Union[StageChannel, VoiceChannel]] = MISSING,
        cover_image: Optional[bytes] = MISSING,
        reason: Optional[str] = None
    ) -> GuildScheduledEvent:
        """|coro|

        Modify the event. Requires :attr:`~Permissions.manage_events` permissions.
        All parameters are optional.

        Parameters
        ----------
        name: :class:`str`
            The new name of the event
        description: :class:`str`
            The new description of the event
        start_time: :class:`datetime.datetime`
            The new start time of the event
        end_time: Optional[:class:`datetime.datetime`]
            The new end time of the event
        status: :class:`EventStatus`
            The new status of the event.
        entity_type: :class:`EventEntityType`
            The new type of the scheduled event
        location: :class:`str`
            The new location of the event. If ``entity_type`` is :attr:`~EventEntityType.external`
        channel: Optional[Union[:class:`StageChannel, :class:`VoiceChannel`]]
            The new channel the event is scheduled in if ``entity_type`` is :attr:`EventEntityType.stage` or
            :attr:`EventEntityType.voice`.
        cover_image: Optional[:class:`bytes`]
            The new cover image of the event. Must be a :attr:`bytes` object representing a jpeg or png image.
        reason: Optional[:class:`str`]
            The reason for editing the event, shows up in the audit-log.

        Returns
        -------
        :class:`GuildScheduledEvent`
            The updatet event.
        """

        payload: Dict[str, Any] = {}

        if entity_type is MISSING:
            entity_type = self.entity_type
        else:
            payload['entity_type'] = int(entity_type)

        if name is not MISSING:
            if 1 > len(name) > 100:
                raise ValueError(f'The length of the name must be between 1 and 100 characters long; got {len(name)}.')
            payload['name'] = name

        if description is not MISSING:
            if 1 > len(description) > 1000:
                raise ValueError(
                    f'The length of the description must be between 1 and 1000 characters long; got {len(description)}.'
                )

            payload['description'] = description

        if location is not MISSING:
            if 1 > len(location) > 100:
                raise ValueError(
                    f'The length of the location must be between 1 and 100 characters long; got {len(location)}.'
                )
            if not entity_type.external:
                entity_type = EventEntityType.external
                payload['entity_type'] = int(entity_type)
            payload['entity_metadata'] = {'location': location}
            payload['channel_id'] = None

        if channel is not MISSING:
            if channel.__class__.__name__ not in ('StageChannel', 'VoiceChannel'):
                raise TypeError(
                    f'The new channel must be a StageChannel or VoiceChannel object, not {channel.__class__.__name__}.'
                )
            if entity_type.external:
                entity_type = {13: EventEntityType.stage, 2: EventEntityType.voice}.get(int(channel.type))
                payload['entity_type'] = entity_type.value
            payload['channel_id'] = str(channel.id)
            payload['entity_metadata'] = None

        if not entity_type.external and not channel:
            raise InvalidArgument(
                'A channel must be provided if type is EventEntityType.stage or EventEntityType.voice.'
            )

        if end_time is MISSING:
            end_time = self.end_time
        elif end_time is not None:
            if not isinstance(end_time, datetime):
                raise TypeError(f'The end_time must be a datetime.datetime object, not {end_time.__class__.__name__}.')
            elif end_time < utcnow():
                raise ValueError('The end_time could not be in the past.')
            payload['scheduled_end_time'] = end_time.isoformat()
        else:
            payload['scheduled_end_time'] = None


        if entity_type.external and not end_time:
            raise ValueError('end_time is required for external events.')

        if start_time is MISSING:
            start_time = self.start_time
        elif start_time is not None:
            if not isinstance(start_time, datetime):
                raise TypeError(
                    f'The start_time must be a datetime.datetime object, not {start_time.__class__.__name__}.'
                )
            elif start_time < utcnow():
                raise ValueError('The start_time could not be in the past.')
            payload['scheduled_start_time'] = start_time.isoformat()
        else:
            payload['scheduled_start_time'] = None

        if end_time and start_time > end_time:
            raise ValueError('The start_time could not be before the end_time.')

        if status is not MISSING:
            if not isinstance(status, EventStatus):
                raise TypeError(f'The status must be of type discord.EventStatus, not {status.__class__.__name__}.')
            current_status = self.status
            if current_status.canceled or current_status.completed:
                raise ValueError('The status of an completed or canceled event could not be changed.')
            elif current_status.active and not status.completed:
                raise ValueError('The status of an active event could only be changed to completed.')
            elif current_status.scheduled and not status.active or status.canceled:
                raise ValueError('The status of an scheduled event could only be changed to active or canceled.')
            payload['status'] = status.value

        if cover_image is not MISSING:
            if cover_image is not None:
                if not isinstance(cover_image, bytes):
                    raise ValueError(f'cover_image must be of type bytes, not {cover_image.__class__.__name__}')
                cover_image = _bytes_to_base64_data(cover_image)
            payload['image'] = cover_image

        data = await self._state.http.edit_guild_event(
            guild_id=self.guild_id,
            event_id=self.id,
            reason=reason,
            payload=payload
        )
        self._update(data)
        return self

    async def users(
        self,
        limit: int = 100,
        before: Union[User, datetime] = None,
        after: Union[User, datetime] = None,
        with_member: bool = False
    ) -> EventUsersIterator:
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

    async def delete(self, *, reason: Optional[str] = None) -> None:
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