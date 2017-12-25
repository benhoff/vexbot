# NOTE: Unimplemented


def pass():
    levels = ('debug', 'info', 'warning', 'warn', 'error', 'critical',
              'DEBUG', 'INFO', 'WARNING', 'WARN', 'ERROR', 'CRITICAL')
    examples = ('set logging to {}',
                'set log to {}',
                'logging to {}')

class BotIntents:
    def __init__(self):
        self._intents = self.get_intents()

    def get_intents(self) -> dict:
        result = {}
        for name, method in _inspect.getmembers(self):
            isintent = getattr(method, '_vex_intent', False)

            if name.startswith('do_') or isintent:
                if isintent:
                    name = method._vex_intent_name
                else:
                    name = name[3:]

                result[name] = method

        return result

    def get_intent_names(self, *args, **kwargs) -> tuple:
        if not args:
            return tuple(self._intents.keys())
        results = {}
        for arg in args:
            # FIXME: I hate this API
            intent_values = self._intents.get(arg)
            if intent_values is not None:
                intent_values = intent_values()
            if intent_values is None:
                intent_values = ()
            results[arg] = intent_values
        return results

    def do_set_log(self) -> tuple:
        levels = ('debug', 'info', 'warning', 'warn', 'error', 'critical',
                  'DEBUG', 'INFO', 'WARNING', 'WARN', 'ERROR', 'CRITICAL')
        examples = ('set logging to {}',
                    'set log to {}',
                    'logging to {}')

        # FIXME: finish
        values = ()
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


    def do_trace(self) -> tuple:
        values = ('run that back for me',
                  'trace last command',
                  'trace command',
                  'trace')

        return values

    def do_lint(self) -> tuple:
        values = ('lint file',
                  'flake file')

        return values


