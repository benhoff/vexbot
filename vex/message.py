import re

class Message(object):
    def __init__(self, command, argument=None):
        self.command = re.compile(command)
        self.argument = argument
