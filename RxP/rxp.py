import ctypes, socket, math, struct
import logging
from collections import OrderedDict
from sys import getsizeof
import random

class Socket:
	"""Socket contains all API methods needed
	to bind to a port, create a connection, send
	and receive data, and close the connection.
	"""

	# constructor
	def __init__(self):

		# create UDP socket
		self._socket = socket.socket(
			socket.AF_INET, socket.SOCK_DGRAM)

		# timeout (milliseconds). 0 => no timeout
		self.timeout = 0
		# size of sender window (bytes)
		self.sendWindow = 1
		# size of receiver window (bytes)
		self.rcvWindow = Packet.MAX_WINDOW_SIZE
		# connection status (see ConnectionStatus)
		self.connStatus = ConnectionStatus.NO_CONN
		# destination address (ipaddress, port)
		self.destAddr = ("", 0)
		# source port
		self.srcAddr = ("", 0)
		# seqNum
		self.seqNum = WrapableNum(max=Packet.MAX_SEQ_NUM)
		# ackNum
		self.ackNum = WrapableNum(max=Packet.MAX_SEQ_NUM)

	def __del__(self):
		# close connection if 
		# object is destroyed
		self.close()

	# timeout is used to interact with
	# self._socket's timeout property
	@property
	def timeout(self):
	    return self._socket.gettimeout()
	@timeout.setter
	def timeout(self, value):
		self._socket.settimeout(value)


	def bind(self, srcAddr):
		"""binds socket to the given port. port is optional.
		If no port is given, self.port is used. If self.port
		has not been set, this method does nothing.
		"""

		if srcAddr:
			self.srcAddr = srcAddr

		if self.srcAddr:
			try:
				self._socket.bind(srcAddr)
			except Exception, e:
				logging.debug("error binding: " + \
					repr(self.srcAddr) + \
					" already in use") 
				raise e

	def listen(self):
		"""listens on the given port number for 
		packets. Blocks until a SYN packet is received.
		"""

		while True:
			# wait to receive SYN
			data, addr = self._socket.recvfrom(self.rcvWindow)
			packet = self._packet(data)
			if packet.checkAttrs(("SYN",)):
				break

		# set ackNum 
		ackNum = packet.header.fields["seqNum"]
		self.ackNum.reset(ackNum+1)

		# set dest addr
		self.destAddr = addr

	def connect(self, destAddr):
		"""connects to destAddr given in format
		(ipaddr, portNum). Uses a handshake. The
		sender sends a SYN packet. The receiver
		sends back a SYN, ACK. The sender then
		sends an ACK and the handshake is complete.
		"""

		# set dest addr
		self.destAddr = destAddr

		# set initial sequence number for
		# new connection
		initial = random.randint(0, Packet.MAX_SEQ_NUM)
		self.seqNum.reset(initial)

		# send SYN packet with sequence number
		attrs = PacketAttributes.pickle(("SYN",))
		header = Header(
			srcPort=self.srcAddr[1],
			destPort=self.destAddr[1],
			seqNum=self.seqNum.next(),
			rcvWindow=self.rcvWindow,
			attrs=attrs
			)
		packet = Packet(header)
		self._socket.sendto(packet.pickle(), self.destAddr)

		# receive SYN, ACK and set ack num
		data, addr = self._socket.recvfrom(self.rcvWindow)
		packet = self._packet(data, addr)
		if not packet.checkAttrs(("SYN", "ACK")):
			raise RxPException(RxPException.UNEXPECTED_PACKET)

		# set ackNum
		ackNum = packet.header.fields["seqNum"]
		self.ackNum.reset(ackNum+1)

		# send ACK, change connection status
		attrs = PacketAttributes.pickle(("ACK",))
		header = Header(
			srcPort=self.srcAddr[1],
			destPort=self.destAddr[1],
			seqNum=self.seqNum.next(),
			rcvWindow=self.rcvWindow,
			attrs=attrs
			)
		packet = Packet(header)
		self._socket.sendto(packet.pickle(), self.destAddr)
		self.connStatus = ConnectionStatus.IDLE



	def accept(self):
		"""accepts an incoming connection. Implements
		the receiver side of the handshake. returns
		the sender's address.
		"""

		# set initial sequence number for
		# new connection
		initial = random.randint(0, Packet.MAX_SEQ_NUM)
		self.seqNum.reset(initial)

		# send SYN, ACK with sequence number
		attrs = PacketAttributes.pickle(("SYN","ACK"))
		header = Header(
			srcPort=self.srcAddr[1],
			destPort=self.destAddr[1],
			seqNum=self.seqNum.next(),
			rcvWindow=self.rcvWindow,
			attrs=attrs
			)
		packet = Packet(header)
		self._socket.sendto(packet.pickle(), self.destAddr)

		# receive ACK and change conn status
		data, addr = self._socket.recvfrom(self.rcvWindow)
		packet = self._packet(data, addr)
		if not packet.checkAttrs(("ACK",)):
			raise RxPException(RxPException.UNEXPECTED_PACKET)
		self.connStatus = ConnectionStatus.IDLE


	def send(self, msg):
		"""sends a message"""
		pass

	def rcv(self):
		"""receives data"""
		pass

	def close(self):
		"""closes the connection and unbinds the port"""
		self._socket.close()

	def _packet(self, data, addr=None):
		""" reconstructs a packet from data and verifies
		checksum and address (if addr is not None).
		"""

		packet = Packet.unpickle(data)

		# verify addr
		if addr is not None and addr != self.destAddr:
			raise RxPException(RxPException.OUTSIDE_PACKET)

		# verify checksum
		if not packet.verify():
			raise RxPException(RxPException.INVALID_CHECKSUM)

		# verify seqnum
		attrs = PacketAttributes.unpickle(
			packet.header.fields["attrs"])
		isSYN = "SYN" in attrs
		packetSeqNum = packet.header.fields["seqNum"]
		socketAckNum = self.ackNum.num
		if (not isSYN and packetSeqNum > 0 and 
			socketAckNum != packetSeqNum):
			logging.debug(str(socketAckNum) + \
			 ', ' + str(packetSeqNum))
			raise RxPException(RxPException.SEQ_MISMATCH)
		else:
			self.ackNum.next()

		return packet

