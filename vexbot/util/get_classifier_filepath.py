from os import path
from vexbot.util.get_vexdir_filepath import get_vexdir_filepath


def get_classifier_filepath(name: str=None) -> str:
    if name is None:
        name = 'classifier.vex'
    directory = get_vexdir_filepath()
    return path.join(directory, name)


def get_entity_filepath(name: str=None) -> str:
    if name is None:
        name = 'entity_extractor.vex'
    directory = get_vexdir_filepath()
    return path.join(directory, name)
