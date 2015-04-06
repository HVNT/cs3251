from rxp import *
import ctypes
import threading
import time

def assert_(result):
	if isinstance(result, bool):
		success = result
	else:
		success = reduce(lambda x,y: x and y, 
			result)

	logging.info("success" if success else "failure")
	assert success

def testBind(port=8764):
	"""Tests socket.bind()"""

	logging.info("testBind...")
	assertions = [False, False]

	s1 = Socket()
	s2 = Socket()

	# test binding to a port that should be empty
	try:
		s1.bind(('127.0.0.1', port))
		assertions[0] = True 
	except Exception, e:
		assertions[0] = False

	# test binding to a port that is in use
	try:
		s2.bind(('127.0.0.1', port))
		assertions[1] = False
	except Exception, e:
		assertions[1] = True

	assert_(assertions)

def testPacketAttributesPickle(attrs=None):
	"""tests PacketAttributes class"""

	logging.info("testPacketAttributesPickle...")

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

	assert_(assertions)

def testHeaderPickle(fields=None):
	""""tests Header class"""

	logging.info("testHeaderPickle...")

	if fields is None:
		attrs = PacketAttributes.pickle(('SYN', 'ACK'))
		fields = {
			"srcPort" : 8080,
			"destPort" : 8081,
			"seqNum" : 12345,
			"ackNum" : 12346,
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

	assert_(assertions)

def testPacketPickle(header=None, data="Hello World!"):
	"""tests the Packet class"""

	logging.info("testPacketPickle...")

	if header is None:
		header = Header(
			



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

	assert_(assertions)

def testPacketChecksum(p=None):

	logging.info('testPacketChecksum...')

	if p is None:
		attrs = PacketAttributes.pickle(("SYN",))
		header = Header(
			srcPort=8080,
			destPort=8081,
			seqNum=123,
			rcvWindow=4096,
			attrs=attrs
			)

	p1 = Packet(header)
	p2 = Packet.unpickle(p1.pickle())

	logging.debug("chksum1: " + str(p1.header.fields["checksum"]))
	logging.debug("chksum2: " + str(p2.header.fields["checksum"]))

	assert_(p2.verify())

def testSocketConnect():

	logging.info('testSocketConnect...')

	def runserver(server):
		try:
			server.listen()
			server.accept()
		except Exception, e:
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
	logging.debug("ack: " + str(client.ackNum))
	logging.debug("seq: " + str(client.seqNum))

	serverThread.join()
	logging.debug("server:")
	logging.debug("ack: " + str(server.ackNum))
	logging.debug("seq: " + str(server.seqNum))