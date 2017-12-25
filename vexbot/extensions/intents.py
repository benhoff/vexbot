def get_intents(self, *args, **kwargs):
    return self.bot.intents.get_intent_names()


def get_intent(self, *args, **kwargs):
    return self.bot.intents.get_intent_names(*args, **kwargs)
