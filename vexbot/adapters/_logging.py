import logging


class MessagingLogger:
    def __init__(self, service_name: str):
        name = service_name + '.messaging'
        self.command = logging.getLogger(name + '.command') 
        self.control = logging.getLogger(name + '.control') 
        self.publish = logging.getLogger(name + '.publish') 
        self.subscribe = logging.getLogger(name + '.subscribe') 
        self.request = logging.getLogger(name + '.request')
