# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz & (c) 2021.present mccoderpy

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
    Union,
    Optional,
    Iterable,
    Callable,
    TypeVar,
    TYPE_CHECKING
)

import os
import re
import sys
import json
import array
import asyncio
import logging
import colorama
import collections.abc
import unicodedata
from base64 import b64encode
from bisect import bisect_left
import datetime
from .enums import TimestampStyle
import functools
from inspect import isawaitable as _isawaitable, signature as _signature
from operator import attrgetter


import warnings

from .errors import InvalidArgument

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, Self

    from .guild import Guild
    from .channel import VoiceChannel
    from .permissions import Permissions

    P = ParamSpec('P')


T = TypeVar('T')

DISCORD_EPOCH = 1420070400000
MAX_ASYNCIO_SECONDS = 3456000

colorama.init()


class _MISSING:
    """
    A placeholder object for missing attributes.
    """
    __slots__ = ()

    def __repr__(self):
        return 'MISSING'

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other) -> bool:
        return False

    def __hash__(self):
        return 0


MISSING = _MISSING()


class cached_property:
    def __init__(self, function):
        self.function = function
        self.__doc__ = getattr(function, '__doc__')

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = self.function(instance)
        setattr(instance, self.function.__name__, value)

        return value


class CachedSlotProperty:
    def __init__(self, name, function):
        self.name = name
        self.function = function
        self.__doc__ = getattr(function, '__doc__')

    def __get__(self, instance, owner):
        if instance is None:
            return self

        try:
            return getattr(instance, self.name)
        except AttributeError:
            value = self.function(instance)
            setattr(instance, self.name, value)
            return value


def cached_slot_property(name):
    def decorator(func):
        return CachedSlotProperty(name, func)

    return decorator


class SequenceProxy(collections.abc.Sequence):
    """Read-only proxy of a Sequence."""
    def __init__(self, proxied):
        self.__proxied = proxied

    def __getitem__(self, idx):
        return self.__proxied[idx]

    def __len__(self):
        return len(self.__proxied)

    def __contains__(self, item):
        return item in self.__proxied

    def __iter__(self):
        return iter(self.__proxied)

    def __reversed__(self):
        return reversed(self.__proxied)

    def index(self, value, *args, **kwargs):
        return self.__proxied.index(value, *args, **kwargs)

    def count(self, value):
        return self.__proxied.count(value)


def parse_time(timestamp: str):
    if timestamp:
        return datetime.datetime(*map(int, re.split(r'\D', timestamp.replace('+00:00', ''))))
    return None


def copy_doc(original: Callable) -> Callable[[T], T]:
    def decorator(overriden: T) -> T:
        overriden.__doc__ = f'{overriden.__doc__}\n\n' if overriden.__doc__ else "" + original.__doc__
        overriden.__signature__ = _signature(original)
        return overriden
    return decorator