class Packet:
	"""Represents a single packet and includes
	header and data.
	"""

	# maximum sequence number
	MAX_SEQ_NUM = math.pow(2, 32)
	# max window size for sender
	# or receiver (bytes)
	MAX_WINDOW_SIZE = 65485
	# Ethernet MTU (1500) - UDP header
	DATA_LENGTH = 1492

	def __init__(self, header=None, data=""):

		if len(data) > Packet.DATA_LENGTH:
			# error if too much packet data is given
			raise RxPException(msg="too much data")
		else:
			self.data = data
			self.header = header or Header()
			self.header.fields["length"] = len(data)
			self.header.fields["checksum"] = self._checksum()


	def pickle(self):
		""" returns a byte string representation
		using pickling"""

		b = bytearray()
		b.extend(self.header.pickle())
		b.extend(self.data)

		return b

	@staticmethod
	def unpickle(byteArr):
		""" returns an instance of Packet
		reconstructed from a byte string.
		"""
		p = Packet()

		p.header = Header.unpickle(
			byteArr[0:Header.LENGTH])
		p.data = str(byteArr[Header.LENGTH:])

		return p

	# http://stackoverflow.com/a/1769267
	@staticmethod
	def _add(a, b):
	    c = a + b
	    return (c & 0xffff) + (c >> 16)

	# http://stackoverflow.com/a/1769267
	def _checksum(self):
		self.header.fields["checksum"] = 0
		p = str(self.pickle())

		s = 0
		for i in range(0, len(p), 2):
		    w = ord(p[i]) + (ord(p[i+1]) << 8)
		    s = Packet._add(s, w)
		s = ~s & 0xffff

		return s

	def verify(self):
		# compare packet checksum with
		# calculated checksum
		packetChksum = self.header.fields["checksum"]
		calcChksum = self._checksum()

		return packetChksum == calcChksum

	def checkAttrs(self, expectedAttrs):
		# verify expected attrs
		attrs = PacketAttributes.unpickle(
			self.header.fields["attrs"])

		if len(attrs) != len(expectedAttrs):
			return False
		else:
			for attr in expectedAttrs:
				if (attr is not None and 
					attr not in attrs):
					return False
		return True
			

	def __str__(self):
		d = self.__dict__ 
		d2 = {}
		for key in d.keys():
			d2[key] = str(d[key])
		return str(d2)

