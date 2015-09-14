import re

class Message(object):
    def __init__(self, adapter, user, command, argument=None):
        self.user = user
        # TODO: rm the distinction between command and argument?
        self.command = re.compile(command)
        self.argument = argument
        self.adapter = adapter