def deprecated(instead: Optional[str] = None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def actual_decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def decorated(*args: P.args, **kwargs: P.kwargs) -> T:
            warnings.simplefilter('always', DeprecationWarning)  # turn off filter
            deprecation_warning(func.__name__, instead)
            warnings.simplefilter('default', DeprecationWarning)  # reset filter
            return func(*args, **kwargs)
        return decorated
    return actual_decorator


def deprecation_warning(target: str, instead: Optional[str] = None) -> None:
    warnings.simplefilter('always', DeprecationWarning)  # turn off filter
    if instead:
        fmt = "{0} is deprecated, use {1} instead."
    else:
        fmt = '{0} is deprecated.'

    warnings.warn(fmt.format(target, instead), stacklevel=3, category=DeprecationWarning)
    warnings.simplefilter('default', DeprecationWarning)  # reset filter


def oauth_url(
        client_id: str,
        permissions: Optional[Permissions] = None,
        guild: Optional[Guild] = None,
        redirect_uri: Optional[str] = None,
        scopes: Iterable[str] = ('bot',)):
    """A helper function that returns the OAuth2 URL for inviting the bot
    into guilds.

    Parameters
    -----------
    client_id: :class:`str`
        The client ID for your bot.
    permissions: :class:`~discord.Permissions`
        The permissions you're requesting. If not given then you won't be requesting any
        permissions.
    guild: :class:`~discord.Guild`
        The guild to pre-select in the authorization screen, if available.
    redirect_uri: :class:`str`
        An optional valid redirect URI.
    scopes: Iterable[:class:`str`]
        An optional valid list of scopes. Defaults to ``('bot',)``.

        .. versionadded:: 1.7

    Returns
    --------
    :class:`str`
        The OAuth2 URL for inviting the bot into guilds.
    """
    url = 'https://discord.com/oauth2/authorize?client_id={}'.format(client_id)
    url = url + '&scope=' + '+'.join(scopes or ('bot',))
    if permissions is not None:
        url = url + '&permissions=' + str(permissions.value)
    if guild is not None:
        url = url + "&guild_id=" + str(guild.id)
    if redirect_uri is not None:
        from urllib.parse import urlencode
        url = url + "&response_type=code&" + urlencode({'redirect_uri': redirect_uri})
    return url


def utcnow() -> datetime.datetime:
    """:class:`datetime.datetime`: Returns a timezone aware :class:`datetime.datetime` object representing the current UTC time."""
    return datetime.datetime.now(datetime.timezone.utc)


def snowflake_time(id: int):
    """
    Parameters
    -----------
    id: :class:`int`
        The snowflake ID.

    Returns
    --------
    :class:`datetime.datetime`
        The creation date in UTC of a Discord snowflake ID.
    """
    return datetime.datetime.utcfromtimestamp(((id >> 22) + DISCORD_EPOCH) / 1000)


def time_snowflake(datetime_obj, high=False):
    """
    Returns a numeric snowflake pretending to be created at the given date.

    When using as the lower end of a range, use ``time_snowflake(high=False) - 1`` to be inclusive, ``high=True`` to be exclusive
    When using as the higher end of a range, use ``time_snowflake(high=True)`` + 1 to be inclusive, ``high=False`` to be exclusive

    Parameters
    -----------
    datetime_obj: :class:`datetime.datetime`
        A timezone-naive datetime object representing UTC time.
    high: :class:`bool`
        Whether or not to set the lower 22 bit to high or low.
    """
    unix_seconds = (datetime_obj - type(datetime_obj)(1970, 1, 1)).total_seconds()
    discord_millis = int(unix_seconds * 1000 - DISCORD_EPOCH)

    return (discord_millis << 22) + (2**22-1 if high else 0)


def find(predicate, seq):
    """
    A helper to return the first element found in the sequence
    that meets the predicate. For example: ::

        member = discord.utils.find(lambda m: m.name == 'Mighty', channel.guild.members)

    would find the first :class:`~discord.Member` whose name is 'Mighty' and return it.
    If an entry is not found, then ``None`` is returned.

    This is different from :func:`py:filter` due to the fact it stops the moment it finds
    a valid entry.

    Parameters
    -----------
    predicate
        A function that returns a boolean-like result.
    seq: iterable
        The iterable to search through.
    """

    for element in seq:
        if predicate(element):
            return element
    return None


def get(iterable, **attrs):
    r"""A helper that returns the first element in the iterable that meets
    all the traits passed in ``attrs``. This is an alternative for
    :func:`~discord.utils.find`.

    When multiple attributes are specified, they are checked using
    logical AND, not logical OR. Meaning they have to meet every
    attribute passed in and not one of them.

    To have a nested attribute search (i.e. search by ``x.y``) then
    pass in ``x__y`` as the keyword argument.

    If nothing is found that matches the attributes passed, then
    ``None`` is returned.

    Examples
    ---------

    Basic usage:

    .. code-block:: python3

        member = discord.utils.get(message.guild.members, name='Foo')

    Multiple attribute matching:

    .. code-block:: python3

        channel = discord.utils.get(guild.voice_channels, name='Foo', bitrate=64000)

    Nested attribute matching:

    .. code-block:: python3

        channel = discord.utils.get(client.get_all_channels(), guild__name='Cool', name='general')

    Parameters
    -----------
    iterable
        An iterable to search through.
    \*\*attrs
        Keyword arguments that denote attributes to search with.
    """

    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace('__', '.'))
        for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [
        (attrget(attr.replace('__', '.')), value)
        for attr, value in attrs.items()
    ]

    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem

    return None


