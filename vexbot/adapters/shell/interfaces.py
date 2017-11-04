from vexbot.adapters.shell.observers import AuthorObserver
from vexbot.adapters.shell.observers import ServiceObserver
from vexbot.util.lru_cache import LRUCache as _LRUCache


def _add_word(completer):
    """
    Used to add words to the completors
    """
    def inner(word: str):
        completer.words.add(word)
    return inner


def _remove_word(completer):
    """
    Used to remove words from the completors
    """
    def inner(word: str):
        try:
            completer.words.remove(word)
        except Exception:
            pass
    return inner


class AuthorInterface:
    def __init__(self, word_completer, messaging):
        self.author_observer = AuthorObserver(self)

        messaging.chatter.subscribe(self.author_observer)
        self.authors = _LRUCache(100, 
                                 _add_word(word_completer),
                                 _remove_word(word_completer))
        self.author_metadata = _LRUCache(100)
        self.metadata_words = ['channel', ]

    def add_author(self, author: str, source: str, **metadata: dict):
        # NOTE: this fixes the parsing for usernames
        author = author.replace(' ', '_')

        self.authors[author] = source
        self.author_metadata[author] = {k: v for k, v in metadata.items()
                                        if k in self.metadata_words} 

    def is_author(self, author: str):
        return author in self.author_observer.authors

    def get_metadata(self, author: str, kwargs: dict) -> dict:
        source = self.author_observer.authors[author]
        metadata = self.author_observer.author_metadata[author]
        # TODO: Determine if this makes the most sense to update in
        metadata.update(kwargs)
        kwargs = metadata
        kwargs['target'] = source
        kwargs['msg_target'] = author
        return kwargs


class ServiceInterface:
    def __init__(self, word_completer, messaging):
        self.service_observer = ServiceObserver(self)
        messaging.chatter.subscribe(self.service_observer)

        self.services = set()
        self.channels = _LRUCache(100, 
                                  _add_word(word_completer),
                                  _remove_word(word_completer))

    def add_service(self, source: str, channel: str=None):
        if source not in self.services:
            # NOTE: small hack to append word to completer
            self.channels.add_callback(source)
            self.services.add(source)

        if channel is not None and channel not in self.channels:
            self.channels[channel] = source

    def is_service(self, service: str):
        in_service = service in self.services
        in_channel = service in self.channels
        return in_service or in_channel

    def get_metadata(self, service: str, kwargs: dict) -> dict:
        if service in self.channels:
            kwargs['channel'] = service
            service = self.channels[service]
        kwargs['target'] = service
        return args, kwargs

    def get_entites(self, text: str) -> tuple:
        pass
