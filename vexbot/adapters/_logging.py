import logging

_TOPIC_DELIM="::"

class LoopPubHandler(logging.Handler):
    def __init__(self, messaging, level=logging.NOTSET):
        super().__init__(level)
        self.messaging = messaging

    def emit(self, record):
        info = {'name': record.name,
                'level': record.levelno,
                'pathname': record.pathname,
                'lineno': record.lineno,
                'msg': record.msg,
                'args': [str(x) for x in record.args],
                'exc_info': record.exc_info,
                'func': record.funcName,
                'sinfo': record.stack_info,
                'type': 'log'}

        self.messaging.send_log(**info)


class MessagingLogger:
    def __init__(self, service_name: str):
        name = service_name + '.messaging'
        self.command = logging.getLogger(name + '.command') 
        self.control = logging.getLogger(name + '.control') 
        self.publish = logging.getLogger(name + '.publish') 
        self.subscribe = logging.getLogger(name + '.subscribe') 
        self.request = logging.getLogger(name + '.request')
