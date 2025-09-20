# Fallctf 2025 Badge

This is the fallctf 2025 badge. It is written in Micropython, which is a subset of Python designed for microcontrollers.

In order to improve performance and reduce the memory usage, most of our code has been "frozen" into the micropython build. This means that it is packaged with the full micropython binary. To make hacking easier, a copy of the source code is provided here in the zip file. If you wish to make changes, simply make a copy of a file and move to the top level directory. For example, if you wanted to change settings.py (`import settings`), copy it from `src/settings.py` to the root and make changes there. Any changes will override code frozen in the binary.
