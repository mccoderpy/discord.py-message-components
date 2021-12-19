# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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
import datetime
import re
import inspect
import typing

import discord

from .errors import *

__all__ = (
    'Converter',
    'MemberConverter',
    'UserConverter',
    'MessageConverter',
    'PartialMessageConverter',
    'TextChannelConverter',
    'InviteConverter',
    'GuildConverter',
    'RoleConverter',
    'GameConverter',
    'ColourConverter',
    'ColorConverter',
    'VoiceChannelConverter',
    'StageChannelConverter',
    'EmojiConverter',
    'PartialEmojiConverter',
    'StickerConverter',
    'CategoryChannelConverter',
    'IDConverter',
    'StoreChannelConverter',
    'clean_content',
    'Greedy',
)

def _get_from_guilds(bot, getter, argument):
    result = None
    for guild in bot.guilds:
        result = getattr(guild, getter)(argument)
        if result:
            return result
    return result

_utils_get = discord.utils.get

class Converter:
    """The base class of custom converters that require the :class:`.Context`
    to be passed to be useful.

    This allows you to implement converters that function similar to the
    special cased ``discord`` classes.

    Classes that derive from this should override the :meth:`~.Converter.convert`
    method to do its conversion logic. This method must be a :ref:`coroutine <coroutine>`.
    """

    async def convert(self, ctx, argument):
        """|coro|

        The method to override to do conversion logic.

        If an error is found while converting, it is recommended to
        raise a :exc:`.CommandError` derived exception as it will
        properly propagate to the error handlers.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context that the argument is being used in.
        argument: :class:`str`
            The argument that is being converted.

        Raises
        -------
        :exc:`.CommandError`
            A generic exception occurred when converting the argument.
        :exc:`.BadArgument`
            The converter failed to convert the argument.
        """
        raise NotImplementedError('Derived classes need to implement this.')

class IDConverter(Converter):
    def __init__(self):
        self._id_regex = re.compile(r'([0-9]{15,20})$')
        super().__init__()

    def _get_id_match(self, argument):
        return self._id_regex.match(argument)

class MemberConverter(IDConverter):
    """Converts to a :class:`~discord.Member`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name#discrim
    4. Lookup by name
    5. Lookup by nickname

    .. versionchanged:: 1.5
         Raise :exc:`.MemberNotFound` instead of generic :exc:`.BadArgument`

    .. versionchanged:: 1.5.1
        This converter now lazily fetches members from the gateway and HTTP APIs,
        optionally caching the result if :attr:`.MemberCacheFlags.joined` is enabled.
    """

    async def query_member_named(self, guild, argument):
        cache = guild._state.member_cache_flags.joined
        if len(argument) > 5 and argument[-5] == '#':
            username, _, discriminator = argument.rpartition('#')
            members = await guild.query_members(username, limit=100, cache=cache)
            return discord.utils.get(members, name=username, discriminator=discriminator)
        else:
            members = await guild.query_members(argument, limit=100, cache=cache)
            return discord.utils.find(lambda m: m.name == argument or m.nick == argument, members)

    async def query_member_by_id(self, bot, guild, user_id):
        ws = bot._get_websocket(shard_id=guild.shard_id)
        cache = guild._state.member_cache_flags.joined
        if ws.is_ratelimited():
            # If we're being rate limited on the WS, then fall back to using the HTTP APIMethodes
            # So we don't have to wait ~60 seconds for the query to finish
            try:
                member = await guild.fetch_member(user_id)
            except discord.HTTPException:
                return None

            if cache:
                guild._add_member(member)
            return member

        # If we're not being rate limited then we can use the websocket to actually query
        members = await guild.query_members(limit=1, user_ids=[user_id], cache=cache)
        if not members:
            return None
        return members[0]

    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)
        guild = ctx.guild
        result = None
        user_id = None
        if match is None:
            # not a mention...
            if guild:
                result = guild.get_member_named(argument)
            else:
                result = _get_from_guilds(bot, 'get_member_named', argument)
        else:
            user_id = int(match.group(1))
            if guild:
                result = guild.get_member(user_id) or _utils_get(ctx.message.mentions, id=user_id)
            else:
                result = _get_from_guilds(bot, 'get_member', user_id)

        if result is None:
            if guild is None:
                raise MemberNotFound(argument)

            if user_id is not None:
                result = await self.query_member_by_id(bot, guild, user_id)
            else:
                result = await self.query_member_named(guild, argument)

            if not result:
                raise MemberNotFound(argument)

        return result

