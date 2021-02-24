def foo():
    pass


try:
    foo()
except EnvironmentError:
    pass

try:
    foo()
except IOError:
    pass

try:
    foo()
except WindowsError:
    pass

try:
    foo()
except socket.error:
    pass

try:
    foo()
except select.error:
    pass

try:
    foo()
except mmap.error:
    pass

try:
    foo()
except OSError:
    pass

try:
    foo()
except (EnvironmentError):
    pass

try:
    foo()
except (EnvironmentError, mmap.error):
    pass

try:
    foo()
except (EnvironmentError, ValueError, mmap.error):
    pass
