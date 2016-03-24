class Response(object):
    def __init__(self, bot, message, match=None):
        self.bot = bot
        self.message = message
        self.match = match
