def foo():
    pass


try:
    foo()
except OSError:
    pass

try:
    foo()
except OSError:
    pass

try:
    foo()
except OSError:
    pass

try:
    foo()
except OSError:
    pass

try:
    foo()
except OSError:
    pass

try:
    foo()
except OSError as exc:
    pass

try:
    foo()
except OSError:
    pass

try:
    foo()
except OSError:
    pass

try:
    foo()
except OSError:
    pass

try:
    foo()
except (ValueError, OSError):
    pass

try:
    foo()
except RuntimeError:
    pass

try:
    foo()
except (RuntimeError, ValueError) as error:
    pass
