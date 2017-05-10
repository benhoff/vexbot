import argparse as _argparse


def get_kwargs():
    parser = _argparse.ArgumentParser()
    parser.add_argument('robot_name', default='vexbot', nargs='?')
    parser.add_argument('configuration_filepath', nargs='?')
    args = parser.parse_args()
    return vars(args)
