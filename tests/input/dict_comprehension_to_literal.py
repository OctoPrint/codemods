foo = dict((k, v) for k, v in {"a": 1, "b": 2, "c": 3}.items())

foo = dict((x.a, x) for x in [{"a": 1}, {"a": 2}])

foo = {k: v for k, v in {"a": 1, "b": 2, "c": 3}.items()}
