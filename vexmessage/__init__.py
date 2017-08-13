import pickle as _pickle
import textwrap as _textwrap


VERSION = '0.3.0'

class Message:
    def __init__(self,
                 target: str,
                 source, type,
                 version: str=VERSION,
                 **content):

        self.target = target
        self.source = source
        self.type = type
        self.VERSION = version
        self.contents = content

    def __repr__(self):
        s = "type: {}  target: {}  source: {}  version: {}  contents: {}"
        target = self.target
        if target == '':
            target = 'all'
        s = s.format(self.type,
                     target,
                     self.source,
                     self.VERSION,
                     self.contents)

        return _textwrap.fill(s)

def decode(frame) -> Message:
    target = frame[0].decode('ascii')
    deserial = _pickle.loads(frame[1])
    source = deserial[0]
    type = deserial[1]
    version = deserial[2]
    content = deserial[3]

    return Message(target, source, type, version, **content)


def encode(target: str,
           source: str,
           type: str,
           version: str=VERSION,
           **message) -> tuple:

    target = target.encode('ascii')
    serialization = _pickle.dumps((source, type, version, message))
    return (target, serialization)


def create_vex_message(target: str,
                       source: str,
                       type: str,
                       version: str=VERSION,
                       **msg) -> Message:

    return encode(target, source, type, version, **msg)


def decode_vex_message(frame):
    return decode(frame)

def create_request(source: str, type: str, version: str=VERSION, **request):
    source = source.encode('ascii')
    serialization = _pickles.dumps(('', type, version, request))
    return (source, serialization)


class Request:
    def __init__(self,
                 command: str,
                 source: str,
                 version: str=VERSION,
                 *args,
                 **kwargs):

        self.source = source
        self.command = command
        self.version = version
        self.args = args
        self.kwargs = kwargs




class VexTypes:
    command = 'CMD'
    response = 'RSP'
    message = 'MSG'
    # STAUS ?
