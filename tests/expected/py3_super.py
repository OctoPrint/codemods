class Foo:
    pass


class Bar(Foo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Fnord(Foo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class A:
    pass


class B(A, Fnord):
    def __init__(self, *args, **kwargs):
        super(Fnord, self).__init__(*args, **kwargs)
