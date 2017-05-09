import argparse as _argparse


def get_args():
    parser = _argparse.ArgumentParser()
    parser.add_argument('robot_name', default='vexbot', nargs='?')
    parser.add_argument('configuration_filepath', nargs='?')
    args = parser.parse_args()
    return args
