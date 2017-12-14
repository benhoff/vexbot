def do_get_intents(self, *args, **kwargs):
    return self.bot.intents.get_intent_names()


def do_get_intent(self, *args, **kwargs):
    return self.bot.intents.get_intent_names(*args, **kwargs)
