
import socket, sys, re, os, shutil
import threading, time
from useful import *

PYTHONPORTS = 56224
HOST = "localhost"
LOGS = "LOGS"
LOCKS = "LOCKS"
RAMAPP = "ramapp.cs.man.ac.uk"

def doit(x):
    try:
        return x
    except:
        return "Couldn't do '%s'"%(x)
    
def lockfile(port):
    return os.path.join(LOCKS, "locked%s"%(port))

def portfile(port):
    return os.path.join(LOCKS, "port%s"%(port))

def lock(msg, port):
    with safeout(lockfile(port)) as write:
        write(msg)

def unlock(port):
    try:
        os.remove(lockfile(port))
    except:
        print "%s didn't exist?"%(lockfile(port))

"""
Probably better to do logging in one central place: this does it in
the directory where startServers was run from, which could be
confusing and which does require a bit of mildly time-consuming
inspection of files
"""
def log(who, msg):
    logfile = os.path.join(os.getcwd(), LOGS, "log")
    if os.path.exists(logfile):
        mode = "a"
    else:
        mode = "w"
    with safeout(logfile, mode=mode, encoding="UTF-8") as write:
        msg = "%s at %s: %s\n"%(who, datetime.datetime.today().isoformat(' '), msg)
        print msg
        write(msg)
        
def listen(host=HOST, port=PYTHONPORTS, task=doit):
    me = "LISTENER, host %s, port %s"%(host, port)
    log(me, "getting socket on port %s"%(port))
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
    except Exception as e:
        log(me, e)
        return
    while True:
        try:
            converse(me, s, port, task=task)
        except Exception as e:
            log(me, e)

"""
managing all the log messages probably takes as much time as doing
what the client asked for. Once I trust it all, I'll probably just log
the actual exchange, and I'll do that after I've sent the reply back,
to minimise the delay the client experiences. But unless we're
overwhelmed with requests, the fact that I've got N servers ready and
waiting will help.
"""
def converse(me, s, port, task=doit):
    s.listen(port)
    log(me, "listening for client on %s"%(port))
    conn, addr = s.accept()
    lock("%s locked by %s"%(port, conn), port)
    log(me, "contacted by %s"%(addr,))
    try:
        query = conn.recv(1024)
        answer = task(query)
    except Exception as e:
        answer = e
    conn.sendall("%s"%(answer))
    log(me, "sent back '%s'"%(answer))
    conn.close()
    unlock(port)
    log(me, "done")

def connect(host=HOST, port=PYTHONPORTS):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = PYTHONPORTS
    print host, port
    s.connect((host, port))
    
def askserver(msg, host=HOST):
    me = "client"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = PYTHONPORTS
    """
    Get the first free port
    """
    while os.path.exists(lockfile(port)):
        port += 1
    """
    Start a server at this port if there isn't already one running: use
    the global value for TASK which will have been set in the initial call of
    startSServers
    """
    print portfile(port)
    print "MSG %s"%(msg)
    s.connect((host, port))
    log(me, "connected(%s)"%(port))
    s.sendall(msg)
    print "SENT %s"%(msg)
    wholething = ""
    while True:
        data = str(s.recv(1024))
        if len(data) > 0:
            wholething += str(data)
        else:
            break
    s.close()
    return wholething

def startServer(host=HOST, port=PYTHONPORTS, task=doit):
    with safeout(os.path.join(LOCKS, "port%s"%(port))) as write:
        write("%s started"%(port))
    print "Starting at %s, %s"%(host, port)
    threading.Thread(target=lambda:listen(host=host, port=port, task=task)).start()
            
def startServers(host=HOST, startport=PYTHONPORTS, count=1, task=doit):
    global TASK
    TASK = task
    try:
        shutil.rmtree(LOCKS)
    except:
        print "LOCKS not deleted because it didn't exist"
    makedirs(LOCKS)
    makedirs(LOGS)
    for port in range(startport, startport+count):
        """
        If we don't have a little nap between creating listeners, it
        seems to have difficulty making the initial connection. I
        don't know why, I'm just going to live with it

        THERE DOESN'T SEEM TO BE ANY WAY OF KILLING THE LISTENERS
        OTHER THAN BY KILLING THE MAIN THREAD
        """
        threading._sleep(5)
        startServer(host=host, port=port, task=task)
    return startport
