class User(object):
    def __init__(self, id, *args, **kwargs):
        self.id = id
        for k, v in kwargs.items():
            setattr(self, k, v)