class UserConverter(IDConverter):
    """Converts to a :class:`~discord.User`.

    All lookups are via the global user cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name#discrim
    4. Lookup by name

    .. versionchanged:: 1.5
         Raise :exc:`.UserNotFound` instead of generic :exc:`.BadArgument`

    .. versionchanged:: 1.6
        This converter now lazily fetches users from the HTTP APIs if an ID is passed
        and it's not available in cache.
    """
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)
        result = None
        state = ctx._state

        if match is not None:
            user_id = int(match.group(1))
            result = ctx.bot.get_user(user_id) or _utils_get(ctx.message.mentions, id=user_id)
            if result is None:
                try:
                    result = await ctx.bot.fetch_user(user_id)
                except discord.HTTPException:
                    raise UserNotFound(argument) from None

            return result

        arg = argument

        # Remove the '@' character if this is the first character from the argument
        if arg[0] == '@':
            # Remove first character
            arg = arg[1:]

        # check for discriminator if it exists,
        if len(arg) > 5 and arg[-5] == '#':
            discrim = arg[-4:]
            name = arg[:-5]
            predicate = lambda u: u.name == name and u.discriminator == discrim
            result = discord.utils.find(predicate, state._users.values())
            if result is not None:
                return result

        predicate = lambda u: u.name == arg
        result = discord.utils.find(predicate, state._users.values())

        if result is None:
            raise UserNotFound(argument)

        return result

class PartialMessageConverter(Converter):
    """Converts to a :class:`discord.PartialMessage`.

    .. versionadded:: 1.7

    The creation strategy is as follows (in order):

    1. By "{channel ID}-{message ID}" (retrieved by shift-clicking on "Copy ID")
    2. By message ID (The message is assumed to be in the context channel.)
    3. By message URL
    """
    def _get_id_matches(self, argument):
        id_regex = re.compile(r'(?:(?P<channel_id>[0-9]{15,20})-)?(?P<message_id>[0-9]{15,20})$')
        link_regex = re.compile(
            r'https?://(?:(ptb|canary|www)\.)?discord(?:app)?\.com/channels/'
            r'(?:[0-9]{15,20}|@me)'
            r'/(?P<channel_id>[0-9]{15,20})/(?P<message_id>[0-9]{15,20})/?$'
        )
        match = id_regex.match(argument) or link_regex.match(argument)
        if not match:
            raise MessageNotFound(argument)
        channel_id = match.group("channel_id")
        return int(match.group("message_id")), int(channel_id) if channel_id else None

    async def convert(self, ctx, argument):
        message_id, channel_id = self._get_id_matches(argument)
        channel = ctx.bot.get_channel(channel_id) if channel_id else ctx.channel
        if not channel:
            raise ChannelNotFound(channel_id)
        return discord.PartialMessage(channel=channel, id=message_id)

class MessageConverter(PartialMessageConverter):
    """Converts to a :class:`discord.Message`.

    .. versionadded:: 1.1

    The lookup strategy is as follows (in order):

    1. Lookup by "{channel ID}-{message ID}" (retrieved by shift-clicking on "Copy ID")
    2. Lookup by message ID (the message **must** be in the context channel)
    3. Lookup by message URL

    .. versionchanged:: 1.5
         Raise :exc:`.ChannelNotFound`, :exc:`.MessageNotFound` or :exc:`.ChannelNotReadable` instead of generic :exc:`.BadArgument`
    """
    async def convert(self, ctx, argument):
        message_id, channel_id = self._get_id_matches(argument)
        message = ctx.bot._connection._get_message(message_id)
        if message:
            return message
        channel = ctx.bot.get_channel(channel_id) if channel_id else ctx.channel
        if not channel:
            raise ChannelNotFound(channel_id)
        try:
            return await channel.fetch_message(message_id)
        except discord.NotFound:
            raise MessageNotFound(argument)
        except discord.Forbidden:
            raise ChannelNotReadable(channel)

