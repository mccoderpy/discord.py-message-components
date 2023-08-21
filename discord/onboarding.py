#  The MIT License (MIT)
#
#  Copyright (c) 2021-present mccoderpy
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

from __future__ import annotations

import os
from typing import (
    TYPE_CHECKING,
    Iterable,
    Optional,
    Set,
    List,
    Union,
)


from . import utils
from .mixins import Hashable
from .enums import OnboardingMode, OnboardingPromptType, try_enum
from .utils import cached_slot_property, MISSING

__all__ = (
    'Onboarding',
    'OnboardingPrompt',
    'PartialOnboardingPrompt',
    'OnboardingPromptOption',
    'PartialOnboardingPromptOption',
)


if TYPE_CHECKING:
    from .abc import GuildChannel
    from .channel import ThreadChannel
    from .emoji import Emoji
    from .guild import Guild
    from .partial_emoji import PartialEmoji
    from .role import Role
    from .state import ConnectionState
    from .types.guild import (
        Onboarding as OnboardingData,
        OnboardingPrompt as PromptData,
        OnboardingPromptOption as PromptOptionData,
    )


class PartialOnboardingPromptOption(Hashable):
    """Represents a partial onboarding prompt option.
    These are used when creating a new :class:`OnboardingPrompt` via. :meth:`Guild.edit_onboarding`.

    .. versionadded:: 2.0

    Attributes
    ----------
    title: :class:`str`
        The title of the option.
    description: :class:`str`
        The description of the option.
    emoji: Optional[Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`]]
        The emoji to display next to the option. This can be a custom emoji of the same guild, or a unicode emoji.
    channel_ids: Set[:class:`int`]
        The IDs of the channels added to the users channel list, if the option is selected.
    role_ids: Set[:class:`int`]
        The IDs of the roles that the option will add the user to, if the option is selected.
    """

    __slots__ = (
        'title',
        'emoji',
        'description',
        'channel_ids',
        'role_ids',
    )

    def __init__(
        self,
        title: str,
        emoji: Optional[Union[Emoji, PartialEmoji, str]] = None,
        description: Optional[str] = None,
        channel_ids: Iterable[int] = MISSING,
        role_ids: Iterable[int] = MISSING,
    ) -> None:
        self.title: str = title
        self.emoji: Optional[Union[Emoji, PartialEmoji, str]] = emoji
        self.description: Optional[str] = description
        self.channel_ids: Set[int] = set(channel_ids or [])
        self.role_ids: Set[int] = set(role_ids or [])

    def _to_dict(self, *, id: int = MISSING) -> PromptOptionData:
        from .state import ConnectionState

        base = {
            'title': self.title,
            'emoji': ConnectionState.emoji_to_partial_payload(self.emoji) if self.emoji else None,
            'description': self.description,
            'channel_ids': list(self.channel_ids),
            'role_ids': list(self.role_ids),
        }
        if id is not MISSING:
            base['id'] = id
        return base


class OnboardingPromptOption(PartialOnboardingPromptOption, Hashable):
    """Represents an onboarding prompt option.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the option.
    title: :class:`str`
        The title of the option.
    description: Optional[:class:`str`]
        The description of the option.
    emoji: Optional[Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`]]
        The emoji displayed next to the option.
        This can be a custom emoji of the same guild, or a unicode emoji.
    channel_ids: Set[:class:`int`]
        The IDs of the channels added to the users channel list, if the option is selected.
    role_ids: Set[:class:`int`]
        The IDs of the roles added to the user, if the option is selected.
    """

    __slots__ = (
        '_state',
        '_cs_channels',
        '_cs_roles',
        'guild',
        'id',
    )

    def __init__(self, *, data: PromptOptionData, state: ConnectionState, guild: Guild) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self.id: int = int(data['id'])
        super().__init__(
            title=data['title'],
            emoji=state.get_emoji_from_partial(data['emoji']),
            description=data['description'],
            channel_ids=[int(id) for id in data['channel_ids']],
            role_ids=[int(id) for id in data['role_ids']],
        )

    def __repr__(self) -> str:
        return f'<OnboardingPromptOption id={self.id} title={self.title!r}>'

    @cached_slot_property('_cs_channels')
    def channels(self) -> List[Union[GuildChannel, ThreadChannel]]:
        """List[Union[:class:`abc.GuildChannel`, :class:`ThreadChannel`]]: The channels added to the users channel list,
        if the option is selected.
        """
        return utils._unique(filter(None, map(self.guild.get_channel, self.channel_ids)))  # type: ignore

    @cached_slot_property('_cs_roles')
    def roles(self) -> List[Role]:
        """List[:class:`Role`]: The roles added to the user, if the option is selected."""
        return utils._unique(filter(None, map(self.guild.get_role, self.role_ids)))  # type: ignore

    def _to_dict(self) -> PromptOptionData:
        return super()._to_dict(id=self.id)


