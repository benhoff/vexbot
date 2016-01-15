import re

class Message(object):
    def __init__(self, adapter, user, command):
        self.adapter = adapter
        self.user = user
        # TODO: rm the distinction between command and argument?
        self.command = re.compile(command)