class TextChannelConverter(IDConverter):
    """Converts to a :class:`~discord.TextChannel`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name

    .. versionchanged:: 1.5
         Raise :exc:`.ChannelNotFound` instead of generic :exc:`.BadArgument`
    """
    async def convert(self, ctx, argument):
        bot = ctx.bot

        match = self._get_id_match(argument) or re.match(r'<#([0-9]+)>$', argument)
        result = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                result = discord.utils.get(guild.text_channels, name=argument)
            else:
                def check(c):
                    return isinstance(c, discord.TextChannel) and c.name == argument
                result = discord.utils.find(check, bot.get_all_channels())
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, discord.TextChannel):
            raise ChannelNotFound(argument)

        return result

class ThreadChannelConverter(IDConverter):
    async def convert(self, ctx, argument):
        bot = ctx.bot

        match = self._get_id_match(argument) or re.match(r'<#([0-9]+)>$', argument)
        result = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                result = discord.utils.get(guild.thread_channels, name=argument)
            else:
                def check(c):
                    return isinstance(c, discord.ThreadChannel) and c.name == argument
                result = discord.utils.find(check, bot.get_all_channels())
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, discord.ThreadChannel):
            raise ChannelNotFound(argument)

        return result

class VoiceChannelConverter(IDConverter):
    """Converts to a :class:`~discord.VoiceChannel`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name

    .. versionchanged:: 1.5
         Raise :exc:`.ChannelNotFound` instead of generic :exc:`.BadArgument`
    """
    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r'<#([0-9]+)>$', argument)
        result = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                result = discord.utils.get(guild.voice_channels, name=argument)
            else:
                def check(c):
                    return isinstance(c, discord.VoiceChannel) and c.name == argument
                result = discord.utils.find(check, bot.get_all_channels())
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, discord.VoiceChannel):
            raise ChannelNotFound(argument)

        return result

class StageChannelConverter(IDConverter):
    """Converts to a :class:`~discord.StageChannel`.

    .. versionadded:: 1.7

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name
    """
    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r'<#([0-9]+)>$', argument)
        result = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                result = discord.utils.get(guild.stage_channels, name=argument)
            else:
                def check(c):
                    return isinstance(c, discord.StageChannel) and c.name == argument
                result = discord.utils.find(check, bot.get_all_channels())
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, discord.StageChannel):
            raise ChannelNotFound(argument)

        return result

class CategoryChannelConverter(IDConverter):
    """Converts to a :class:`~discord.CategoryChannel`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name

    .. versionchanged:: 1.5
         Raise :exc:`.ChannelNotFound` instead of generic :exc:`.BadArgument`
    """
    async def convert(self, ctx, argument):
        bot = ctx.bot

        match = self._get_id_match(argument) or re.match(r'<#([0-9]+)>$', argument)
        result = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                result = discord.utils.get(guild.categories, name=argument)
            else:
                def check(c):
                    return isinstance(c, discord.CategoryChannel) and c.name == argument
                result = discord.utils.find(check, bot.get_all_channels())
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, discord.CategoryChannel):
            raise ChannelNotFound(argument)

        return result

class StoreChannelConverter(IDConverter):
    """Converts to a :class:`~discord.StoreChannel`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name.

    .. versionadded:: 1.7
    """

    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r'<#([0-9]+)>$', argument)
        result = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                result = discord.utils.get(guild.channels, name=argument)
            else:
                def check(c):
                    return isinstance(c, discord.StoreChannel) and c.name == argument
                result = discord.utils.find(check, bot.get_all_channels())
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, discord.StoreChannel):
            raise ChannelNotFound(argument)

        return result