class PartialOnboardingPrompt:
    """Represents a partial onboarding prompt.
    These are used when creating a new :class:`OnboardingPrompt` via. :meth:`Guild.edit_onboarding`.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`OnboardingPromptType`
        The type of the prompt.
    title: :class:`str`
        The title of the prompt.
    options: List[:class:`PartialOnboardingPromptOption`]
        The options of the prompt.
    single_select: :class:`bool`
        Whether users can only select one option in the prompt.
    required: :class:`bool`
        Whether the prompt is required, for completing the onboarding flow.
    in_onboarding: :class:`bool`
        Whether the prompt is in the onboarding flow.
        If ``False``, the prompt will only appear in the Channels & Roles tab
    """

    __slots__ = (
        'type',
        'title',
        'options',
        'single_select',
        'required',
        'in_onboarding',
    )

    def __init__(
        self,
        *,
        type: OnboardingPromptType,
        title: str,
        options: List[PartialOnboardingPromptOption],
        single_select: bool = True,
        required: bool = True,
        in_onboarding: bool = True,
    ) -> None:
        self.type: OnboardingPromptType = try_enum(OnboardingPromptType, type)
        self.title: str = title
        self.options: List[PartialOnboardingPromptOption] = options
        self.single_select: bool = single_select
        self.required: bool = required
        self.in_onboarding: bool = in_onboarding

    def _to_dict(self, *, id: int = MISSING) -> PromptData:
        base = {
            'type': self.type.value,
            'title': self.title,
            'options': [option._to_dict() for option in self.options],
            'single_select': self.single_select,
            'required': self.required,
            'in_onboarding': self.in_onboarding,
        }
        if id is not MISSING:
            base['id'] = id
        else:
            base['id'] = 0
        return base


class OnboardingPrompt(PartialOnboardingPrompt, Hashable):
    """Represents an onboarding prompt.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the prompt.
    guild: :class:`Guild`
        The guild that the prompt belongs to.
    type: :class:`OnboardingPromptType`
        The type of the prompt.
    title: :class:`str`
        The title of the prompt.
    options: List[:class:`OnboardingPromptOption`]
        The options available to select from in the prompt.
    single_select: :class:`bool`
        Whether users can only select one option in the prompt.
    in_onboarding: :class:`bool`
        Whether the prompt is in the onboarding flow.
    """

    options: List[OnboardingPromptOption]

    __slots__ = (
        '_state',
        'guild',
        'id',
        'type',
        'title',
        'options',
        'single_select',
        'required',
        'in_onboarding',
    )

    def __init__(self, *, data: PromptData, state: ConnectionState, guild: Guild) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self.id: int = int(data['id'])
        super().__init__(
            type=try_enum(OnboardingPromptType, data['type']),
            title=data['title'],
            options=[OnboardingPromptOption(data=option, state=state, guild=guild) for option in data['options']],
            single_select=data['single_select'],
            required=data['required'],
            in_onboarding=data['in_onboarding'],
        )

    def __repr__(self) -> str:
        return f'<OnboardingPrompt id={self.id} title={self.title!r}>'

    def _to_dict(self) -> PromptData:
        return super()._to_dict(id=self.id)


class Onboarding:
    """Represents a guilds onboarding configuration.

    .. versionadded:: 2.0

    Attributes
    ----------
    guild: :class:`Guild`
        The guild that the onboarding configuration belongs to.
    prompts: List[:class:`OnboardingPrompt`]
        The list of prompts shown during onboarding flow and in the customize community (Channel & Roles) tab.
    default_channel_ids: Set[:class:`int`]
        The IDs of the channels that are added to the users channel list by default.
    enabled: :class:`bool`
        Whether onboarding is enabled for the guild.
    mode: :class:`OnboardingMode`
        The onboarding mode for the guild.
    """

    __slots__ = (
        '_state',
        '_cs_default_channels',
        'guild',
        'prompts',
        'default_channel_ids',
        'enabled',
        'mode',
    )

    def __init__(self, *, data: OnboardingData, state: ConnectionState, guild: Guild) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self.default_channel_ids: Set[int] = set(map(int, data['default_channel_ids']))
        self.prompts: List[OnboardingPrompt] = [
            OnboardingPrompt(data=prompt, state=state, guild=guild) for prompt in data['prompts']
        ]
        self.enabled: bool = data['enabled']
        self.mode: OnboardingMode = try_enum(OnboardingMode, data['mode'])

    def __repr__(self) -> str:
        return f'<Onboarding guild={self.guild!r} enabled={self.enabled}>'

    @cached_slot_property('_cs_default_channels')
    def default_channels(self) -> List[Union[GuildChannel, ThreadChannel]]:
        """List[Union[:class:`abc.GuildChannel`, :class:`ThreadChannel`]]: The list of channels
        that are added to the users channel list by default."""
        return utils._unique(filter(None, map(self.guild.get_channel, self.default_channel_ids)))  # type: ignore
