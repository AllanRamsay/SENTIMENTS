#!/usr/bin/python
import sys, os
from servers import startServers, LOCKS
from stemmer import stemAll

if "startstemmer.py" in sys.argv[0]:
    task = lambda x: "%s\n"%(" ".join(stemAll(x.strip())))
    if len(sys.argv) > 1:
        startServers(host=sys.argv[1], count=1, task=task)
    else:
        startServers(count=1, task=task)
    print "Servers started: lockfiles are %s"%(os.listdir(LOCKS))
