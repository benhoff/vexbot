#!/usr/bin/env python
"""
Generate client and server CURVE certificate files then move them into the
appropriate store directory, private_keys or public_keys.

Adapted from:
https://github.com/zeromq/pyzmq/blob/master/examples/security/generate_certificates.py

Original Author: Chris Laws
"""

import os
import sys
import shutil
import logging
import zmq.auth

from prompt_toolkit import prompt

from vexbot.util.create_vexdir import create_vexdir
from vexbot.util.get_vexdir_filepath import get_vexdir_filepath
from vexbot.util.get_certificate_filepath import get_certificate_filepath


def _handle_secret_exists():
    answer = prompt('Found some stuff, continue? [Y/N]: ')
    answer = answer.lower()


def _handle_public_exists():
    pass


def _generate_client_certificates():
    pass


def _generate_server_certificates():
    pass


def generate_certificates(base_dir):
    ''' Generate client and server CURVE certificate files'''
    public_keys_dir = os.path.join(base_dir, 'public_keys')
    secret_keys_dir = os.path.join(base_dir, 'private_keys')

    # Make the public and private key directories
    for path in (public_keys_dir, secret_keys_dir):
        if not os.path.exists(path):
            os.mkdir(path)

    # create new keys in certificates dir
    server_public_file, server_secret_file = zmq.auth.create_certificates(base_dir, "vexbot")
    client_public_file, client_secret_file = zmq.auth.create_certificates(base_dir, "client")

    vexbot_public = os.path.join(public_keys_dir, 'vexbot.key')
    client_public = os.path.join(public_keys_dir, 'client.key')

    vexbot_secret = os.path.join(secret_keys_dir, 'vexbot.key_secret')
    client_secret = os.path.join(secret_keys_dir, 'client.key_secret')

    # FIXME
    if os.path.exists(vexbot_public):
        pass

    if os.path.exists(client_public):
        pass

    if os.path.exists(vexbot_secret):
        pass

    if os.path.exists(client_secret):
        pass


    # move public keys to appropriate directory
    for key_file in os.listdir(base_dir):
        if key_file.endswith(".key"):
            shutil.move(os.path.join(base_dir, key_file),
                        os.path.join(public_keys_dir, '.'))

    # move secret keys to appropriate directory
    for key_file in os.listdir(base_dir):
        if key_file.endswith(".key_secret"):
            shutil.move(os.path.join(base_dir, key_file),
                        os.path.join(secret_keys_dir, '.'))


def _check_vexbot_filepath(create_if_missing=True):
    filepath = get_vexdir_filepath()
    is_missing = os.path.isdir(filepath)

    if create_if_missing and is_missing:
        create_vexdir()
    elif is_missing and not create_if_missing:
        logging.error('Vexbot filepath not found! Please create')


def main():
    _check_vexbot_filepath(create_if_missing=True)
    cert_path = get_certificate_filepath()
    if not os.path.exists(cert_path):
        os.mkdir(cert_path)

    generate_certificates(cert_path)


if __name__ == '__main__':
    main()
