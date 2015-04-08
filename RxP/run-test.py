#!/usr/bin/env python

from rxp import *
import test
import logging

def main():
	test.testBind()
	test.testPacketAttributesPickle()
	test.testHeaderPickle()
	test.testPacketPickle()
	test.testPacketChecksum()
	test.testSocketConnect()

logging.basicConfig(level=logging.DEBUG)

# main()
test.testSocketSend()

