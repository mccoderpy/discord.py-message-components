Es ist folgender Fehler beim Versuch den Cog decorator_test_cog neu zuladen aufgetreten:

Traceback (most recent call last):
  File "C:\Users\McCub\Desktop\discord.py-message-components\cogs\developer-commands_cog.py", line 135, in reload
    self.bot.reload_extension(f'cogs.{cog}')
  File "C:\Users\McCub\Desktop\discord.py-message-components\discord\ext\commands\bot.py", line 947, in reload_extension
    self._remove_module_references(lib.__name__)
  File "C:\Users\McCub\Desktop\discord.py-message-components\discord\ext\commands\bot.py", line 755, in _remove_module_references
    if event.__module__ is not None and _is_submodule(name, event.__module__):
AttributeError: 'tuple' object has no attribute '__module__'
