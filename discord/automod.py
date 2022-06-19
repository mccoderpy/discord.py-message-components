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

from .abc import Snowflake
from .enums import AutoModEventType, AutoModKeywordPresetType, AutoModActionType, AutoModTriggerType, try_enum


if TYPE_CHECKING:
    # Add imports here, that are only used for annotation and would raise CircularImportError otherwise
    pass


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

        self.keyword_filter: Optional[List[str]] = keyword_filter
        self.presets: Optional[List[AutoModKeywordPresetType]] = presets


class AutoModRule:
    def __init__(self,
                 event_type: AutoModEventType,
                 trigger_type: AutoModTriggerType,
                 actions: List[AutoModAction],
                 trigger_metadata: AutoModTriggerMetadata,
                 enabled: bool,
                 except_roles: List[Snowflake] = [],
                 except_channels: List[Snowflake] = [],
                 ):
        #TODO: Get some sleep now 😅 will continue tomorrow
        pass