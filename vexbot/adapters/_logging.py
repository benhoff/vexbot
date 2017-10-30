import logging


class LoopPubHandler(logging.Handler):
    root_topic=""
    
    formatters = {
        logging.DEBUG: logging.Formatter(
        "%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"),
        logging.INFO: logging.Formatter("%(message)s\n"),
        logging.WARN: logging.Formatter(
        "%(levelname)s %(filename)s:%(lineno)d - %(message)s\n"),
        logging.ERROR: logging.Formatter(
        "%(levelname)s %(filename)s:%(lineno)d - %(message)s - %(exc_info)s\n"),
        logging.CRITICAL: logging.Formatter(
        "%(levelname)s %(filename)s:%(lineno)d - %(message)s\n")}
    
    def __init__(self, messaging, level=logging.NOTSET):
        super().__init__(level)
        self.messaging = messaging

    def format(self,record):
        """Format a record."""
        return self.formatters[record.levelno].format(record)

    def emit(self, record):
        """Emit a log message on my socket."""
        try:
            topic, record.msg = record.msg.split(TOPIC_DELIM,1)
        except Exception:
            topic = ""
        try:
            msg = self.format(record)
        except Exception:
            self.handleError(record)
            return
        
        topic_list = []

        if self.root_topic:
            topic_list.append(self.root_topic)

        topic_list.append(record.levelname)

        if topic:
            topic_list.append(topic)

        topic = '.'.join(t for t in topic_list)
        self.messaging.send_log(topic, msg)



class MessagingLogger:
    def __init__(self, service_name: str):
        name = service_name + '.messaging'
        self.command = logging.getLogger(name + '.command') 
        self.control = logging.getLogger(name + '.control') 
        self.publish = logging.getLogger(name + '.publish') 
        self.subscribe = logging.getLogger(name + '.subscribe') 
        self.request = logging.getLogger(name + '.request')
