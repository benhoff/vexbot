import irc3


@irc3.plugin
class EchoToMessage:
    requires = ['irc3.plugins.core',
                'irc3.plugins.command']

    def __init__(self, bot):
        self.bot = bot

    @irc3.event(irc3.rfc.PRIVMSG)
    def message(self, mask, event, target, data):
        nick = mask.nick
        nick = str(nick)
        message = str(data)
        target = str(target)
        self.bot.messaging.send_chatter(author=nick,
                                        message=message,
                                        channel=target)
