#!/usr/bin/env python
# 
# usage: ./run-test.py [-d]
# 

from rxp import *
from test import *
import logging
import subprocess
import time
import os
import threading
import sys
import getopt

C_ADDR = ("127.0.0.1", 8080)
S_ADDR = ("127.0.0.1", 8081)
N_ADDR = ("127.0.0.1", 5001)

opts, args = getopt.getopt(sys.argv[1:], "d")

if opts and "-d" in opts[0]:
	logging.basicConfig(level=logging.DEBUG)
else:
	logging.basicConfig(level=logging.INFO)

# set up tests
tester = Test()
tester.add(testBind)
tester.add(testPacketAttributesPickle)
tester.add(testHeaderPickle)
tester.add(testPacketPickle)
tester.add(testPacketChecksum)
tester.add(testSocketConnect, C_ADDR, S_ADDR, N_ADDR)
tester.add(testSocketSendRcv, C_ADDR, S_ADDR, N_ADDR)
tester.add(testSocketTimeout, C_ADDR, S_ADDR, N_ADDR)
tester.add(testRequestSendPermission, C_ADDR, S_ADDR, N_ADDR)

# run tests
tester.run()
