#!/usr/bin/env python
# This script is used during debugging in Eclipse IDE which starts the server.
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('pyramid', 'console_scripts', 'pserve')()
    )