def styled_timestamp(
        timestamp: Union[datetime.datetime, int],
        style: Union[TimestampStyle, str] = TimestampStyle.short
) -> str:
    """
    A small function that returns a styled timestamp for discord, this will be displayed accordingly in the Discord client depending on the :attr:`style` specified.

    Timestamps will display the given timestamp in the user's timezone and locale.

    Parameters
    ----------
    timestamp: Union[:class:`datetime.datetime`, :class:`int`]
        The timestamp; A :class:`datetime.datetime` object or a unix timestamp as an :class:`int`.

    style: Optional[Union[:class:`~discord.TimestampStyle`, :class:`str`]]
        How the timestamp should be displayed in Discord; this can either be a :class:`~discord.TimestampStyle` or directly the associated value.

        :default: :attr:`~discord.TimestampStyle.short`

    Examples
    --------
    .. code-block:: python

        # Normal timestamp
        @client.command()
        async def time(ctx):
            await ctx.send(discord.utils.styled_timestamp(discord.utils.utcnow(), discord.TimestampStyle.long))

        # Relative timestamp
        @client.command()
        async def countdown(ctx, seconds: int):
            happens_in = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
            await ctx.send(f'Happens {discord.utils.styled_timestamp(happens_in, discord.TimestampStyle.relative)}')

    Raises
    -------
    AttributeError
        If the :attr:`style` is not a valid member of :class:`~discord.TimestampStyle`

    Returns
    -------
    :class:`str`
        The formatted timestamp.
    """
    unix_timestamp = int(timestamp.timestamp()) if isinstance(timestamp, datetime.datetime) else int(timestamp)
    style = TimestampStyle.from_value(style) if isinstance(style, str) else style
    if not isinstance(style, TimestampStyle):
        raise AttributeError('style has to be a discord.TimestampStyle')
    return f'<t:{unix_timestamp}:{str(style)}>'


async def create_voice_activity(channel: VoiceChannel, target_application_id: int, **kwargs):
    return await channel.create_invite(targe_type=2, target_application_id=target_application_id, **kwargs)


def _unique(iterable):
    seen = set()
    adder = seen.add
    return [x for x in iterable if not (x in seen or adder(x))]


def _get_as_snowflake(data, key):
    try:
        value = data[key]
    except KeyError:
        return None
    else:
        return value and int(value)


def _get_mime_type_for_image(data):
    if data.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
        return 'image/png'
    elif data[0:3] == b'\xff\xd8\xff' or data[6:10] in (b'JFIF', b'Exif'):
        return 'image/jpeg'
    elif data.startswith((b'\x47\x49\x46\x38\x37\x61', b'\x47\x49\x46\x38\x39\x61')):
        return 'image/gif'
    elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return 'image/webp'
    else:
        raise InvalidArgument('Unsupported image type given')


def _bytes_to_base64_data(data):
    fmt = 'data:{mime};base64,{data}'
    mime = _get_mime_type_for_image(data)
    b64 = b64encode(data).decode('ascii')
    return fmt.format(mime=mime, data=b64)


def to_json(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=True)


def _parse_ratelimit_header(request, *, use_clock=False):
    reset_after = request.headers.get('X-Ratelimit-Reset-After')
    if use_clock or not reset_after:
        utc = datetime.timezone.utc
        now = datetime.datetime.now(utc)
        reset = datetime.datetime.fromtimestamp(float(request.headers['X-Ratelimit-Reset']), utc)
        return (reset - now).total_seconds()
    else:
        return float(reset_after)


async def maybe_coroutine(f, *args, **kwargs):
    value = f(*args, **kwargs)
    if _isawaitable(value):
        return await value
    else:
        return value


async def async_all(gen, *, check=_isawaitable):
    for elem in gen:
        if check(elem):
            elem = await elem
        if not elem:
            return False
    return True