class Header:
	"""Encapsulation of the header fields
	associated with a packet. See API docs
	for descriptions of each header field.
	"""

	# define binary types for use in header fields.
	uint16 = ctypes.c_uint16
	uint32 = ctypes.c_uint32

	# available header fields. formatted as:
	# fieldName, dataType, numBytes
	FIELDS = (
		("srcPort", uint16, 2),
		("destPort", uint16, 2),
		("seqNum", uint32, 4),
		("ackNum", uint32, 4),
		("rcvWindow", uint16, 2),
		("length", uint16, 2),
		("checksum", uint16, 2),
		("attrs", uint32, 4)
		)

	# sum of the length of all fields (bytes)
	LENGTH = sum(map(lambda x: x[2], FIELDS))

	def __init__(self, **kwargs):
		self.fields = {}
		keys = kwargs.keys()

		for item in Header.FIELDS:
			fieldName = item[0]
			fieldType = item[1]
			if fieldName in keys:
				field = kwargs[fieldName]
			else:
				field = 0
			self.fields[fieldName] = field

	def pickle(self):
		"""converts the object to a binary string
		that can be prepended onto a packet. pickle
		enforces size restrictions and pads fields
		"""
		byteArr = bytearray()

		# add fields to bytearray one field at a time
		for item in Header.FIELDS:
			fieldName = item[0]
			fieldType = item[1]
			fieldVal = self.fields[fieldName]
			if fieldVal is not None:
				byteArr.extend(bytearray(
					fieldType(fieldVal)))

		return byteArr

	@staticmethod
	def unpickle(byteArr):
		"""creates an instance of Header from a byte
		array. This must be done manually using knowledge
		about the order and size of each field.
		"""

		# ensure the byte array is of
		# type bytearray
		if not isinstance(byteArr, bytearray):
			byteArr = bytearray(byteArr)

		h = Header()
		base = 0
		for item in Header.FIELDS:

			fieldName = item[0]
			fieldType = item[1]
			fieldSize = item[2]

			# extract field from header using
			# base + offset addressing
			value = byteArr[base : base + fieldSize]

			# convert value from bytes to int
			field = fieldType.from_buffer(value).value

			# update base
			base += fieldSize

			# add field to header 
			h.fields[fieldName] = field

		return h

	def __str__(self):
		
		str_ = "{ "
		for item in Header.FIELDS:
			fieldName = item[0]
			if fieldName in self.fields:
				str_ += fieldName + ': ' 
				str_ += str(self.fields[fieldName]) + ', '
		str_ += " }"

		return str_

class RxPException(Exception):
	"""Exception that gives details on RxP related errors."""

	# exception types

	# checksums do not match
	INVALID_CHECKSUM = 1
	# packet sent from outside
	# connection
	OUTSIDE_PACKET = 2
	# connection timed out
	CONNECTION_TIMEOUT = 3
	# packet type not expected
	# SYN, ACK, etc
	UNEXPECTED_PACKET = 4
	# mismatch between packet seq
	# num and expected seq num
	SEQ_MISMATCH = 5

	DEFAULT_MSG = {
		INVALID_CHECKSUM: "invalid checksum",
		OUTSIDE_PACKET: "outside packet",
		CONNECTION_TIMEOUT: "connection timeout",
		UNEXPECTED_PACKET: "unexpected packet type",
		SEQ_MISMATCH: "sequence mismatch"
	}

	def __init__(self, type_, msg=None, innerException=None):
		self.type = type_
		self.inner = innerException
		if msg is None:
			self.msg = RxPException.DEFAULT_MSG[type_]
		else:
			self.msg = msg

	def __str__(self):
		return self.msg

class ConnectionStatus:
	"""enum that describes the status 
	of a connection
	"""
	NO_CONN = "no_conn"
	IDLE = "idle"
	SENDING = "sending"
	RECEVING = "receiving"

class PacketAttributes:
	"""class that generates the bit string that describes
	the type of the packet being sent.
	"""
	# possible attributes
	__values = ["SYN", "CLOSE", "NM", "EOM",  
		"ACK", "NOP", "SRQ"] 

	@staticmethod
	def pickle(attrs):
		"""produces a single byte string with the
		correct bit set for each pack type passed
		in as a string.
		"""
		submittedAttrs = list(attrs)
		attrList = []
		pos = 0

		# add attributes to list if they match
		# an attribute offered in __values
		for item in PacketAttributes.__values:
			if item in submittedAttrs:
				byte = 0b1 << pos
				attrList.append(byte)
			pos += 1

		# generate binary from array
		if len(attrList) > 1:
			byteStr = reduce(lambda x,y: x | y, 
				attrList)
		else:
			byteStr = attrList[0]
		
		return byteStr

	@staticmethod
	def unpickle(byteStr):
		"""creates an instance of PacketAttributes from
		a pickled instance (byte string)
		"""
		attrs = list()
		pos = 0

		# check each bit in the byte string
		for item in PacketAttributes.__values: 
			if (byteStr >> pos & 1):
				attrs.append(item)
			pos += 1

		return tuple(attrs)

	def __str__(self):
		return repr(self.attrs)

class WrapableNum:
	""" houses a number that increments when it is read.
	when the num reaches its max, it wraps around to
	zero.
	"""

	def __init__(self, initial=0, step=1, max=0):
		self.max = max
		self.step = step
		self.num = initial

	def reset(self, value):
		self.num = value

	def next(self):
		# get num and increment
		num = self.num
		self.num += self.step
		# wrap around if max has been reached
		if self.num > self.max:
			self.num = 0
		return num	

	def __str__(self):
		return str(self.num)
