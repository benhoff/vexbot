import abc
from abc import abstractmethod
import pluginmanager

class Adapter(pluginmanager.IPlugin, metaclass=abc.ABCMeta):
    """
    An adapter is a specific interface to a source
    """
    def __init__(self):
        pass

    @abstractmethod
    def send(self):
        """
        Method for sending data back to the chat source. Reimplement this
        """
        pass

    @abstractmethod
    def reply(self):
        """
        Method for building a reply and sending it back to the chat source. Reimplement
        """
        pass

    def close(self):
        pass

    @abstractmethod
    def receive(self, message):
        """
        dispatch a receieved message to the bot
        """
        pass


    @abstractmethod
    def run(self):
        pass

    # TODO: possible methods: emote