async def sane_wait_for(futures, *, timeout):
    ensured = [
        asyncio.ensure_future(fut) for fut in futures
    ]
    done, pending = await asyncio.wait(ensured, timeout=timeout, return_when=asyncio.ALL_COMPLETED)

    if len(pending) != 0:
        raise asyncio.TimeoutError()

    return done

async def sleep_until(when, result=None):
    """|coro|

    Sleep until a specified time.

    If the time supplied is in the past this function will yield instantly.

    .. versionadded:: 1.3

    Parameters
    -----------
    when: :class:`datetime.datetime`
        The timestamp in which to sleep until. If the datetime is naive then
        it is assumed to be in UTC.
    result: Any
        If provided is returned to the caller when the coroutine completes.
    """
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = (when - now).total_seconds()
    while delta > MAX_ASYNCIO_SECONDS:
        await asyncio.sleep(MAX_ASYNCIO_SECONDS)
        delta -= MAX_ASYNCIO_SECONDS
    return await asyncio.sleep(max(delta, 0), result)


def valid_icon_size(size):
    """Icons must be power of 2 within [16, 4096]."""
    return not size & (size - 1) and size in range(16, 4097)


class SnowflakeList(array.array):
    """Internal data storage class to efficiently store a list of snowflakes.

    This should have the following characteristics:

    - Low memory usage
    - O(n) iteration (obviously)
    - O(n log n) initial creation if data is unsorted
    - O(log n) search and indexing
    - O(n) insertion
    """

    __slots__ = ()

    def __new__(cls, data, *, is_sorted=False):
        return array.array.__new__(cls, 'Q', data if is_sorted else sorted(data))

    def add(self, element):
        i = bisect_left(self, element)
        self.insert(i, element)

    def get(self, element):
        i = bisect_left(self, element)
        return self[i] if i != len(self) and self[i] == element else None

    def has(self, element):
        i = bisect_left(self, element)
        return i != len(self) and self[i] == element


_IS_ASCII = re.compile(r'^[\x00-\x7f]+$')


def _string_width(string, *, _IS_ASCII=_IS_ASCII):
    """Returns string's width."""
    match = _IS_ASCII.match(string)
    if match:
        return match.endpos

    UNICODE_WIDE_CHAR_TYPE = 'WFA'
    func = unicodedata.east_asian_width
    return sum(2 if func(char) in UNICODE_WIDE_CHAR_TYPE else 1 for char in string)


def resolve_invite(invite):
    """
    Resolves an invite from a :class:`~discord.Invite`, URL or code.

    Parameters
    -----------
    invite: Union[:class:`~discord.Invite`, :class:`str`]
        The invite.

    Returns
    --------
    :class:`str`
        The invite code.
    """
    from .invite import Invite  # circular import
    if isinstance(invite, Invite):
        return invite.code
    else:
        rx = r'(?:https?\:\/\/)?discord(?:\.gg|(?:app)?\.com\/invite)\/(.+)'
        m = re.match(rx, invite)
        if m:
            return m.group(1)
    return invite


def resolve_template(code):
    """
    Resolves a template code from a :class:`~discord.Template`, URL or code.

    .. versionadded:: 1.4

    Parameters
    -----------
    code: Union[:class:`~discord.Template`, :class:`str`]
        The code.

    Returns
    --------
    :class:`str`
        The template code.
    """
    from .template import Template  # circular import
    if isinstance(code, Template):
        return code.code
    else:
        rx = r'(?:https?\:\/\/)?discord(?:\.new|(?:app)?\.com\/template)\/(.+)'
        m = re.match(rx, code)
        if m:
            return m.group(1)
    return code


_MARKDOWN_ESCAPE_SUBREGEX = '|'.join(r'\{0}(?=([\s\S]*((?<!\{0})\{0})))'.format(c)
                                     for c in ('*', '`', '_', '~', '|'))

_MARKDOWN_ESCAPE_COMMON = r'^>(?:>>)?\s|\[.+\]\(.+\)'

_MARKDOWN_ESCAPE_REGEX = re.compile(r'(?P<markdown>%s|%s)' % (_MARKDOWN_ESCAPE_SUBREGEX, _MARKDOWN_ESCAPE_COMMON), re.MULTILINE)

