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


from typing import (
    Any,
    List,
    Dict,
    Tuple,
    Union,
    Optional,
    Iterable,
    TYPE_CHECKING
)

import datetime

from .role import Role
from .abc import Snowflake, GuildChannel
from .object import Object
from .enums import AutoModEventType, AutoModKeywordPresetType, AutoModActionType, AutoModTriggerType, try_enum


if TYPE_CHECKING:
    # Add imports here, that are only used for annotation and would raise CircularImportError otherwise
    from .state import ConnectionState
    from .guild import Guild
    from .member import Member

__all__ = (
    'AutoModAction',
    'AutoModTriggerMetadata',
    'AutoModRule'
)

class AutoModAction:
    def __init__(self, type: AutoModActionType, **metadata):
        """
        Represents an action which will execute whenever a rule is triggered.

        Parameters
        -----------
        type: :class:`AutoModActionType`
            The type of action
        channel_id: Optional[:class:`Snowflake]
            The channel to which user content should be logged.

            .. note::
                This field is only required :attr:`type` is :attr:`AutoModActionType.send_alert_message`

        timeout_duration: Union[:class:`int`, :class:`datetime.datetime`, None]
            Duration in seconds (:class:`int`) or a timerange (:class:`~datetime.timedelta`) for wich the user should be timeouted.

            **The maximum value is ``2419200`` seconds (4 weeks)**

            .. note::
               This field is only required if :attr:`type` is :attr:`AutoModActionType.timeout_user`
        """

        self.type = try_enum(type, AutoModActionType)
        self._metadata = metadata
        self.channel_id: Optional[Snowflake] = metadata.get('channel_id', None)
        timeout_duration: Optional[int, datetime.timedelta] = metadata.get('timeout_duration', None)
        if timeout_duration and isinstance(timeout_duration, int):
            timeout_duration = datetime.timedelta(seconds=timeout_duration)
        if timeout_duration.total_seconds() > 2419200:
            raise ValueError('The maximum timeout duration is 2419200 seconds (4 weeks).')
        self.timeout_duration = timeout_duration


class AutoModTriggerMetadata:
    def __init__(self,
                 keyword_filter: Optional[List[str]] = None,
                 presets: Optional[List[AutoModKeywordPresetType]] = None):
        """
        Additional data used to determine whether a rule should be triggered.
        Different fields are relevant based on the value of :attr:`AutoModRule.trigger_type`

        Parameters
        -----------
        keyword_filter: Optional[List[:class:`str`]]
            Substrings which will be searched for in content

            .. note::
                Field is only required if :attr:`AutoModRule.trigger_type` is :attr:`AutoModTriggerType.keyword`

        presets: Optional[List[:class:`AutoModKeywordPresetType`]]
            The internally pre-defined wordsets which will be searched for in content

            .. note::
                Field is only required if :attr:`AutoModRule.trigger_type` is :attr:`AutoModTriggerType.keyword_preset`
        """

        self.keyword_filter: Optional[List[str]] = keyword_filter or []
        self.presets: Optional[List[AutoModKeywordPresetType]] = presets or []

    @property
    def prefix_keywords(self):
        """
        Returns all keywords for words that must start with the keyword.

        .. note::
            This is equal to
            .. code-block:: python3

                for keyword in self.keyword_filter:
                    if keyword[0] != '*' and keyword[-1] == '*':
                        yield keyword
                        
        Yields
        -------
        :class:`str`
            A keyword
        """
        for keyword in self.keyword_filter:
            if keyword[0] != '*' and keyword[-1] == '*':
                yield keyword

    @property
    def suffix_keywords(self):
        """
        Returns all keywords for words that must end with the keyword.

        .. note::
            This is equal to
            .. code-block:: python3

                for keyword in self.keyword_filter:
                    if keyword[0] == '*' and keyword[-1] != '*':
                        yield keyword

        Yields
        -------
        :class:`str`
            A keyword
        """
        for keyword in self.keyword_filter:
            if keyword[0] != '*' and keyword[-1] == '*':
                yield keyword

    @property
    def anywhere_keywords(self):
        """
        Returns all keywords which can appear anywhere in a word

        .. note::
            This is equal to
            .. code-block:: python3

                for keyword in self.keyword_filter:
                    if keyword[0] == '*' and keyword[-1] == '*':
                        yield keyword

        Yields
        -------
        :class:`str`
            A keyword
        """
        for keyword in self.keyword_filter:
            if keyword[0] == '*' and keyword[-1] == '*':
                yield keyword

    @property
    def whole_word_keywords(self):
        """
        Returns all keywords that must occur as a whole in a word or phrase and must be surrounded by spaces.

        .. note::
            This is equal to
            .. code-block:: python3

                for keyword in self.keyword_filter:
                    if keyword[0] != '*' and keyword[-1] != '*':
                        yield keyword

        Yields
        -------
        :class:`str`
            A keyword
        """
        for keyword in self.keyword_filter:
            if keyword[0] != '*' and keyword[-1] != '*':
                yield keyword


