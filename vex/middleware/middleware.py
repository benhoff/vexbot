class Middleware(object):
    def __init__(self, bot=None):
        self.stack = []

    def execute(self, response, next=None):
        for middleware in self.stack:
            response, continue_processing yield from middleware.call(response)
            if not continue_processing:
                break
        if next is not None:
            next(response)

    def register(self, middleware):
        # NOTE: hubot has a check for length here
        self.stack.append(middleware)
