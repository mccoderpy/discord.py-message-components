:og:title: discord4py OAuth2 documentation
:og:description: Use discord4pys build-in oauth2 package to interact with discords OAuth2 API

.. currentmodule:: discord.oauth2

OAuth2
=======

.. warning::

    **This feature is new in the library and may miss some parts.**

    If you find anything that looks wrong whether it is a bug/missing feature or something in the documentation, please fill out a |bugreport|

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
    :maxdepth: 1

    Main Oauth2 API <api.rst>