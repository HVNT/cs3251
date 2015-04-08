#!/usr/bin/env python

from rxp import *
import test
import logging

logging.basicConfig(level=logging.DEBUG)

test.add(test.testBind)
test.add(test.testPacketAttributesPickle)
test.add(test.testHeaderPickle)
test.add(test.testPacketPickle)
test.add(test.testPacketChecksum)
test.add(test.testSocketConnect)
test.add(test.testSocketSendRcv)
test.add(test.testSocketTimeout)

test.run(test.testSocketConnect)



