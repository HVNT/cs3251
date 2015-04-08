from rxp import *
import ctypes
import threading
import time
from functools import reduce

tests = list()

def add(test):
	tests.append(test)

def run(test=None, index=None):

	if test is not None:
		logging.info(test.__name__ + "...")
		success = test()
		logging.info("...done")
		assert success
	elif index is not None:
		run(tests[index])
	else:
		runAll()

def runAll():
	for test in tests:
		run(test)

def testBind(port=8764):
	"""Tests socket.bind()"""

	assertions = []

	s1 = Socket()
	s2 = Socket()

	# test binding to a port that should be empty
	try:
		s1.bind(('127.0.0.1', port))
		assertions.append(True) 
	except Exception:
		assertions.append(False)

	# test binding to a port that is in use
	try:
		s2.bind(('127.0.0.1', port))
		assertions.append(False)
	except Exception:
		assertions.append(True)

	return all(assertions)

def testPacketAttributesPickle(attrs=None):
	"""tests PacketAttributes class"""

	if attrs is None:
		attrs = ('SYN', 'ACK')

	attrsP = PacketAttributes.pickle(attrs)
	attrs2 = PacketAttributes.unpickle(attrsP)
 	
	logging.debug(attrs)
	logging.debug(attrs2)

	assert len(attrs) == len(attrs2)

	assertions = []
	for index, item in enumerate(attrs):
		assertions.append(item == attrs2[index])

	return all(assertions)

def testHeaderPickle(fields=None):
	""""tests Header class"""

	if fields is None:
		attrs = PacketAttributes.pickle(('SYN', 'ACK'))
		fields = {
			"srcPort" : 8080,
			"destPort" : 8081,
			"seq" : 12345,
			"ack" : 12346,
			"rcvWindow" : 4096,
			"length" : 4096,
			"checksum" : 123,
			"attrs" : attrs
			}

	h = Header(**fields)
	h2 = Header.unpickle(h.pickle())
	
	logging.debug(h)
	logging.debug(h2) 

	assertions = []
	for item in Header.FIELDS:
		fieldName = item[0]
		val1 = h.fields[fieldName]
		val2 = h2.fields[fieldName]
		assertions.append(val1 == val2)

	return all(assertions)

def testPacketPickle(header=None, data="Hello World!"):
	"""tests the Packet class"""

	if header is None:
		attrs = PacketAttributes.pickle(('SYN', 'ACK'))
		header = Header(
			srcPort=8080,
			destPort=8081,
			seq=12345,
			rcvWindow=4096,
			attrs=attrs
			)
	
	p1 = Packet(header, data)
	p2 = Packet.unpickle(p1.pickle())

	logging.debug(p1)
	logging.debug(p2)

	assertions = []

	for item in Header.FIELDS:
		name = item[0]
		f1 = p1.header.fields[name]
		f2 = p2.header.fields[name]
		assertions.append(f1 == f2)

	assertions.append(p1.data == p2.data)

	return all(assertions)

def testPacketChecksum(p=None):

	if p is None:
		attrs = PacketAttributes.pickle(("SYN",))
		header = Header(
			srcPort=8080,
			destPort=8081,
			seq=123,
			rcvWindow=4096,
			attrs=attrs
			)

	p1 = Packet(header)
	p2 = Packet.unpickle(p1.pickle())

	logging.debug("chksum1: " + str(p1.header.fields["checksum"]))
	logging.debug("chksum2: " + str(p2.header.fields["checksum"]))

	return p2.verify()

def testSocketConnect():

	def runserver(server):
		try:
			server.listen()
			server.accept()
		except Exception as e:
			logging.debug(e)

	client = Socket()
	client.bind(('127.0.0.1', 8080))
	client.timeout = 3.0

	server = Socket()
	server.bind(('127.0.0.1', 8081))
	server.timeout = 3.0

	serverThread = threading.Thread(
		target=runserver, args=(server,))
	serverThread.setDaemon(True)
	serverThread.start()

	client.connect(server.srcAddr)
	logging.debug("client")
	logging.debug("ack: " + str(client.ack.num))
	logging.debug("seq: " + str(client.seq.num))

	serverThread.join()
	logging.debug("server:")
	logging.debug("ack: " + str(server.ack.num))
	logging.debug("seq: " + str(server.seq.num))

	assertions = []

	assertions.append(client.connStatus == ConnectionStatus.IDLE)
	assertions.append(server.connStatus == ConnectionStatus.IDLE)
	assertions.append(client.ack.num == server.seq.num)
	assertions.append(client.seq.num == server.ack.num)

	return all(assertions)

def testSocketSendRcv(message="Hello World!"):

	global servermsg
	servermsg = ""

	def runserver(server):
		global servermsg
		try:
			server.listen()
			server.accept()
			servermsg = server.rcv()
		except Exception as e:
			logging.debug(e)

	# create client and server
	client = Socket()
	client.bind(('127.0.0.1', 8080))
	client.timeout = 3.0
	server = Socket()
	server.bind(('127.0.0.1', 8081))
	server.timeout = 3.0

	# run server
	serverThread = threading.Thread(
		target=runserver, args=(server,))
	serverThread.setDaemon(True)
	serverThread.start()

	# connect to server
	client.connect(server.srcAddr)

	# send message
	client.send(message)

	# close server
	serverThread.join()

	# check if server data matches 
	# message
	logging.debug("client msg: " + str(message))
	logging.debug("server msg: " + str(servermsg))

	return message == servermsg

def testSocketTimeout():
	
	assertions = []

	client = Socket()
	client.timeout = 0.01
	client.bind(("127.0.0.1", 8080))
	server = Socket()
	server.timeout = 0.01
	server.bind(("127.0.0.1", 8081))

	def runserver(server):
		server.listen()
		server.accept()

	def expectTimeout(func, *args):
		logging.debug(
			"trying " + func.__name__ + "...")
		try:
			func(*args)
		except socket.timeout:
			assertions.append(True)
		else:
			assertions.append(False)

	# set up server
	serverThread = threading.Thread(
		target=runserver, args=(server,))
	serverThread.setDaemon(True)

	# test listening with a timeout
	expectTimeout(server.listen)

	# test connecting with no response
	expectTimeout(client.connect, ("127.0.0.1", 8081))

	# run server and connect
	serverThread.start()
	client.connect(server.srcAddr)

	expectTimeout(client.rcv)

	serverThread.join()

	return all(assertions)






