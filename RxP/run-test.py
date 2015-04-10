#!/usr/bin/env python

from rxp import *
from test import *
import logging
import subprocess
import time
import os
import threading

# PYTHON2_EX = "/usr/bin/python"
# N_PATH = os.path.dirname(
# 	os.path.realpath(__file__)) + \
# 	"/../NetEmu/NetEmu.py"
# N_PORT = 5001
# N_LOSS = "1"
# N_CORR = "1"
# N_DUPL = "1"
# N_DELY = "0"
# N_REOD = "1"

C_ADDR = ("127.0.0.1", 8080)
S_ADDR = ("127.0.0.1", 8081)
N_ADDR = ("127.0.0.1", 5001)

LOG_LVL = logging.DEBUG

# set log level
logging.basicConfig(level=LOG_LVL)

# cmd = [PYTHON2_EX, N_PATH, str(N_PORT), "-l", N_LOSS, 
# 	"-c", N_CORR, "-d", N_DUPL, "-D", N_DELY, "-r", N_REOD]

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
tester.run(index=-1)