_URL_REGEX = r'(?P<url><[^: >]+:\/[^ >]+>|(?:https?|steam):\/\/[^\s<]+[^<.,:;\"\'\]\s])'

_MARKDOWN_STOCK_REGEX = r'(?P<markdown>[_\\~|\*`]|%s)' % _MARKDOWN_ESCAPE_COMMON


def remove_markdown(text, *, ignore_links=True):
    """A helper function that removes markdown characters.

    .. versionadded:: 1.7
    
    .. note::
            This function is not markdown aware and may remove meaning from the original text. For example,
            if the input contains ``10 * 5`` then it will be converted into ``10  5``.
    
    Parameters
    -----------
    text: :class:`str`
        The text to remove markdown from.
    ignore_links: :class:`bool`
        Whether to leave links alone when removing markdown. For example,
        if a URL in the text contains characters such as ``_`` then it will
        be left alone. Defaults to ``True``.

    Returns
    --------
    :class:`str`
        The text with the markdown special characters removed.
    """

    def replacement(match):
        groupdict = match.groupdict()
        return groupdict.get('url', '')

    regex = _MARKDOWN_STOCK_REGEX
    if ignore_links:
        regex = '(?:%s|%s)' % (_URL_REGEX, regex)
    return re.sub(regex, replacement, text, 0, re.MULTILINE)


def escape_markdown(text, *, as_needed=False, ignore_links=True):
    r"""A helper function that escapes Discord's markdown.

    Parameters
    -----------
    text: :class:`str`
        The text to escape markdown from.
    as_needed: :class:`bool`
        Whether to escape the markdown characters as needed. This
        means that it does not escape extraneous characters if it's
        not necessary, e.g. ``**hello**`` is escaped into ``\*\*hello**``
        instead of ``\*\*hello\*\*``. Note however that this can open
        you up to some clever syntax abuse. Defaults to ``False``.
    ignore_links: :class:`bool`
        Whether to leave links alone when escaping markdown. For example,
        if a URL in the text contains characters such as ``_`` then it will
        be left alone. This option is not supported with ``as_needed``.
        Defaults to ``True``.

    Returns
    --------
    :class:`str`
        The text with the markdown special characters escaped with a slash.
    """

    if not as_needed:
        def replacement(match):
            groupdict = match.groupdict()
            is_url = groupdict.get('url')
            if is_url:
                return is_url
            return '\\' + groupdict['markdown']

        regex = _MARKDOWN_STOCK_REGEX
        if ignore_links:
            regex = '(?:%s|%s)' % (_URL_REGEX, regex)
        return re.sub(regex, replacement, text, 0, re.MULTILINE)
    else:
        text = re.sub(r'\\', r'\\\\', text)
        return _MARKDOWN_ESCAPE_REGEX.sub(r'\\\1', text)


def escape_mentions(text):
    """A helper function that escapes everyone, here, role, and user mentions.

    .. note::

        This does not include channel mentions.

    .. note::

        For more granular control over what mentions should be escaped
        within messages, refer to the :class:`~discord.AllowedMentions`
        class.

    Parameters
    -----------
    text: :class:`str`
        The text to escape mentions from.

    Returns
    --------
    :class:`str`
        The text with the mentions removed.
    """
    return re.sub(r'@(everyone|here|[!&]?[0-9]{17,20})', '@\u200b\\1', text)


# Thanks discord.py for this logger, it's grat, so we take this :)
def stream_supports_colour(stream: Any) -> bool:
    # Pycharm and Vscode support colour in their inbuilt editors
    if 'PYCHARM_HOSTED' in os.environ or os.environ.get('TERM_PROGRAM') == 'vscode':
        return True

    is_a_tty = hasattr(stream, 'isatty') and stream.isatty()
    if sys.platform != 'win32':
        return is_a_tty

    # ANSICON checks for things like ConEmu
    # WT_SESSION checks if this is Windows Terminal
    # Sometimes however WT_SESSION is not present, so we check for the SESSIONNAME
    return is_a_tty and ('ANSICON' in os.environ or 'WT_SESSION' in os.environ or os.environ.get('SESSIONNAME', '') == 'Console')


