.. currentmodule:: discord.oauth2

OAuth2
=======

.. warning::

    **This feature is new in the library and not fully developed yet.**

    You can test and use it but be aware that this can change the behavior at any time.

    *PS: As always, feel free to contribute to it and help us improve.*

OAuth2 enables application developers to build applications that utilize authentication and data from the Discord API.
Discord supports multiple types of OAuth2 authentication:

    - the authorization code grant
    - the implicit grant
    - client credentials

and some modified special-for-Discord flows for Bots and Webhooks.

.. code-block:: python3

    import discord.oauth2 as oauth2

Manuals
-------

These pages go into great detail about everything the API can do.

.. toctree::
    :maxdepth: 2

    Main Oauth2 API <api.rst>