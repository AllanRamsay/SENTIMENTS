#!/usr/bin/python
import sys, os
from servers import startServers, LOCKS
from stemmer import stemAll

if "startstemmer.py" in sys.argv[0]:
    startServers(count=5, task=stemAll)
    print "Servers started: lockfiles are %s"%(os.listdir(LOCKS))
