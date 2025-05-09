from __future__ import annotations

from pydub import AudioSegment
from typing import Optional, Union
import io
import os
import base64
import mimetypes
from pathlib import Path
import random

from .mixins import Hashable
from .abc import Snowflake
from .utils import get as utils_get, snowflake_time

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from .state import ConnectionState
    from .guild import Guild

__all__ = (
    'SoundboardSound',
)

class SoundboardSound(Hashable):
    """Represents a Soundboard Sound.

        .. versionadded:: 1.7.5.4

        .. container:: operations

            .. describe:: str(x)

                Returns the name of the SoundboardSounds.

            .. describe:: x == y

                Checks if the Soundboard Sound is equal to another Soundboard Sound.

            .. describe:: hash(x)

                 Enables use in sets or as a dictionary key.

        Attributes
        ----------
        name: :class:`str`
            The sound's name.
        sound_id: :class:`int`
            The id of the sound.
        volume: :class:`float`
            The volume of the sound.
        emoji_id: :class:`int`
            The id for the sound's emoji.
        emoji_name: :class:`str`
            The name for the sound's emoji.
        guild_id: :class:`int`
            The id of the guild which this sound's belongs to.
        available: :class:`bool`
            Whether this guild sound can be used
        user: :class:`User`
            The user that uploaded the guild sound
        """

    __slots__ = ('sound_id', 'name', 'volume', 'emoji_id', 'emoji_name', 'guild', 'guild_id', 'available', 'user', '_state')

    if TYPE_CHECKING:
        name: str
        sound_id: SnowflakeID
        volume: float
        emoji_id: NotRequired[Optional[SnowflakeID]]
        emoji_name: NotRequired[Optional[str]]
        guild_id: NotRequired[int]
        available: bool
        user: NotRequired[User]

    def __init__(self, *, guild: Guild, state: ConnectionState, data):
        self.guild = guild
        self._state = state
        self._from_data(data)
        # TODO: add Cache

    def __repr__(self):
        return f"<SoundboardSound name={self.name!r} sound_id={self.sound_id}, "\
               f"volume={self.volume} emoji_id={self.emoji_id} emoji_name={self.emoji_name!r}, "\
               f"guild={self.guild}, available={self.available}, user={self.user}>"

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, SoundboardSound) and self.id == other.id

    def __hash__(self):
        return hash((self.name, self.sound_id))

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the sound's creation time in UTC as a naive datetime."""
        return snowflake_time(self.sound_id)

    @staticmethod
    def _auto_trim(input_path: Union[str, bytes, io.IOBase, Path], max_duration_sec: float = 5, max_size_bytes: int = 512 * 1024) -> bytes:
        if isinstance(input_path, str):
            if input_path.startswith("data:"):
                try:
                    b64_data = input_path.split(",", 1)[1]
                    input_path = base64.b64decode(b64_data)
                except Exception as e:
                    raise ValueError(f"Invalid base64 data URI: {e}")
            elif os.path.exists(input_path):
                input_path = Path(input_path)
            else:
                try:
                    input_path = base64.b64decode(input_path)
                except Exception:
                    raise ValueError("Invalid base64 string or path")

        if isinstance(input_path, Path):
            audio = AudioSegment.from_file(str(input_path))
        elif isinstance(input_path, bytes):
            audio = AudioSegment.from_file(io.BytesIO(input_path))
        elif isinstance(input_path, io.IOBase):
            input_path.seek(0)
            audio = AudioSegment.from_file(input_path)
        else:
            raise TypeError("Unsupported input type")

        duration_ms = len(audio)
        max_duration_ms = int(max_duration_sec * 1000)

        if duration_ms > max_duration_ms:
            start = random.randint(0, duration_ms - max_duration_ms)
            audio = audio[start:start + max_duration_ms]
        else:
            audio = audio[:max_duration_ms]

        buffer = io.BytesIO()
        audio.export(buffer, format="mp3", parameters=["-t", "5", "-write_xing", "0"])
        return buffer.getvalue()

    @staticmethod
    def _encode_sound(sound: Union[str, bytes, io.IOBase, Path]) -> str:
        raw: bytes
        mime_type: str = "audio/ogg"
        sound_duration: float

        if isinstance(sound, bytes):
            raw = sound

        elif isinstance(sound, io.IOBase):
            raw = sound.read()

        elif isinstance(sound, Path):
            file_size = os.path.getsize(sound)
            if file_size > 512 * 1024:
                raise ValueError("The audio file exceeds the maximum file size of 512 KB")

            with open(sound, 'rb') as f:
                raw = f.read()

            try:
                audio = AudioSegment.from_file(sound)
                sound_duration = audio.duration_seconds
            except Exception as e:
                raise ValueError(f"Error loading the audio file: {e}")

            if sound_duration > 5.2:
                raise ValueError("The audio file exceeds the maximum duration of 5.2 seconds")

            mime_type, _ = mimetypes.guess_type(sound)
            if mime_type is None:
                mime_type = "audio/ogg"
            elif sound.suffix == ".mp3":
                mime_type = "audio/mpeg"

        elif isinstance(sound, str):
            if sound.startswith("data:"):
                return sound
            try:
                base64.b64decode(sound, validate=True)
                return f"data:audio/ogg;base64,{sound}"
            except Exception:
                raise ValueError("Invalid Base64-String")

        else:
            raise ValueError("Invalid sound type")

        encoded = base64.b64encode(raw).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    def _from_data(self, data):
        self.name = data['name']
        self.sound_id = int(data['sound_id'])
        self.volume = float(data['volume'])

        self.emoji_id = int(data['emoji_id']) if data.get('emoji_id') else None
        self.emoji_name = data.get('emoji_name')

        self.guild_id = self.guild.id

        self.available = data.get('available', True)

        user = data.get('user')
        if user:
            self.user = self._state.get_user(int(user['id']))
        else:
            self.user = None

    @classmethod
    def _from_list(cls, guild, state, data_list):
        return [cls(guild=guild, state=state, data=data) for data in data_list]

