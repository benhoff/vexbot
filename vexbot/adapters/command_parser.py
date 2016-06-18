from vexmessage import create_vex_message


class CommandParser:
    def __init__(self):
        self._commands = {}

    def register_command(self, cmd, function):
        self._commands[cmd] = function

    def is_command(self, cmd, call_command=False):
        callback = self._commands.get(cmd, None)

        if callback and call_command:
            callback_result = callback()
            if callback_result:
                self.send_message(callback_result)

            return True
        elif callback:
            return True

        return False
