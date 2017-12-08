#!/usr/bin/python

from servers import askserver

if "runserver.py" in sys.argv[0]:
    print askserver(sys.argv[1])
