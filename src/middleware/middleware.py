import asyncio

class Middleware(object):
    def __init__(self, bot=None):
        self.stack = []
        self.is_activated = False
        self.bot = bot
    
    def execute(self, response, next=None, done=None):
        for middleware in self.stack:
            next, done = middleware.call(self.bot, response, next, done)

            # see if we are done
            if isinstance(done, bool) and done:
                return

        return done

    def register(self, middleware):
        # NOTE: hubot has a check for length here
        self.stack.append(middleware)
