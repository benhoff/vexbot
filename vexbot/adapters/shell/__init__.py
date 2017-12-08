from vexbot.command import extension
from vexbot.adapters.shell.observers import CommandObserver

from vexbot.extensions.develop import do_code
from vexbot.extensions.hidden import do_hidden
from vexbot.extensions.log import (log_level,
                                   set_log_debug,
                                   set_log_info,
                                   filter_logs,
                                   anti_filter)


extension(CommandObserver)(do_hidden)
extension(CommandObserver)(log_level)
extension(CommandObserver)(filter_logs)
extension(CommandObserver)(anti_filter)
extension(CommandObserver, hidden=True)(set_log_info)
extension(CommandObserver, alias=['source',])(do_code)
extension(CommandObserver, hidden=True)(set_log_debug)
