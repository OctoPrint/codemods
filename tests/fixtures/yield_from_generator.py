data = (x for x in range(10))


def fnord(x):
    return x


def a():
    for entry in data:
        yield entry


def b():
    for entry in data:
        yield entry


def c():
    yield from data


def d():
    for x in data:
        yield fnord(x)


def e():
    for x in data:
        yield x, True


def f():
    l = "aaaaaaaaaaaaaaaaaaa"
    for x in range(3):
        yield l[x:]