class AutoModRule:
    def __init__(self,
                 state: ConnectionState,
                 guild: Guild,
                 data: Dict[str, Any]
                 ):
        """
        .. warning::
            Do not initialize this class directly. Use :func:`discord.Guild.add_auto_mod_rule` instead.

        Attributes
        -----------
        id: :class:`int`
            The id of this rule
        guild: :class:`~discord.Guild`
            The guild  this rule belongs to
        name: :class:`str`
            The name of the rule
        creator_id: :class:`int`
            The id of the user wich created this rule
        event_type: :class:`AutoModEventType`
            The event wich will trigger this rule
        trigger_type: :class:`AutoModEventType`
            The type of content which will trigger the rule
        trigger_metadata: :class:`AutoModTriggerMetadata`
            Additional data used to determine whether a rule should be triggered.
            Different fields are relevant based on the value of :attr:`.trigger_type`.
        actions: List[:class:AutoModAction`]
            The actions which will execute when the rule is triggered
        enabled: :class:`bool`
            Whether the rule is enabled
        """
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.guild: Guild = guild
        self.name: str = data['name']
        self.creator_id: int = int(data['creator_id'])
        self.event_type: AutoModEventType = try_enum(AutoModEventType, data['event_type'])
        self.trigger_type: AutoModTriggerType = try_enum(AutoModTriggerType, data['trigger_type'])
        self.trigger_metadata: AutoModTriggerMetadata = AutoModTriggerMetadata(**data['trigger_metadata'])
        self.actions: List[AutoModAction] = [AutoModAction(**action) for action in data['actions']]
        self.enabled: bool = data['enabled']
        self._except_roles: List[Snowflake] = [role_id for role_id in data.get('except_roles', [])],
        self._except_channels: List[Snowflake] = [channel_id for channel_id in data.get('except_channels', [])],

    @property
    def except_roles(self):
        """
        Yields the roles that should not be affected by the rule (Maximum of 20)

        .. note::
            This is equal to
            .. code-block:: python3

                for role_id in self._except_roles:
                    role = self.guild.get_role(int(role_id))
                    yield role or Object(int(role_id))

        Yields
        -------
        Union[:class:`~discord.Role`, :class:`~discord.Object`]
            An excluded role or an object with the id if the role is not found
        """
        for role_id in self._except_roles:
            role = self.guild.get_role(int(role_id))
            yield role or Object(role_id, _type=Role, state=self._state)

    @property
    def except_channels(self):
        """
        Yields the channels that should not be affected by the rule (Maximum of 20)

        .. note::
            This is equal to
            .. code-block:: python3

                for channel_id in self._except_channels:
                    channel = self.guild.get_role(int(channel_id))
                    yield channel or Object(channel_id, _type=GuildChannel, state=self._state)

        Yields
        -------
        Union[:class:`~discord.Role`, :class:`~discord.Object`]
            An excluded channel or an :class:`~discord.object` with the id if the channel is not found
        """
        for channel_id in self._except_channels:
            channel = self.guild.get_role(int(channel_id))
            yield channel or Object(channel_id, _type=GuildChannel, state=self._state)