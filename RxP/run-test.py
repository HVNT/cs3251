#!/usr/bin/env python

from rxp import *
import test
import logging

def main():
	test.testBind()
	test.testPacketAttributes()
	test.testHeader()
	test.testPacket()

logging.basicConfig(level=logging.INFO)

main()