class ColourConverter(Converter):
    """Converts to a :class:`~discord.Colour`.

    .. versionchanged:: 1.5
        Add an alias named ColorConverter

    The following formats are accepted:

    - ``0x<hex>``
    - ``#<hex>``
    - ``0x#<hex>``
    - ``rgb(<number>, <number>, <number>)``
    - Any of the ``classmethod`` in :class:`Colour`

        - The ``_`` in the name can be optionally replaced with spaces.

    Like CSS, ``<number>`` can be either 0-255 or 0-100% and ``<hex>`` can be
    either a 6 digit hex number or a 3 digit hex shortcut (e.g. #fff).

    .. versionchanged:: 1.5
         Raise :exc:`.BadColourArgument` instead of generic :exc:`.BadArgument`

    .. versionchanged:: 1.7
        Added support for ``rgb`` function and 3-digit hex shortcuts
    """

    RGB_REGEX = re.compile(r'rgb\s*\((?P<r>[0-9]{1,3}%?)\s*,\s*(?P<g>[0-9]{1,3}%?)\s*,\s*(?P<b>[0-9]{1,3}%?)\s*\)')

    def parse_hex_number(self, argument):
        arg = ''.join(i * 2 for i in argument) if len(argument) == 3 else argument
        try:
            value = int(arg, base=16)
            if not (0 <= value <= 0xFFFFFF):
                raise BadColourArgument(argument)
        except ValueError:
            raise BadColourArgument(argument)
        else:
            return discord.Color(value=value)

    def parse_rgb_number(self, argument, number):
        if number[-1] == '%':
            value = int(number[:-1])
            if not (0 <= value <= 100):
                raise BadColourArgument(argument)
            return round(255 * (value / 100))

        value = int(number)
        if not (0 <= value <= 255):
            raise BadColourArgument(argument)
        return value

    def parse_rgb(self, argument, *, regex=RGB_REGEX):
        match = regex.match(argument)
        if match is None:
            raise BadColourArgument(argument)

        red = self.parse_rgb_number(argument, match.group('r'))
        green = self.parse_rgb_number(argument, match.group('g'))
        blue = self.parse_rgb_number(argument, match.group('b'))
        return discord.Color.from_rgb(red, green, blue)

    async def convert(self, ctx, argument):
        if argument[0] == '#':
            return self.parse_hex_number(argument[1:])

        if argument[0:2] == '0x':
            rest = argument[2:]
            # Legacy backwards compatible syntax
            if rest.startswith('#'):
                return self.parse_hex_number(rest[1:])
            return self.parse_hex_number(rest)

        arg = argument.lower()
        if arg[0:3] == 'rgb':
            return self.parse_rgb(arg)

        arg = arg.replace(' ', '_')
        method = getattr(discord.Colour, arg, None)
        if arg.startswith('from_') or method is None or not inspect.ismethod(method):
            raise BadColourArgument(arg)
        return method()

ColorConverter = ColourConverter

class RoleConverter(IDConverter):
    """Converts to a :class:`~discord.Role`.

    All lookups are via the local guild. If in a DM context, the converter raises
    :exc:`.NoPrivateMessage` exception.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name

    .. versionchanged:: 1.5
         Raise :exc:`.RoleNotFound` instead of generic :exc:`.BadArgument`
    """
    async def convert(self, ctx, argument):
        guild = ctx.guild
        if not guild:
            raise NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(r'<@&([0-9]+)>$', argument)
        if match:
            result = guild.get_role(int(match.group(1)))
        else:
            result = discord.utils.get(guild._roles.values(), name=argument)

        if result is None:
            raise RoleNotFound(argument)
        return result

class GameConverter(Converter):
    """Converts to :class:`~discord.Game`."""
    async def convert(self, ctx, argument):
        return discord.Game(name=argument)

