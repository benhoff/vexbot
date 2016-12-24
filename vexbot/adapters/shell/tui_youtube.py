import urwid

from vexbot.adapters.shell.tui_address import Address


def button_press():
    pass


def main():
    blank = urwid.Divider()
    content = [
            # TODO: filepath
            urwid.Edit('Client Secret Filepath: '),
            blank,
            *Address('Subscribe Address').content,
            blank,
            *Address('Publish Address').content,
            blank,
            urwid.GridFlow(
                [urwid.AttrWrap(urwid.Button(txt, button_press),
                    'buttn', 'buttnf') for txt in ['Ok', 'Cancel']],
                13, 3, 1, 'center'),
            ]



    header = urwid.AttrWrap(urwid.Text("Edit Youtube Settings", 'center'), 'header')
    listbox = urwid.ListBox(urwid.SimpleFocusListWalker(content))
    frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'), header=header)
    loop = urwid.MainLoop(frame)
    try:
        loop.run()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
