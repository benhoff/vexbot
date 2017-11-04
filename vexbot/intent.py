import inspect as _inspect
import functools as _functools


class Entity:
    def __init__(self, text: str, start: int, end: int, name: str, type_: str, value: str=None):
        """
        Args:
            text: Example utterance
            start: Starting position of the value
            end: Ending position of the value
            name: Name of the entity
            type_: Entity Type
        """
        self.text = text
        self.start = start
        self.end = end
        self.name = name
        self.type = type_
        if value is None:
            value = name
        self.value = value

class FindEntity(text, value, name):
    pass


# http://rasa-nlu.readthedocs.io/en/latest/tutorial.html#preparing-the-training-data
def action(function=None,
           intent: str=None,
           name: str=None,
           examples: list,
           **defaults):

    if function is None:
        return _functools.partial(action,
                                  intent=intent,
                                  name=name,
                                  examples=examples,
                                  defaults=defaults)

    # https://stackoverflow.com/questions/10176226/how-to-pass-extra-arguments-to-python-decorator
    @_functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    # TODO: Do things here to the wrapper
    # TODO: Get entities from the examples



def intent(function=None,
           name: str=None):

    if function is None:
        return _functools.partial(intent,
                                  name=name)

    # https://stackoverflow.com/questions/10176226/how-to-pass-extra-arguments-to-python-decorator
    @_functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    wrapper._vex_intent = True
    wrapper._vex_intent_name = name


class BotIntents:
    def get_intents(self) -> dict:
        result = {}
        for name, method in _inspect.getmembers(self):
            if name.startswith('do_'):
                result[name[3:]] = method
            elif method._vex_intent:
                result[method._vex_intent_name] = method

        return result

    def do_get_log(self) -> tuple:
        values = ('get log',
                  'get logging',
                  'get logging value',
                  'get logs',
                  'what is the logging',
                  'what is the logging?',
                  'show me the log',
                  'show me the logging',
                  'what is the logging value?')

        return values

    def do_set_log(self) -> tuple:
        levels = ('debug', 'info', 'warning', 'warn', 'error', 'critical',
                  'DEBUG', 'INFO', 'WARNING', 'WARN', 'ERROR', 'CRITICAL')
        examples = ('set logging to {}',
                    'set log to {}',
                    'logging to {}')

        # FIXME: finish
        values = ()
        return values

    def do_get_services(self) -> tuple:
        values = ('what services are up'
                  'services up'
                  'services available'
                  'what is running'
                  'running')

        return values

    def do_get_help(self) -> tuple:
        values = ('help me please',
                  'what does this do',
                  'what can I do',
                  'what can you do')

        return values

    def do_get_code(self) -> tuple:
        values = ('get code for that commands',
                  'get code for last',
                  'get code for {}',
                  'get source for {}',
                  'show me the code',
                  'show code',
                  'display code')

    def do_get_commands(self) -> tuple:
        pass

    def do_restart_program(self) -> tuple:
        pass

    def do_start_program(self) -> tuple:
        pass

    def do_stop(self) -> tuple:
        pass

    def do_status(self) -> tuple:
        pass

    def do_error(self) - > tuple:
        values = ('show me the error',
                  'what\'s wrong with you',
                  'tell me how you\'re broken',
                  'what\'s wrong',
                  'what happened')

        return values

    def do_trace(self) -> tuple:
        values = ('run that back for me',
                  'trace last command',
                  'trace command',
                  'trace')

        return values

    def do_lint(self): -> tuple:
        values ('lint file',
                'flake file')

        return values
