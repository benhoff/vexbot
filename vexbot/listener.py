from pluginmanager import IPlugin


class Listener(IPlugin):
    def __init__(self, robot, matcher, callback=None):
        """
        Listeners receive every messsage from the chat source and 
        decide if they want to act on it

        An identifier should be provided in the options parameter 
        to uniquely identify the listener (options.id)

        robot    - A Robot instance
        matcher  - A function that determines if this listener 
        should trigger the callback

        options  - an object of additional parameters keyed on 
        extension name (optional)

        callback - a function that is triggered if the message matches
        """
        super().__init__()
        self.bot = robot
        self.matcher = matcher
        self.callback = callback

    def call(self, message):
        result = self.matcher(message)
        if result and self.callback is not None:
            self.callback()
