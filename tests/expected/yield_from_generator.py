data = (x for x in range(10))


def a():
    yield from data


def b():
    yield from data


def c():
    yield from data
