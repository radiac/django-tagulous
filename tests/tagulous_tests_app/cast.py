"""
Objects for cast.py tests
"""


class OldBase:
    def __init__(self, v):
        self.v = v


class Target(OldBase):
    pass


class NewBase:
    pass
