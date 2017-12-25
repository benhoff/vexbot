import inspect as _inspect
import functools as _functools


# http://rasa-nlu.readthedocs.io/en/latest/tutorial.html#preparing-the-training-data
def intent(function=None,
           name: str=None):

    if function is None:
        return _functools.partial(intent,
                                  name=name)

    function._vex_intent = True
    function._vex_intent_name = name
    return function


class Entity:
    def __init__(self, text: str, start: int, end: int, name: str, type_: str, value: str=None):
        """
        Args:
            text: Example utterance
            start: Starting position of the value
            end: Ending position of the value
            name: Name of the entity
            type_: Entity Type
        """
        self.text = text
        self.start = start
        self.end = end
        self.name = name
        self.type = type_
        if value is None:
            value = name
        self.value = value


class FindEntity:
    def __init__(text, value, name):
        pass
