import urwid

from vexbot.settings_manager import SettingsManager


def _button_press(*args):
    pass

def menu(items, callback_func, klass='Button'):
    """
    just for robot settings currently
    """
    klass = getattr(urwid, klass, 'Button')
    body = []
    for i in items:
        button = klass(i)
        urwid.connect_signal(button, 'click', callback_func, i)
        body.append(button)
    return urwid.BoxAdapter(urwid.ListBox(urwid.SimpleFocusListWalker(body)), 8)


def check_menu(items):
    """
    just for robot settings currently
    """
    body = []
    for i in items:
        button = urwid.CheckBox(i)
        body.append(button)
    return urwid.BoxAdapter(urwid.ListBox(urwid.SimpleFocusListWalker(body)), 8)


def radio_menu(items, callback_func):
    """
    just for robot settings currently
    """
    body = []
    for i in items:
        button = urwid.RadioButton(body, i, on_state_change=callback_func)
    return urwid.BoxAdapter(urwid.ListBox(urwid.SimpleFocusListWalker(body)), 8)

class VexTextInterface:
    def __init__(self, settings_manager=None):
        if settings_manager is None:
            settings_manager = SettingsManager()

        self.settings = settings_manager

    blank = urwid.Divider()

    buttons = urwid.GridFlow(
            [urwid.AttrWrap(urwid.Button(txt, _button_press),
                            'buttn', 'buttnf') for txt in ['Ok', 'Cancel']],

            13, 3, 1, 'center'),

    def _get_normal_addresses(self):
        return tuple()

    def _get_robot_addresses(self):
        return tuple()


    def handle_input(self, event):
        if event == "up":
            pass
        elif event == "down":
            pass

    def _execute(self, widgets, header):
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(widgets))
        frame = urwid.Frame(listbox, header=header)
        loop = urwid.MainLoop(frame, unhandled_input=self.handle_input)
        loop.screen.set_terminal_properties(colors=256)
        try:
            loop.run()
        except KeyboardInterrupt:
            return False
        return True


    def robot_settings(self):
        context = urwid.Edit('Context: ')
        name = urwid.Edit('Name: ')
        contexts = self.settings.get_all_contexts()

        def callback(_, context_name):
            button_context = self.settings.get_robot_model(context_name)
            context.set_edit_text(button_context.context)
            name.set_edit_text(button_context.name)

        contexts = menu(contexts, callback)
        def do_nothing(*args):
            pass
        addresses = self.settings.get_all_addresses()
        check_addresses = check_menu(addresses)

        # TODO: add in ability to create/update
        address = urwid.Edit('Address: ')
        port = urwid.IntEdit('Port: ')

        widgets = [contexts,
                   context,
                   name,
                   self.blank,
                   AdapterAddress(self.settings),
                   self.blank,
                   urwid.Text('Add or Modify Address'),
                   urwid.Text('Subscription Addresses'),
                   check_addresses,
                   self.blank,
                   *self.buttons]
        header = urwid.AttrWrap(urwid.Text("Edit Robot Settings", 'center'), 'header')

        save = self._execute(widgets, header)
        if not save:
            return


    def irc(self):
        service_name = urwid.Edit('Service Name: ')
        password = urwid.Edit('Password: ')
        channel = urwid.Edit('Channel: ')
        nick = urwid.Edit('Nick: ')
        host = urwid.Edit('Host: ')
        addresses = AdapterAddresses()

        widgets = [service_name,
                   password,
                   channel,
                   nick,
                   host,
                   addresses.widget]

        header = urwid.AttrWrap(urwid.Text("Edit Irc Settings", 'center'), 'header')
        save = self._execute(widgets, header)
        if not save:
            return

class AdapterAddress(urwid.GridFlow):
    def __init__(self, settings):
        addresses = list(settings.get_all_addresses())
        addresses.insert(0, '(None)')
        def callback(_, text):
            pass

        def _fancy_callback(*args):
            # TODO: actually look these up in the session
            address.set_edit_text('')
            port.set_edit_text('')

        leftmost = radio_menu(['publish',
                               'heartbeat'],
                        _fancy_callback)

        center = radio_menu(addresses, callback)


        right = urwid.BoxAdapter(urwid.ListBox(urwid.SimpleFocusListWalker(right)), 10)
        content = [leftmost, center]

        super().__init__(content,
                         cell_width=20,
                         h_sep=3,
                         v_sep=1,
                         align='left')

    @property
    def widgets(self):
        return tuple()



def main():
    listbox = urwid.ListBox(urwid.SimpleFocusListWalker(content))
    frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'), header=header)
    loop = urwid.MainLoop(frame)
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
