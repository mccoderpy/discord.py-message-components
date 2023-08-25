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
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Optional,
    List
)
from typing_extensions import Literal

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.appinfo import (
        Team as TeamData,
        TeamMember as TeamMemberData,
    )

from . import utils
from .user import BaseUser
from .asset import Asset
from .enums import TeamMembershipState, TeamRole, try_enum

__all__ = (
    'Team',
    'TeamMember',
)

class Team:
    """Represents an application team for a bot provided by Discord.

    Attributes
    -------------
    id: :class:`int`
        The team ID.
    name: :class:`str`
        The team name
    icon: Optional[:class:`str`]
        The icon hash, if it exists.
    owner_id: :class:`int`
        The team's owner ID.
    members: List[:class:`TeamMember`]
        A list of the members in the team

        .. versionadded:: 1.3
    """
    __slots__ = ('_state', 'id', 'name', 'icon', 'owner_id', 'members')

    def __init__(self, state: ConnectionState, data: TeamData) -> None:
        self._state: ConnectionState = state
        self.id: int = utils._get_as_snowflake(data, 'id')
        self.name: str = data['name']
        self.icon: str = data['icon']
        self.owner_id: int = utils._get_as_snowflake(data, 'owner_user_id')
        self.members: List[TeamMember] = [TeamMember(self, self._state, member) for member in data['members']]

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'

    @property
    def icon_url(self) -> Asset:
        """:class:`.Asset`: Retrieves the team's icon asset.

        This is equivalent to calling :meth:`icon_url_as` with
        the default parameters ('webp' format and a size of 1024).
        """
        return self.icon_url_as()

    def icon_url_as(self, *, format: Literal['webp', 'jpeg', 'jpg', 'png'] = 'webp', size: int = 1024) -> Asset:
        """Returns an :class:`Asset` for the icon the team has.

        The format must be one of 'webp', 'jpeg', 'jpg' or 'png'.
        The size must be a power of 2 between 16 and 4096.

        .. versionadded:: 2.0

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the icon to. Defaults to 'webp'.
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
        return Asset._from_icon(self._state, self, 'team', format=format, size=size)

    @property
    def owner(self) -> Optional[TeamMember]:
        """Optional[:class:`TeamMember`]: The team's owner."""
        return utils.get(self.members, id=self.owner_id)


class TeamMember(BaseUser):
    """Represents a team member in a team.

    .. versionchanged:: 2.0
        The :attr:`name` attribute was renamed to :attr:`username` due to the (upcoming)
        :dis-gd:`username changes <username>`.

    .. container:: operations

        .. describe:: x == y

            Checks if two team members are equal.

        .. describe:: x != y

            Checks if two team members are not equal.

        .. describe:: hash(x)

            Return the team member's hash.

        .. describe:: str(x)

            Returns the team member's :attr:`username` if :attr:`is_migrated` is true, else the user's name with discriminator.

            .. note::

                When the migration is complete, this will always return the :attr:`username`.

    .. versionadded:: 1.3

    Attributes
    -------------
    username: :class:`str`
        The team member's username.
    global_name: Optional[:class:`str`]
        The team members :attr:`~User.global_name` if any.
    id: :class:`int`
        The team member's unique ID.
    discriminator: :class:`str`
        The team member's discriminator.

        .. important::
            This will be removed in a future API version.
            Read more about it :dis-gd:`here <usernames>`.
    avatar: Optional[:class:`str`]
        The avatar hash the team member has. Could be None.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    team: :class:`Team`
        The team that the member is from.
    membership_state: :class:`TeamMembershipState`
        The membership state of the member (e.g. invited or accepted)
    role: :class:`TeamRole`
        The role of the team member.

        .. versionadded:: 2.0
    """
    __slots__ = BaseUser.__slots__ + ('team', 'membership_state', 'permissions', 'role')

    def __init__(self, team: Team, state: ConnectionState, data: TeamMemberData):
        self.team: Team = team
        self.membership_state: TeamMembershipState = try_enum(TeamMembershipState, data['membership_state'])
        self.permissions: List[str] = data['permissions']
        self.role: TeamRole = try_enum(TeamRole, data['role'])
        super().__init__(state=state, data=data['user'])

    def __repr__(self) -> str:
        if not self.is_migrated:
            return (
                f'<{self.__class__.__name__} role={self.role!r} id={self.id} username={self.username!r} '
                f'global_name={self.global_name} membership_state={self.membership_state!r}>'
            )
        return (
            f'<{self.__class__.__name__} role={self.role!r} id={self.id} username={self.username!r} '
            f'discriminator={self.discriminator!r} global_name={self.global_name} '
            f'membership_state={self.membership_state!r}>'
        )

