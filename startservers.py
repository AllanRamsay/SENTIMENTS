#!/usr/bin/python
import sys, os
from servers import startServers, LOCKS

if "startservers.py" in sys.argv[0]:
    startServers(count=5)
    print "Servers started: lockfiles are %s"%(os.listdir(LOCKS))
