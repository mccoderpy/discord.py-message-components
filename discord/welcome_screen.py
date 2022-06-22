from typing import Optional, List, Union, TYPE_CHECKING

from .partial_emoji import PartialEmoji

if TYPE_CHECKING:
    from .abc import GuildChannel

__all__ = (
    'WelcomeScreenChannel',
    'WelcomeScreen'
)


class WelcomeScreenChannel:
    r"""Represents a channel shown in a welcome screen.

    Attributes
    -----------
    channel: :class:`~discord.Snowflake`
        The channel the welcome screen channel belongs to
    description: :class:`str`
        The description of the welcome screen channel
    emoji: Optional[:class:`~discord.PartialEmoji`]
        The emoji that is shown on the left side of the welcome screen channel
    """
    def __init__(self, channel: 'GuildChannel', description: str = None, emoji: Optional[Union[PartialEmoji, str]] = None):
        """
        Represents a channel shown in a welcome screen.

        Parameters
        -----------
        channel: :class:`~discord.Snowflake`
            The channel the welcome screen channel belongs to
        description: :class:`str`
            The description of the welcome screen channel
        emoji: Optional[Union[:class:`~discord.PartialEmoji`, :class:`str`]
            The emoji that is shown on the left side of the welcome screen channel
        """
        try:
            self._state = channel._state
        except AttributeError:
            pass
        self.channel = channel
        self.description: Optional[str] = description
        if emoji and isinstance(emoji, str):
            emoji = PartialEmoji.from_string(emoji)
        self.emoji: Optional[PartialEmoji] = emoji

    @classmethod
    def _from_data(cls, state, guild, data):
        channel = guild.get_channel(int(data['channel_id']))
        description = data.get('description', None)
        custom_emoji = data.get('emoji_id', None)
        if custom_emoji:
            emoji = state.get_emoji(int(custom_emoji))
        else:
            emoji_name = data.get('emoji_name', None)
            if emoji_name:
                emoji = PartialEmoji(name=emoji_name)
            else:
                emoji = None
        return cls(channel=channel, description=description, emoji=emoji)

    def to_dict(self):
        base = {'channel_id': str(self.channel.id)}
        if self.description:
            base['description'] = str(self.description)
        if self.emoji:
            base['emoji_name'] = self.emoji.name
            if self.emoji.id:
                base['emoji_id'] = self.emoji.id
        return base


class WelcomeScreen:
    """
    Represents a welcome screen for a guild returned by :meth:`~Guild.welcome_screen`.

    .. warning::
        Do not initialize this class directly. Use :meth:`~Guild.welcome_screen` instead.

    Attributes
    -----------
    guild: :class:`~discord.Guild`
        The guild the welcome screen belongs to
    description: :class:`str`
        The description of the welcome screen
    welcome_channels: List[:class:`WelcomeScreenChannel`]
    """
    def __init__(self, state, guild, data):
        self._state = state
        self.guild = guild
        self.description = data.get('description', None)
        self.welcome_channels = [WelcomeScreenChannel._from_data(state=state, guild=guild, data=c) for c in data.get('welcome_channels', [])]

    def _update(self, data):
        self.description = data.get('description', self.description)
        self.welcome_channels = [WelcomeScreenChannel._from_data(state=self._state, guild=self.guild, data=c) for c in data.get('welcome_channels', [])]

    async def edit(self, *, reason: str = None, **fields):
        try:
            enabled: bool = fields['enabled']
        except KeyError:
            pass
        else:
            if enabled is not None:
                fields['enabled'] = bool(enabled)

        try:
            welcome_channels: Optional[List[WelcomeScreenChannel]] = fields['welcome_channels']
        except KeyError:
            pass
        else:
            if welcome_channels is not None:
                fields['welcome_channels'] = [wc.to_dict() for wc in welcome_channels]

        try:
            description: Optional[str] = fields['description']
        except KeyError:
            pass
        else:
            if description is not None:
                fields['description'] = str(description)
        data = await self._state.http.edit_welcome_screen(guild_id=self.guild.id, reason=reason, **fields)
        self._update(data)
        return self
