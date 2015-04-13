from rxp import *
import ctypes
import threading
import time
from functools import reduce

class Test:

	def __init__(self):
		self.tests = list()
		self.clientAddr = None
		self.serverAddr = None
		self.netAddr = None

	def add(self, func, *args):
		self.tests.append((func, args))

	def run(self, test=None, args=(), index=None):

		if test is not None:
			logging.info(test.__name__ + "...")
			success = test(*args)
			logging.info("...done")
			assert success
		elif index is not None:
			self.run(
				test=self.tests[index][0], 
				args=self.tests[index][1])
		else:
			self.runAll()

	def runAll(self):
		for test in self.tests:
			self.run(
				test=test[0], 
				args=test[1])

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
			"recvWindow" : 4096,
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
			recvWindow=4096,
			attrs=attrs
			)
	
	p1 = Packet(header, data)
	p2 = Packet.unpickle(p1.pickle(), toString=True)

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
			recvWindow=4096,
			attrs=attrs
			)

	p1 = Packet(header)
	p2 = Packet.unpickle(p1.pickle())

	logging.debug("chksum1: " + str(p1.header.fields["checksum"]))
	logging.debug("chksum2: " + str(p2.header.fields["checksum"]))

	return p2.verify()

def testSocketConnect(clientAddr, serverAddr, netAddr, timeout=3):

	def runserver(server):
		try:
			server.listen()
			server.accept()
		except Exception as e:
			logging.debug("server " + str(e))

	client = Socket()
	client.bind(clientAddr)
	client.timeout = timeout

	server = Socket()
	server.bind(serverAddr)
	server.timeout = timeout

	serverThread = threading.Thread(
		target=runserver, args=(server,))
	serverThread.setDaemon(True)
	serverThread.start()

	client.connect(netAddr)
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

def testSocketSendRcv(clientAddr, serverAddr, netAddr, timeout=3, message="Hello World!"):

	global servermsg
	servermsg = ""

	def runserver(server):
		global servermsg
		try:
			server.listen()
			server.accept()
			servermsg = server.recv()
		except Exception as e:
			logging.debug("server " + str(e))

	# create client and server
	client = Socket()
	client.bind(clientAddr)
	client.timeout = timeout
	client.resendLimit = 10
	client.acceptStrings = True

	server = Socket()
	server.bind(serverAddr)
	server.timeout = timeout
	server.resendLimit = 10
	server.acceptStrings = True


	# run server
	serverThread = threading.Thread(
		target=runserver, args=(server,))
	serverThread.setDaemon(True)
	serverThread.start()

	# connect to server
	client.connect(netAddr)

	# send message
	client.send(message)

	# close server
	serverThread.join()

	# check if server data matches 
	# message
	logging.debug("client msg: " + str(message))
	logging.debug("server msg: " + str(servermsg))

	return message == servermsg

def testSocketTimeout(clientAddr, serverAddr, netAddr, timeout=3):
	
	assertions = []

	client = Socket()
	client.timeout = timeout
	client.bind(clientAddr)
	server = Socket()
	server.timeout = timeout
	server.bind(serverAddr)

	def runserver(server):
		server.listen()
		server.accept()

	def expectTimeout(func, *args):
		logging.debug(
			"trying " + func.__name__ + "...")
		try:
			func(*args)
		except RxPException as e:
			if e.type == RxPException.CONNECTION_TIMEOUT:
				assertions.append(True)
			else:
				assertions.append(False)

	# set up server
	serverThread = threading.Thread(
		target=runserver, args=(server,))
	serverThread.setDaemon(True)

	# test listening with a timeout
	expectTimeout(server.listen)

	# run server and connect
	serverThread.start()
	client.connect(netAddr)

	expectTimeout(client.recv)

	serverThread.join()

	return all(assertions)

def testRequestSendPermission(clientAddr, serverAddr, netAddr, timeout=3):

	message = "Hello World!"
	servermsg = " right back at ya"
	expectedResult = message + servermsg

	client = Socket()
	client.timeout = timeout
	client.bind(clientAddr)
	client.acceptStrings = True
	server = Socket()
	server.timeout = timeout
	server.bind(serverAddr)
	server.acceptStrings = True

	def runserver(server):
		server.listen()
		server.accept()
		msg = server.recv()
		server.send(msg + servermsg)

	# create and start server thread
	serverThread = threading.Thread(
		target=runserver, 
		args=(server,))
	serverThread.daemon = True
	serverThread.start()

	# connect to server
	client.connect(netAddr)

	client.send(message)
	result = client.recv()

	serverThread.join()

	logging.debug("expected: " + expectedResult)
	logging.debug("result: " + result)

	return result == expectedResult






