class Foo:
    pass


class Bar(Foo):
    def __init__(self, *args, **kwargs):
        super(Foo, self).__init__(*args, **kwargs)


class Fnord(Foo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
