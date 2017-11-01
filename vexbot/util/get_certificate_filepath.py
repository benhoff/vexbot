from os import path

from vexbot.util.get_vexdir_filepath import get_vexdir_filepath


def get_certificate_filepath():
    vexdir = get_vexdir_filepath()
    certs = path.join(vexdir, 'certificates')
    return certs

def get_certificate_directories() -> (str, str):
    root = get_certificate_filepath()
    public_dir = 'public_keys'
    private_dir = 'private_keys'
    public_dir = path.join(root, public_dir)
    private_dir = path.join(root, private_dir)
    return public_dir, private_dir

def _certificate_helper(public_filepath: str,
                        secret_filepath: str) -> (str, str):

    public_dir, private_dir = get_certificate_directories()
    secret_filepath = path.join(private_dir, secret_filepath)
    public_filepath = path.join(public_dir, public_filepath)
    return public_filepath, secret_filepath


def get_vexbot_certificate_filepath() -> (str, bool):
    """
    Returns the vexbot certificate filepath and the whether it is the private
    filepath or not
    """
    public_filepath, secret_filepath = _certificate_helper('vexbot.key','vexbot.key_secret')
    if path.isfile(secret_filepath):
        return secret_filepath, True
    if not path.isfile(public_filepath):
        err = ('certificates not found. Generate certificates from the '
               'command line using `vexbot_generate_certificates`')
        raise FileNotFoundError(err)
    return public_filepath, False


def get_client_certificate_filepath() -> (str, bool):
    _, secret_filepath = _certificate_helper('client.key','client.key_secret')
    if not path.isfile(secret_filepath):
        err = 'certificates not found. Where they generated?'
        raise FileNotFoundError(err)
    return secret_filepath
