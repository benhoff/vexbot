import logging
import irc3


@irc3.plugin
class EchoToMessage:
    requires = ['irc3.plugins.core',
                'irc3.plugins.command']

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @irc3.event(irc3.rfc.PRIVMSG)
    def message(self, mask, event, target, data):
        nick = mask.nick
        nick = str(nick)
        message = str(data)
        target = str(target)
        self.logger.info(' message %s %s %s', nick, message, target)
        self.bot.messaging.send_chatter(author=nick,
                                        message=message,
                                        channel=target)
