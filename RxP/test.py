from rxp import *
import ctypes

# lambda used to reduce
# arrays of assertions
r = lambda x,y: x and y

def testBind(port=8764):
	"""Tests socket.bind()"""

	logging.info("testing Socket.bind()")
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

	success = reduce(r, assertions)
	logging.info("success" if success else "failure")
	assert success

def testPacketAttributes(attrs=None):
	"""tests PacketAttributes class"""

	logging.info("testing PacketAttributes")

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

	success = reduce(r, assertions)
	logging.info("success" if success else "failure")
	assert success

def testHeader(fields=None):
	""""tests Header class"""

	logging.info("testing Header")

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

	success = reduce(r, assertions)
	logging.info("success" if success else "failure")
	assert success

def testPacket(header=None, data="Hello World!"):
	"""tests the Packet class"""

	logging.info("testing Packet")

	if header is None:
		header = Header(
			srcPort=8080,
			destPort=8081,
			seqNum=12345,
			rcvWindow=4096,
			checksum=123,
			attrs=17
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

	success = reduce(r, assertions)
	logging.info("success" if success else "failure")
	assert success





		

	