class InviteConverter(Converter):
    """Converts to a :class:`~discord.Invite`.

    This is done via an HTTP request using :meth:`.Bot.fetch_invite`.

    .. versionchanged:: 1.5
         Raise :exc:`.BadInviteArgument` instead of generic :exc:`.BadArgument`
    """
    async def convert(self, ctx, argument):
        try:
            invite = await ctx.bot.fetch_invite(argument)
            return invite
        except Exception as exc:
            raise BadInviteArgument() from exc

class GuildConverter(IDConverter):
    """Converts to a :class:`~discord.Guild`.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by name. (There is no disambiguation for Guilds with multiple matching names).

    .. versionadded:: 1.7
    """

    async def convert(self, ctx, argument):
        match = self._get_id_match(argument)
        result = None

        if match is not None:
            guild_id = int(match.group(1))
            result = ctx.bot.get_guild(guild_id)

        if result is None:
            result = discord.utils.get(ctx.bot.guilds, name=argument)

            if result is None:
                raise GuildNotFound(argument)
        return result

class EmojiConverter(IDConverter):
    """Converts to a :class:`~discord.Emoji`.

    All lookups are done for the local guild first, if available. If that lookup
    fails, then it checks the client's global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by extracting ID from the emoji.
    3. Lookup by name

    .. versionchanged:: 1.5
         Raise :exc:`.EmojiNotFound` instead of generic :exc:`.BadArgument`
    """
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r'<a?:[a-zA-Z0-9\_]+:([0-9]+)>$', argument)
        result = None
        bot = ctx.bot
        guild = ctx.guild

        if match is None:
            # Try to get the emoji by name. Try local guild first.
            if guild:
                result = discord.utils.get(guild.emojis, name=argument)

            if result is None:
                result = discord.utils.get(bot.emojis, name=argument)
        else:
            emoji_id = int(match.group(1))

            # Try to look up emoji by id.
            if guild:
                result = discord.utils.get(guild.emojis, id=emoji_id)

            if result is None:
                result = discord.utils.get(bot.emojis, id=emoji_id)

        if result is None:
            raise EmojiNotFound(argument)

        return result

class PartialEmojiConverter(Converter):
    """Converts to a :class:`~discord.PartialEmoji`.

    This is done by extracting the animated flag, name and ID from the emoji.

    .. versionchanged:: 1.5
         Raise :exc:`.PartialEmojiConversionFailure` instead of generic :exc:`.BadArgument`
    """
    async def convert(self, ctx, argument):
        match = re.match(r'<(a?):([a-zA-Z0-9\_]+):([0-9]+)>$', argument)

        if match:
            emoji_animated = bool(match.group(1))
            emoji_name = match.group(2)
            emoji_id = int(match.group(3))

            return discord.PartialEmoji.with_state(ctx.bot._connection, animated=emoji_animated, name=emoji_name,
                                                   id=emoji_id)

        raise PartialEmojiConversionFailure(argument)


class StickerConverter(IDConverter):
    """Converts to a :class:`~discord.Sticker`.

    All lookups are done for the local guild first, if available. If that lookup
    fails, then it checks the client's global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by name.
    2. Lookup by ID.
    """
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument)
        result = None
        bot = ctx.bot
        guild = ctx.guild

        if match is None:
            # Try to get the sticker by name. Try local guild first.
            if guild:
                result = discord.utils.get(guild.stickers, name=argument)

            if result is None:
                result = discord.utils.get(bot.stickers, name=argument)
        else:
            sticker_id = int(match.group(1))

            # Try to look up sticker by id.
            if guild:
                result = discord.utils.get(guild.stickers, id=sticker_id)

            if result is None:
                result = discord.utils.get(bot.stickers, id=sticker_id)

        if result is None:
            raise StickerNotFound(argument)

        return result


