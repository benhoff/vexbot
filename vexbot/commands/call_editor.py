import os
import random
import string
import tempfile
from subprocess import call


def call_editor(directory=None):
    editor = os.environ.get('EDITOR', 'vim')
    initial_message = b""
    file = None
    filename = None

    if directory is not None:
        # create a random filename
        filename = ''.join(random.choice(string.ascii_uppercase +
                                         string.digits) for _ in range(8))

        filename = filename + '.py'
        # TODO: loop back if isfile is True
        filepath = os.path.join(directory, filename)
        file = open(filepath, 'w+b')
    else:
        file = tempfile.NamedTemporaryFile(prefix=directory, suffix='.py')
        filename = file.name
    current_dir = os.getcwd()
    os.chdir(directory)
    file.write(initial_message)
    file.flush()
    call([editor, filename])
    file.close()
    file = open(filename)
    message = file.read()
    file.close()
    os.chdir(current_dir)

    return message
