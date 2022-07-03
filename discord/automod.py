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


from typing import (
    Any,
    List,
    Dict,
    Union,
    Optional,
    TYPE_CHECKING,
    Iterator
)

import datetime

from . import utils
from .role import Role
from .object import Object
from .abc import GuildChannel
from .utils import SnowflakeList
from .errors import ClientException
from .enums import AutoModEventType, AutoModKeywordPresetType, AutoModActionType, AutoModTriggerType, try_enum


if TYPE_CHECKING:
    # Add imports here, that are only used for annotation and would raise CircularImportError otherwise
    from .state import ConnectionState
    from .guild import Guild
    from .user import User
    from .member import Member

__all__ = (
    'AutoModAction',
    'AutoModTriggerMetadata',
    'AutoModRule',
    'AutoModActionPayload'
)


class AutoModAction:
    """
    Represents an action which will execute whenever a rule is triggered.

    Parameters
    -----------
    type: :class:`AutoModActionType`
        The type of action
    channel_id: Optional[:class:`int`]
        The channel to which user content should be logged.

        .. note::
            This field is only required :attr:`~AutoModAction.type` is :attr:~`AutoModActionType.send_alert_message`

    timeout_duration: Optional[Union[:class:`int`, :class:`datetime.timedelta`]]
        Duration in seconds (:class:`int`) or a timerange (:class:`~datetime.timedelta`) for wich the user should be timeouted.

        **The maximum value is ``2419200`` seconds (4 weeks)**

        .. note::
           This field is only required if :attr:`type` is :attr:`AutoModActionType.timeout_user`

    """
    def __init__(self, type: AutoModActionType, **metadata):
        self.type: AutoModActionType = try_enum(AutoModActionType, type)
        self.metadata = metadata  # maybe we need this later... idk
        action_type = self.type  # speedup attribute access
        if action_type.send_alert_message:
            try:
                self.channel_id: Optional[int] = metadata['channel_id']
            except KeyError:
                raise TypeError('If the type is send_alert_message you must specify a channel_id')
        elif action_type.timeout_user:
            try:
                timeout_duration: Optional[Union[int, datetime.timedelta]] = metadata['timeout_duration']
            except KeyError:
                raise TypeError('If the type is timeout_user you must specify a timeout_duration')
            else:
                if isinstance(timeout_duration, int):
                    timeout_duration = datetime.timedelta(seconds=timeout_duration)
                if timeout_duration.total_seconds() > 2419200:
                    raise ValueError('The maximum timeout duration is 2419200 seconds (4 weeks).')
                self.timeout_duration: Optional[datetime.timedelta] = timeout_duration

    def to_dict(self) -> Dict[str, Any]:
        base = {
            'type': int(self.type)
        }
        metadata = {}
        if self.type.send_alert_message:
            metadata['channel_id'] = self.channel_id
        elif self.type.timeout_user:
            metadata['duration_seconds'] = self.timeout_duration
        base['metadata'] = metadata
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AutoModAction:
        action_type = try_enum(AutoModActionType, data['type'])
        metadata = data['metadata']
        if action_type.timeout_user:
            metadata['timeout_duration'] = metadata.pop('duration_seconds')
        elif action_type.send_alert_message:
            metadata['channel_id'] = int(metadata['channel_id'])
        return cls(action_type, **metadata)