class datetimeConverter(Converter):
    """Converts to a :class:`datetime.datetime`. Made by mccuber04#2960

    Valid formats for the time(``H`` = hour | ``M`` = minute | ``S`` = second):
        ``HH:MM:SS``,
        ``HH:MM``

        Each value can also be specified as a single digit.

        All ``:`` could be ``-`` too.

    Valid formats for the date(``d`` = day | ``m`` = month | ``y`` = year):
        ``dd.mm.yyyy``,
        ``dd.mm``,
        ``dd``,
        ``yyyy``
        ``mm.yyyy``

        Each value for day and month can also be specified as a single digit.

        All ``.`` could be ``,``, ``-`` and ``/`` too.

    .. note::
        Values that are not specified are filled with those of the current time.

        If you want to pass a time in 12h-format that is in the afternoon,
        the ``pm`` must be after the time like ``08:42 pm 04.10.2022``.
    """
    time_regex = re.compile(
        r'(?P<hour>'  # group for hour value
        r'0?[0-9]'  # 0 to 9
        r'|'  # or
        r'1[0-9]'  # 10 to 19
        r'|'  # or
        r'2[0-3]'  # 20 to 23
        r')'
        r'[:\-]'  # brake could be : or -
        r'(?P<minute>'  # group for minute value
        r'[1-5][0-9]'  # 10 to 59
        r'|'  # or
        r'0?[0-9]'  # 0 to 9
        r')'
        r'('  # group for brake and second
        r'[:\-]'  # brake could be : or -
        r'(?P<second>'  # group for second value
        r'[1-5][0-9]'  # 10 to 59
        r'|'  # or
        r'[0-9]'  # 0 to 9
        r')'
        r')?'  # mark the brake and second group as optional
        r' ?' # a optional whitespace
        r'(?P<am_or_pm>'  # group for am or pm value if it is in 12h-format
        r'am' # am for ante mediteran (Morning), would be ignored
        r'|'  # or
        r'pm'  # pm for post mediteran (afternoon)
        r')'
    )
    date_regex = re.compile(
        r'(?P<day>'  # group for day value
        r'3[0-1]'  # 31. or 30.
        r'|'  # or
        r'[1-2][0-9]'  # 10. to 29.
        r'|'  # or
        r'0?[1-9]'  # 1. to 9.
        r')?'  # mark the day as optional
        r'('  # group for brake and month
        r'[.,\-/]'  # brake could be . or , or - or /
        r'(?P<month>'  # group for month value
        r'1[0-2]'  # october to december
        r'|'  # or
        r'0?[1-9]'  # january to september
        r')'
        r')?'  # mark the brake and month group as optional 
        r'('  # group for brake and year
        r'[.,\-/]'  # brake could be . or , or - or /
        r'(?P<year>'  # group for year value
        r'[1-9][0-9]{3}'  # any year from 1000 to 9999 in format yyyy
        r'|'  # or
        r'[0-9]{2}'   # any year from 2000 to 2099 in format YY (20YY)
        r')'
        r'(\s|$)' # to be shure that "1996telefon" is not valid there should be a whitespace or the end of the string after the year
        r')?'  # mark the brake and year group as optional
    )

    async def convert(self, ctx, argument) -> datetime.datetime:
        argument = argument.lower().rstrip()

        now = datetime.datetime.utcnow()  # to set defaults for non provided parts
        invalid = False

        date = self.date_regex.search(argument)

        if date and any(date.groups()):
            day = int(date.group('day') or now.day)
            month = int(date.group('month') or now.month)
            year = date.group('year')

            if year and len(year) == 2: # it is in YY (20YY) format, convert it to a full year (yyyy)
                year = '20' + year

            year = int(year or now.year)
            # to make something like ``10.2022`` also valid
            if date.group('day') and not date.group('month'):
                month = day
                day = now.day
        else:
            invalid = True
            day, month, year = now.day, now.month, now.year

        time = self.time_regex.search(argument)

        if time and any(time.groups()):
            invalid = False
            pm = bool(time.group('am_or_pm') == 'pm')
            hour = int(time.group('hour') or now.hour)
            # if it is in 12-hour format and pm, just increase it by 12 so that it is in 24-hour format
            if pm and hour <= 12:
                hour += 12
            minute = int(time.group('minute') or now.minute)
            second = int(time.group('second') or now.second)

        else:
            # set the time to the current if no time provided
            hour, minute, second = now.hour, now.minute, now.second

        if invalid:
            raise DatetimeConversionFailure(argument)

        try:
            result = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        except Exception as exc:
            raise DatetimeConversionFailure(argument, original_exception=exc)
        else:
            return result


