from time import sleep as _sleep
from threading import Thread as _Thread

import zmq
from vexmessage import decode_vex_message


class ShellController:
    def __init__(self,
                 shell,
                 messaging,
                 **kwargs):

        self.messaging = messaging
        self._shell = shell
        self._loop_thread = _Thread(target=self._recv_loop)
        self._loop_thread.daemon = True

    def cmdloop(self, intro=None):
        self._shell.running = True
        self._loop_thread.start()
        return self._shell.cmdloop(intro)

    def _recv_loop(self):
        frame = None
        while True and self._shell.running:
            try:
                # NOTE: not blocking here to check the _exit_loop condition
                frame = self.messaging.sub_socket.recv_multipart(zmq.NOBLOCK)
            except zmq.error.ZMQError:
                pass

            _sleep(.5)

            if frame:
                message = decode_vex_message(frame)
                print(message)
                # NOTE: No message type other than `RSP` currently handeled
                if message.type == 'RSP':
                    s = "\n{}\n".format(self._shell.doc_leader)
                    self._shell.stdout.write(s)
                    header = message.contents.get('original', 'Response')
                    contents = message.contents.get('response', None)
                    # FIXME --------------------------------------
                    if (isinstance(header, (tuple, list))
                            and isinstance(contents, (tuple, list))
                            and contents):

                        for head, content in zip(header, contents):
                            self._shell.print_topics(head, (contents,), 15, 70)
                    else:
                        if isinstance(contents, str):
                            contents = (contents,)
                        self._shell.print_topics(header,
                                                 contents,
                                                 15,
                                                 70)
                    # ENDFIXME ----------------------------------

                    self._shell.stdout.write("vexbot: ")
                    self._shell.stdout.flush()
                frame = None