class AutoModTriggerMetadata:
    """Additional data used to determine whether a rule should be triggered.
    Different fields are relevant based on the value of :attr:`AutoModRule.trigger_type`

    Parameters
    -----------
    keyword_filter: Optional[List[:class:`str`]]
        Substrings which will be searched for in content

        .. note::
            This field is only present if :attr:`~AutoModRule.trigger_type` is :attr:`AutoModTriggerType.keyword`

    presets: Optional[List[:class:`AutoModKeywordPresetType`]]
        The internally pre-defined wordsets which will be searched for in content

        .. note::
            This field is only present if :attr:`~AutoModRule.trigger_type` is :attr:`AutoModTriggerType.keyword_preset`
    exempt_words: Optional[List[str]]
        Substrings which should be excluded from the blacklist.

        .. note::
            This field is only present if :attr:`~AutoModRule.trigger_type` is :attr:`AutoModTriggerType.keyword_preset`
    """
    def __init__(self,
                 keyword_filter: Optional[List[str]] = None,
                 presets: Optional[List[AutoModKeywordPresetType]] = None,
                 exempt_words: Optional[List[str]] = None) -> None:
        """Additional data used to determine whether a rule should be triggered.
        Different fields are relevant based on the value of :attr:`AutoModRule.trigger_type`

        Parameters
        -----------
        keyword_filter: Optional[List[:class:`str`]]
            Substrings which will be searched for in content

            .. note::
                This field is only required if :attr:`~AutoModRule.trigger_type` is :attr:`~AutoModTriggerType.keyword`

        presets: Optional[List[:class:`AutoModKeywordPresetType`]]
            The internally pre-defined wordsets which will be searched for in content

            .. note::
                This field is only required if :attr:`~AutoModRule.trigger_type` is :attr:`~AutoModTriggerType.keyword_preset`

        exempt_words: Optional[List[str]]
            Substrings which should be excluded from the blacklist.

            .. note::
                This field is only present if :attr:`~AutoModRule.trigger_type` is :attr:`~AutoModTriggerType.keyword_preset`

        Raises
        -------
        :exc:`TypeError`
            Both of keyword_filter and presets was passed
        """
        if keyword_filter and presets:
            raise TypeError('Only one of keyword_filter or presets are accepted.')
        self.keyword_filter: Optional[List[str]] = keyword_filter or []
        self.presets: Optional[List[AutoModKeywordPresetType]] = presets or []
        if exempt_words and not presets:
            raise TypeError('exempt_words can only be used with presets')
        self.exempt_words: Optional[List[str]] = exempt_words

    @property
    def prefix_keywords(self) -> Iterator[str]:
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
    def suffix_keywords(self) -> Iterator[str]:
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
    def anywhere_keywords(self) -> Iterator[str]:
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
    def whole_word_keywords(self) -> Iterator[str]:
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

    def to_dict(self) -> Dict[str, Any]:
        if self.keyword_filter:
            return {'keyword_filter': self.keyword_filter}
        else:
            base = {'presets': [int(p) for p in self.presets]}
            if self.exempt_words:
                base['allow_list'] = self.exempt_words
            return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AutoModTriggerMetadata:
        self = cls.__new__(cls)
        presets = data.get('presets', None)
        if presets:
            self.presets = data['presets']
            self.exempt_words = data.get('allow_list', [])
        else:
            self.keyword_filter = data.get('keyword_filter', None)
        return self


