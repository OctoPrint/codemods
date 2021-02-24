data = (x for x in range(10))

def a():
    for entry in data:
        yield entry

def b():
    yield entry from data
