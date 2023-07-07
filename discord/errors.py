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
import traceback

__all__ = (
    'AlreadyResponded',
    'DiscordException',
    'DiscordWarning',
    'ClientException',
    'NoMoreItems',
    'GatewayNotFound',
    'HTTPException',
    'InvalidArgument',
    'LoginFailure',
    'ConnectionClosed',
    'PrivilegedIntentsRequired',
    'InvalidData',
    'Unauthorized',
    'Forbidden',
    'NotFound',
    'DiscordServerError',
    'URLAndCustomIDNotAlowed',
    'UnknownInteraction',
    'EmptyActionRow',
    'NotInVoiceChannel',
    'RecordingException',
    'ThreadIsArchived',
    'MissingPermissionsToCreateThread'
)


class DiscordException(Exception):
    """Base exception class for discord.py

    Ideally speaking, this could be caught to handle any exceptions thrown from this library.
    """
    pass


class DiscordWarning(Warning):
    """Base warning class for discord.py

    Ideally speaking, this could be caught to handle any warnings thrown from this library.

    .. note::
        This inherits from :class:`Warning` instead of :class:`Exception`.
    """
    pass


class ClientException(DiscordException):
    """Exception that's thrown when an operation in the :class:`Client` fails.

    These are usually for exceptions that happened due to user input.
    """
    pass


class NoMoreItems(DiscordException):
    """Exception that is thrown when an async iteration operation has no more
    items."""
    pass


class GatewayNotFound(DiscordException):
    """An exception that is usually thrown when the gateway hub
    for the :class:`Client` websocket is not found."""
    def __init__(self):
        message = 'The gateway to connect to discord was not found.'
        super(GatewayNotFound, self).__init__(message)


