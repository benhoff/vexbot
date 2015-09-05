import re

class Message(object):
    def __init__(self, adapter, user, command, argument=None):
        self.user = user
        self.command = re.compile(command)
        self.argument = argument
        self.adapter = adapter