class AutoModRule:
    """
    Represents a rule for auto moderation

    .. warning::
        Do not initialize this class directly. Use :meth:`~discord.Guild.create_automod_rule` instead.

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
    actions: List[:class:`AutoModAction`]
        The actions which will execute when the rule is triggered
    enabled: :class:`bool`
        Whether the rule is enabled
    """
    def __init__(self,
                 state: ConnectionState,
                 guild: Guild,
                 **data) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.creator_id: int = int(data['creator_id'])
        self.event_type: AutoModEventType = try_enum(AutoModEventType, data['event_type'])
        self.trigger_type: AutoModTriggerType = try_enum(AutoModTriggerType, data['trigger_type'])
        self.trigger_metadata: AutoModTriggerMetadata = AutoModTriggerMetadata.from_dict(data['trigger_metadata'])
        self.actions: List[AutoModAction] = [AutoModAction.from_dict(action) for action in data['actions']]
        self.enabled: bool = data['enabled']
        self._exempt_roles: SnowflakeList = SnowflakeList(map(int, data['exempt_roles']))
        self._exempt_channels: SnowflakeList = SnowflakeList(map(int, data['exempt_channels']))

    def __repr__(self) -> str:
        return f'<AutoModRule "{self.name}" guild_id={self.guild.id} creator_id={self.creator_id}>'

    @property
    def exempt_roles(self) -> Iterator[Union[Role, Object]]:
        """
        Yields the roles that should not be affected by the rule (Maximum of 20)

        .. note::
            This is equal to

            .. code-block:: python3

                for role_id in self._exempt_roles:
                    role = self.guild.get_role(int(role_id))
                    yield role or Object(int(role_id))

        Yields
        -------
        Union[:class:`~discord.Role`, :class:`~discord.Object`]
            An excluded role or an object with the id if the role is not found
        """
        for role_id in self._exempt_roles:
            role = self.guild.get_role(int(role_id))
            yield role or Object(role_id, _type=Role, state=self._state)

    @property
    def exempt_channels(self) -> Iterator[Union[GuildChannel, Object]]:
        """
        Yields the channels that should not be affected by the rule (Maximum of 20)

        .. note::
            This is equal to

            .. code-block:: python3

                for channel_id in self._exempt_channels:
                    channel = self.guild.get_role(int(channel_id))
                    yield channel or Object(channel_id, _type=GuildChannel, state=self._state)

        Yields
        -------
        Union[:class:`~discord.Role`, :class:`~discord.Object`]
            An excluded channel or an :class:`~discord.object` with the id if the channel is not found
        """
        for channel_id in self._exempt_channels:
            channel = self.guild.get_role(int(channel_id))
            yield channel or Object(channel_id, _type=GuildChannel, state=self._state)
        
    @property
    def creator(self) -> Optional[Member]:
        """
        Returns the creator of the rule

        .. note::
            The :attr:`Intents.members` must be enabled, otherwise this may return `` None``
        
        Raises
        -------
        ClientException:
            If the member is not found and :attr:`~Intents.members` intent is not enabled.
        
        Returns
        --------
        Optional[Member]
            The member, that created the rule.
        """
        creator = self.guild.get_member(self.creator_id)
        # If the member is not found and the members intent is disabled, then raise
        if not creator and not self._state.intents.members:
            raise ClientException('Intents.members must be enabled to use this')
        return creator

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: When the rule was created in UTC"""
        return utils.snowflake_time(self.id)


class AutoModActionPayload:
    """Represents the payload for an :func:`on_automod_action` event

    Attributes
    -----------
    guild_id: :class:`int`
        The id of the guild in which action was executed
    action: :class:`AutoModAction`
        The action wich was executed
    rule_id: :class:`int`
        The id of the rule which action belongs to
    rule_trigger_type: :class:`~discord.AutoModTriggerType`
        The trigger type of rule wich was triggered
    user_id: :class:`int`
        The id of the user which generated the content which triggered the rule
    channel_id: Optional[:class:`int`]
        The id of the channel in which user content was posted
    message_id: Optional[:class:`int`]
        The id of any user message which content belongs to

        .. note::
            This wil not exists if message was blocked by automod or content was not part of any message

    alert_system_message_id: Optional[:class:`int`]
        The id of any system auto moderation messages posted as the result of this action

        .. note::
            This will only exist if the :attr:`~AutoModAction.type` of the :attr:`~AutoModActionPayload.action` is ``send_alert_message``

    content: :class:`str`
        The user generated text content

        .. important::
            The :attr:`Intents.message_content` intent is required to get a non-empty value for this field

    matched_keyword: :class:`str`
        The word ot phrase configured in the rule that triggered the rule
    matched_content: :class:`str`
        The substring in :attr:`~AutoModActionPayload.content` that triggered the rule

         .. important::
            The :attr:`~Intents.message_content` intent is required to get a non-empty value for this field

    """
    __slots__ = (
        '_state', 'guild_id', 'action', 'rule_id', 'rule_trigger_type', 'user_id', 'channel_id', 'message_id',
        'alert_system_message_id', 'content', 'matched_keyword', 'matched_content'
    )

    def __init__(self, state: ConnectionState, data: Dict[str, Any]) -> None:
        self._state = state
        self.guild_id: int = int(data['guild_id'])
        self.action: AutoModAction = AutoModAction.from_dict(data['action'])
        self.rule_id: int = int(data['rule_id'])
        self.rule_trigger_type: AutoModTriggerType = try_enum(AutoModTriggerType, data['rule_trigger_type'])
        self.user_id: int = int(data['user_id'])
        self.channel_id: Optional[int] = int(data.get('channel_id', 0))
        self.message_id: Optional[int] = int(data.get('message_id', 0))
        self.alert_system_message_id: Optional[int] = int(data.get('alert_system_message_id', 0))
        self.content: str = data['content']
        self.matched_keyword: Optional[str] = data.get('matched_keyword', None)
        self.matched_content: Optional[str] = data.get('matched_content', None)

    @property
    def guild(self) -> Guild:
        """
        The guild in which action was executed

        Returns
        --------
        :class:`Guild`
            The guild object
        """
        return self._state._get_guild(self.guild_id)

    @property
    def channel(self) -> Optional[GuildChannel]:
        """
        The channel in wich user content was posted, if any.

        Returns
        --------
        Optional[:class:`abc.GuildChannel`]
            The :class:`TextChannel`, :class:`VoiceChannel` or :class:`ThreadChannel` the user content was posted in.
        """
        return self.guild.get_channel(self.channel_id)

    @property
    def user(self) -> Optional[User]:
        """
        The user which content triggered the rule

        .. note::
            This can return ``None`` if the user is not in the cache

        Returns
        --------
        :class:`.User`
            The user that triggered the rule
        """
        return self._state.get_user(self.user_id)

    @property
    def member(self) -> Optional[Member]:
        """
        The corresponding :class:`Member` of the :attr:`~AutoModActionPayload.user` in the :attr:`~AutoModActionPayload.guild`.

        .. note::
            :attr:`Intents.members` must be enabled in order to use this

        Raises
        -------
        ClientException:
            If the member is not found and :attr:`~Intents.members` intent is not enabled.

        Returns
        --------
        Optional[Member]:
            The guild member
        """
        member = self.guild.get_member(self.user_id)
        # If the member is not found and the members intent is disabled, then raise
        if not member and not self._state.intents.members:
            raise ClientException('Intents.members must be enabled to use this')
        return member