def flatten_error_dict(d, key=''):
    items = []
    for k, v in d.items():
        new_key = key + '.' + k if key else k

        if isinstance(v, dict):
            try:
                _errors = v['_errors']
            except KeyError:
                items.extend(flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, ' '.join(x.get('message', '') for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)


class HTTPException(DiscordException):
    """Exception that's thrown when an HTTP request operation fails.

    Attributes
    ------------
    response: :class:`aiohttp.ClientResponse`
        The response of the failed HTTP request. This is an
        instance of :class:`aiohttp.ClientResponse`. In some cases
        this could also be a :class:`requests.Response`.

    text: :class:`str`
        The text of the error. Could be an empty string.
    status: :class:`int`
        The status code of the HTTP request.
    code: :class:`int`
        The Discord specific error code for the failure.
    """

    def __init__(self, response, message):
        self.response = response
        self.status = response.status
        if isinstance(message, dict):
            self.code = message.get('code', 0)
            base = message.get('message', '')
            errors = message.get('errors')
            if errors:
                errors = flatten_error_dict(errors)
                helpful = '\n'.join('In %s: %s' % t for t in errors.items())
                self.text = base + '\n' + helpful
            else:
                self.text = base
        else:
            self.text = message
            self.code = 0

        fmt = '{0.status} {0.reason} (error code: {1})'
        if len(self.text):
            fmt += ': {2}'

        super().__init__(fmt.format(self.response, self.code, self.text))


class Unauthorized(HTTPException):
    """Exception that's thrown for when status code 401 occurs.
    
    Subclass of :exc:`HTTPException`
    
    .. versionadded:: 2.0
    """
    pass


class Forbidden(HTTPException):
    """Exception that's thrown for when status code 403 occurs.

    Subclass of :exc:`HTTPException`
    """
    pass


class NotFound(HTTPException):
    """Exception that's thrown for when status code 404 occurs.

    Subclass of :exc:`HTTPException`
    """
    pass


class DiscordServerError(HTTPException):
    """Exception that's thrown for when a 500 range status code occurs.

    Subclass of :exc:`HTTPException`.

    .. versionadded:: 1.5
    """
    pass


class InvalidData(ClientException):
    """Exception that's raised when the library encounters unknown
    or invalid data from Discord.
    """
    pass


class InvalidArgument(ClientException):
    """Exception that's thrown when an argument to a function
    is invalid some way (e.g. wrong value or wrong type).

    This could be considered the analogous of ``ValueError`` and
    ``TypeError`` except inherited from :exc:`ClientException` and thus
    :exc:`DiscordException`.
    """
    pass


class LoginFailure(ClientException):
    """Exception that's thrown when the :meth:`Client.login` function
    fails to log you in from improper credentials or some other misc.
    failure.
    """
    pass


class ConnectionClosed(ClientException):
    """Exception that's thrown when the gateway connection is
    closed for reasons that could not be handled internally.

    Attributes
    -----------
    code: :class:`int`
        The close code of the websocket.
    reason: :class:`str`
        The reason provided for the closure.
    shard_id: Optional[:class:`int`]
        The shard ID that got closed if applicable.
    """
    def __init__(self, socket, *, shard_id, code=None):
        # This exception is just the same exception except
        # reconfigured to subclass ClientException for users
        self.code = code or socket.close_code
        # aiohttp doesn't seem to consistently provide close reason
        self.reason = ''
        self.shard_id = shard_id
        super().__init__('Shard ID %s WebSocket closed with %s' % (self.shard_id, self.code))


class PrivilegedIntentsRequired(ClientException):
    """Exception that's thrown when the gateway is requesting privileged intents,
    but they're not ticked in the developer page yet.

    Go to https://discord.com/developers/applications/ and enable the intents
    that are required. Currently, these are as follows:

    - :attr:`Intents.members`
    - :attr:`Intents.presences`
    - :attr:`Intents.message_content`

    Attributes
    -----------
    shard_id: Optional[:class:`int`]
        The shard ID that got closed if applicable.
    """

    def __init__(self, shard_id):
        self.shard_id = shard_id
        msg = f'\n{f"Shard ID {shard_id}" if shard_id else "Default shard"} is requesting privileged intents ' \
              f'that have not been explicitly enabled in the developer portal.' \
              f'\n⚠ It is recommended to go to https://discord.com/developers/applications/ and explicitly enable ' \
              f'the privileged intents within your application\'s page. ⚠\n' \
              f'If this is not possible, then consider disabling the privileged intents in the code instead.\n\n'
        super().__init__(msg)

    def __str__(self):
        return '\n'.join(self.args)


class RecordingException(ClientException):
    """Exception that's thrown when there is an error while trying to record
    audio from a voice channel.
    """
    pass


class NotInVoiceChannel(ClientException):
    """
    Exception that's thrown when trying to connect of a :class:`~discord.VoiceState`
    using `await user.voice()` from a user that is not connected to a channel the bot has access to
    """
    def __init__(self):
        super().__init__(
            'Can\'t connect to channel because the user is not in one or the bot has no access to the channel.'
        )


class URLAndCustomIDNotAlowed(DiscordException):
    """Exception that's thrown when there is an ``url`` and an ``custom_id`` passed in a :class:`discord.Button`,
    what is not supportet by the Discord-API.

    .. note ::
         :class:`discord.Button` with the style :class:`discord.ButtonStyle.url` don't send any Interaction to Discord when they are clicked.
    """
    def __init__(self, custom_id):
        msg = f"custom_id's (%s) are not allowed in :class:`discord.Button` with the style :class:`discord.ButtonStyle.url` because Discord don't send any Interaction when clicking on a Link-Button." \
              f"For More Information visit the `Discord-API Documentation <https://discord.com/developers/docs/interactions/message-components#buttons>`_."
        super().__init__(msg % custom_id)


class EmptyActionRow(DiscordException):
    """
    Exception that's thrown when there is an empty :class:`~discord.ActionRow` in your message.
    """
    def __init__(self):
        msg = 'The Discord-API does not allow you to send an empty ActionRow, you have to parse at least one component'
        super().__init__(msg)


class UnknownInteraction(DiscordWarning):
    """
    A warning that comes when you try to interact with an expired interaction.
    """
    def __init__(self, interaction_id):
        msg = f'You have already respond to this interaction ({interaction_id}) ' \
              f'and/or 15 minutes have passed since the interaction, which is why Discord has deleted the interaction.'
        super().__init__(msg)


class AlreadyResponded(DiscordException):
    """
    Exception thrown when attempting to send the callback for an interaction that has already been responded to.'
    """
    def __init__(self, interaction_id):
        msg = f'You have already send a callback(using defer, respond or respond_with_modal) to this interaction ({interaction_id}) '
        super().__init__(msg)


class ThreadIsArchived(DiscordException):
    """
    Exception that's thrown when trying to use a method on a ThreadChannel that is archived and need's to be unarchived  first.
    """
    def __init__(self, method):
        msg = f'You can\'t use %s when the Thread is archived. Un-archive it first.'
        super().__init__(msg % method)


class MissingPermissionsToCreateThread(DiscordException):
    """
    Exception that's thrown when trying to create a thread of a type you don't have the permission for to create.
    """
    def __init__(self, *permissions, type):
        msg = f'You\'r missing (any of) %s permission(s) to create a thread of type %s.'
        super().__init__(msg % (', '.join([str(p) for p in permissions]), type))
