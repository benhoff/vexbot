import urwid


class Address:
    def __init__(self, header=None, protocol=None, address=None, port=None):
        self.header = header
        self.protocol = protocol
        self.address = address
        self.port = port
        blank = urwid.Divider()

        radio_button = []

        self.content = [urwid.Text('{} Address Information:'.format(self.header)),
                blank,
                urwid.Padding(urwid.Text('Protocol:'), left=2),
                urwid.Padding(urwid.GridFlow(
                    [urwid.AttrWrap(urwid.RadioButton(radio_button, txt), 'buttn', 'buttnf')
                        for txt in ['tcp', 'ipc']], 13, 3, 1, 'left'), left =6),
                blank,
                urwid.Padding(urwid.Edit('Address: '), left=2),
                blank,
                urwid.Padding(urwid.IntEdit('Port: '), left=2),
                ]
