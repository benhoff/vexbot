from vexbot.command import extension
from vexbot.observers import CommandObserver


@extension(CommandObserver)
def do_get_intents(self, *args, **kwargs):
    return self.bot.intents.get_intent_names()


@extension(CommandObserver)
def do_get_intent(self, *args, **kwargs):
    return self.bot.intents.get_intent_names(*args, **kwargs)
