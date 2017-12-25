import re
from six import string_types
from prompt_toolkit.completion import Completer, Completion


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


class WordCompleter(Completer):
    """
    Simple autocompletion on a list of words.
    :param words: List of words.
    :param ignore_case: If True, case-insensitive completion.
    :param meta_dict: Optional dict mapping words to their meta-information.
    :param WORD: When True, use WORD characters.
    :param sentence: When True, don't complete by comparing the word before the
        cursor, but by comparing all the text before the cursor. In this case,
        the list of words is just a list of strings, where each string can
        contain spaces. (Can not be used together with the WORD option.)
    :param match_middle: When True, match not only the start, but also in the
                         middle of the word.
    """
    def __init__(self, words, ignore_case=False, meta_dict=None, WORD=False,
                 sentence=False, match_middle=False):
        assert not (WORD and sentence)

        self.words = set(words)
        self.ignore_case = ignore_case
        self.meta_dict = meta_dict or {}
        self.WORD = WORD
        self.sentence = sentence
        self.match_middle = match_middle
        assert all(isinstance(w, string_types) for w in self.words)

    def get_completions(self, document, complete_event):
        # Get word/text before cursor.
        if self.sentence:
            word_before_cursor = document.text_before_cursor
        else:
            word_before_cursor = document.get_word_before_cursor(WORD=self.WORD)

        if self.ignore_case:
            word_before_cursor = word_before_cursor.lower()

        def word_matches(word):
            """ True when the word before the cursor matches. """
            if self.ignore_case:
                word = word.lower()

            if self.match_middle:
                return word_before_cursor in word
            else:
                return word.startswith(word_before_cursor)

        for a in self.words:
            if word_matches(a):
                display_meta = self.meta_dict.get(a, '')
                yield Completion(a, -len(word_before_cursor), display_meta=display_meta)
