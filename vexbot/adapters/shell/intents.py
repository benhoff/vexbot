import inspect as _inspect

class CommandItents:
    def get_intents(self) -> dict:
        result = {}
        for name, method in _inspect.getmembers(self):
            if name.startswith('do_'):
                result[name[3:]] = method
            elif method._vex_intent:
                result[method._vex_intent_name] = method

        return result

    def do_stop_chatter(self):
        pass

    def do_start_chatter(self):
        pass

    def do_change_color(self):
        pass
