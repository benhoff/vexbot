import argparse as _argparse


def get_kwargs():
    parser = _argparse.ArgumentParser()
    parser.add_argument('--configuration_filepath', default=None)
    args = parser.parse_args()
    return vars(args)
