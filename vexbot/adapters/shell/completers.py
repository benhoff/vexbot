import re
from prompt_toolkit.completion import Completer


_WORD = re.compile(r'([!#a-zA-Z0-9_]+|[^!#a-zA-Z0-9_\s]+)')


def _get_previous_word(document):
    # reverse the text before the curosr, in order to do an efficient
    # backwards search
    text_before_cursor = document.text_before_cursor[::-1]
    iterator = _WORD.finditer(text_before_cursor)
    count = 1
    try:
        for i, match in enumerate(iterator):
            if i == 0 and match.start(1) == 0:
                count += 1
            if i + 1 == count:
                return (-match.end(1), -match.start(1))
    except StopIteration:
        pass
    return None, None


class ServiceCompleter(Completer):
    def __init__(self, command_completer: Completer):
        self._command_completer = command_completer
        self.service_command_map = {}

    def _handle_services(self, previous_word: str, document, complete_event):
        if previous_word in self.service_command_map:
            return self.service_command_map[previous_word].get_completions(document, complete_event)
        else:
            return self._command_completer.get_completions(document, complete_event)

    def get_completions(self, document, complete_event):
        start, end = _get_previous_word(document)
        if start is None:
            return self._command_completer.get_completions(document, complete_event)

        offset = document.cursor_position
        start += offset
        end += offset
        previous_word = document.text[start:end]

        if previous_word in self.service_command_map:
            return self._handle_services(previous_word, document, complete_event)
        else:
            return self._command_completer.get_completions(document, complete_event)

    def set_service_completer(self, service: str, completer: Completer):
        self.service_command_map[service] = completer
