import logging
from tblib import Traceback


class LoopPubHandler(logging.Handler):
    def __init__(self, messaging, level=logging.NOTSET):
        super().__init__(level)
        self.messaging = messaging

    def emit(self, record):
        args = record.args
        if isinstance(args, tuple):
            args = [str(x) for x in record.args]
        elif isinstance(args, dict):
            args = str(args)
        # NOTE: Might need more specific handling in the future
        else:
            args = str(args)

        info = {'name': record.name,
                'level': record.levelno,
                'pathname': record.pathname,
                'lineno': record.lineno,
                'msg': record.msg,
                'args': args,
                'exc_info': record.exc_info,
                'func': record.funcName,
                'sinfo': record.stack_info,
                'type': 'log'}
        exc_info = info['exc_info']

        if exc_info is not None:
            # FIXME: It's hard to transmit an exception because the Error type 
            # might be defined in a library that is not installed on the
            # receiving side. Not sure what the best way to do this is.
            info['exc_info'] = Traceback(exc_info[2]).to_dict()
            """
            new_exc_info = []
            first = exc_info[0]
            if isinstance(first, Exception):
                try:
                    first = first.__name__
                except AttributeError:
                    first = first.__class__.__name__
            print(first, dir(first), isinstance(first, Exception))
            new_exc_info.append(first)
            new_exc_info.append([str(x) for x in exc_info[1].args])
            new_exc_info.append(Traceback(exc_info[2]).to_dict())
            info['exc_info'] = new_exc_info
            """


        self.messaging.send_log(**info)


class MessagingLogger:
    def __init__(self, service_name: str):
        name = service_name + '.messaging'
        self.command = logging.getLogger(name + '.command') 
        self.control = logging.getLogger(name + '.control') 
        self.publish = logging.getLogger(name + '.publish') 
        self.subscribe = logging.getLogger(name + '.subscribe') 
        self.request = logging.getLogger(name + '.request')
