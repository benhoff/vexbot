class Adapter(object):
    """ 
    An adapter is a specific interface to a source
    """
    def __init__(self):
        pass

    def send(self):
        """
        Method for sending data back to the chat source. Reimplement this 
        """
        pass

    def reply(self):
        """
        Method for building a reply and sending it back to the chat source. Reimplement
        """
        pass

    def close(self):
        pass

    def receive(self, message):
        """
        dispatch a receieved message to the bot
        """
        pass


    def run(self):
        pass

    # TODO: possible methods: emote