class _ColourFormatter(logging.Formatter):

    # ANSI codes are a bit weird to decipher if you're unfamiliar with them, so here's a refresher
    # It starts off with a format like \x1b[XXXm where XXX is a semicolon separated list of commands
    # The important ones here relate to colour.
    # 30-37 are black, red, green, yellow, blue, magenta, cyan and white in that order
    # 40-47 are the same except for the background
    # 90-97 are the same but "bright" foreground
    # 100-107 are the same as the bright ones but for the background.
    # 1 means bold, 2 means dim, 0 means reset, and 4 means underline.

    # LEVEL_COLOURS = [
    #     (logging.DEBUG, '\x1b[40;1m'),
    #     (logging.INFO, '\x1b[34;1m'),
    #     (logging.WARNING, '\x1b[33;1m'),
    #     (logging.ERROR, '\x1b[31m'),
    #     (logging.CRITICAL, '\x1b[41m'),
    # ]
    LEVEL_COLOURS = [
        (logging.DEBUG, colorama.Back.BLACK + colorama.Style.BRIGHT),
        (logging.INFO, colorama.Fore.BLUE + colorama.Style.BRIGHT),
        (logging.WARNING, colorama.Fore.YELLOW + colorama.Style.BRIGHT),
        (logging.ERROR, colorama.Fore.RED),
        (logging.CRITICAL, colorama.Back.RED),
    ]

    FORMATS = {
        level: logging.Formatter(
            f'\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s',
            '%Y-%m-%d %H:%M:%S',
        )
        for level, colour in LEVEL_COLOURS
    }

    def __str__(self) -> str:
        return 'ColorFormatter'

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'\x1b[31m{text}\x1b[0m'

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output


def setup_logging(
    *,
    handler: logging.Handler = MISSING,
    formatter: logging.Formatter = MISSING,
    level: int = MISSING,
    root: bool = True,
) -> None:
    """A helper function to set up logging.
    This is superficially similar to :func:`logging.basicConfig` but
    uses different defaults and a colour formatter if the stream can
    display colour.
    This is used by the :class:`~discord.Client` to set up logging
    if ``log_handler`` is not ``None``.

    .. versionadded:: 2.0

    Parameters
    -----------
    handler: :class:`logging.Handler`
        The log handler to use for the library's logger.
        The default log handler if not provided is :class:`logging.StreamHandler`.
    formatter: :class:`logging.Formatter`
        The formatter to use with the given log handler. If not provided then it
        defaults to a colour based logging formatter (if available). If colour
        is not available then a simple logging formatter is provided.
    level: :class:`int`
        The default log level for the library's logger. Defaults to ``logging.INFO``.
    root: :class:`bool`
        Whether to set up the root logger rather than the library logger.
        Unlike the default for :class:`~discord.Client`, this defaults to ``True``.
    """

    if level is MISSING:
        level = logging.INFO

    if handler is MISSING:
        handler = logging.StreamHandler()
        handler_name = 'default stream handler'
    else:
        handler_name = handler.name

    if formatter is MISSING:
        if isinstance(handler, logging.StreamHandler) and stream_supports_colour(handler.stream):
            formatter = _ColourFormatter()
            supports_color = True
        else:
            dt_fmt = '%Y-%m-%d %H:%M:%S'
            formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
            supports_color = False
    else:
        supports_color = stream_supports_colour(handler.stream) if isinstance(handler, logging.StreamHandler) else MISSING

    if root:
        logger = logging.getLogger()
    else:
        library, _, _ = __name__.partition('.')
        logger = logging.getLogger(library)

    handler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(handler)

    if level <= logging.INFO:
        level_name = logging.getLevelName(level)
        if supports_color:
            fmt = f'Started colored logging for \x1b[32m%s\x1b[0m with handler \x1b[32m%s\x1b[0m on level {dict(_ColourFormatter.LEVEL_COLOURS)[level]}%s\x1b[0m.'
        else:
            fmt = 'Started logging for %s with handler %s on level %s.'
        logger.info(
            fmt,
            logger.name,
            handler_name,
            level_name
        )