class clean_content(Converter):
    """Converts the argument to mention scrubbed version of
    said content.

    This behaves similarly to :attr:`~discord.Message.clean_content`.

    Attributes
    ------------
    fix_channel_mentions: :class:`bool`
        Whether to clean channel mentions.
    use_nicknames: :class:`bool`
        Whether to use nicknames when transforming mentions.
    escape_markdown: :class:`bool`
        Whether to also escape special markdown characters.
    remove_markdown: :class:`bool`
        Whether to also remove special markdown characters. This option is not supported with ``escape_markdown``

        .. versionadded:: 1.7
    """
    def __init__(self, *, fix_channel_mentions=False, use_nicknames=True, escape_markdown=False, remove_markdown=False):
        self.fix_channel_mentions = fix_channel_mentions
        self.use_nicknames = use_nicknames
        self.escape_markdown = escape_markdown
        self.remove_markdown = remove_markdown

    async def convert(self, ctx, argument):
        message = ctx.message
        transformations = {}

        if self.fix_channel_mentions and ctx.guild:
            def resolve_channel(id, *, _get=ctx.guild.get_channel):
                ch = _get(id)
                return ('<#%s>' % id), ('#' + ch.name if ch else '#deleted-channel')

            transformations.update(resolve_channel(channel) for channel in message.raw_channel_mentions)

        if self.use_nicknames and ctx.guild:
            def resolve_member(id, *, _get=ctx.guild.get_member):
                m = _get(id)
                return '@' + m.display_name if m else '@deleted-user'
        else:
            def resolve_member(id, *, _get=ctx.bot.get_user):
                m = _get(id)
                return '@' + m.name if m else '@deleted-user'


        transformations.update(
            ('<@%s>' % member_id, resolve_member(member_id))
            for member_id in message.raw_mentions
        )

        transformations.update(
            ('<@!%s>' % member_id, resolve_member(member_id))
            for member_id in message.raw_mentions
        )

        if ctx.guild:
            def resolve_role(_id, *, _find=ctx.guild.get_role):
                r = _find(_id)
                return '@' + r.name if r else '@deleted-role'

            transformations.update(
                ('<@&%s>' % role_id, resolve_role(role_id))
                for role_id in message.raw_role_mentions
            )

        def repl(obj):
            return transformations.get(obj.group(0), '')

        pattern = re.compile('|'.join(transformations.keys()))
        result = pattern.sub(repl, argument)

        if self.escape_markdown:
            result = discord.utils.escape_markdown(result)
        elif self.remove_markdown:
            result = discord.utils.remove_markdown(result)

        # Completely ensure no mentions escape:
        return discord.utils.escape_mentions(result)

class _Greedy:
    __slots__ = ('converter',)

    def __init__(self, *, converter=None):
        self.converter = converter

    def __getitem__(self, params):
        if not isinstance(params, tuple):
            params = (params,)
        if len(params) != 1:
            raise TypeError('Greedy[...] only takes a single argument')
        converter = params[0]

        if not (callable(converter) or isinstance(converter, Converter) or hasattr(converter, '__origin__')):
            raise TypeError('Greedy[...] expects a type or a Converter instance.')

        if converter is str or converter is type(None) or converter is _Greedy:
            raise TypeError('Greedy[%s] is invalid.' % converter.__name__)

        if getattr(converter, '__origin__', None) is typing.Union and type(None) in converter.__args__:
            raise TypeError('Greedy[%r] is invalid.' % converter)

        return self.__class__(converter=converter)

Greedy = _Greedy()
