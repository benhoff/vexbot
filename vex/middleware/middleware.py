import asyncio

class Middleware(object):
    def __init__(self, bot=None):
        self.stack = []
        self.is_activated = False
        self.bot = bot
    
    @asyncio.coroutine
    def activate(self):
        if self.is_activated:
            return

        for item in self.stack:
            if not item.is_activated:
                asyncio.async(item.activate())
        self.is_activated = True

    def execute(self, response, next=None, done=None):
        for middleware in self.stack:
            next, done = middleware.call(self.bot, response, next, done)

            # see if we are done
            if isinstance(done, bool) and done:
                return

        return done

    @asyncio.coroutine
    def run(self):
        if not self.is_activated:
            yield from self.activate()

        for middleware in self.stack:
            if getattr(middleware, 'run'):
                asyncio.async(middleware.run())

    def register(self, middleware):
        # NOTE: hubot has a check for length here
        self.stack.append(middleware)
