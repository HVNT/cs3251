import ctypes, socket, math, struct
import logging
from collections import OrderedDict
from sys import getsizeof

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
		self.sendWindow = 0
		# size of receiver window (bytes)
		self.rcvWindow = 0
		# connection status (see ConnectionStatus)
		self.connStatus = ConnectionStatus.NO_CONN
		# destination address (ipaddress, port)
		self.destAddr = ("", 0)
		# source port
		self.srcAddr = ("", 0)

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
				logging.warning("error binding: " + \
					repr(self.srcAddr) + \
					" already in use") 
				raise e

	def connect(self, destAddr):
		"""connects to destAddr given in format
		(ipaddr, portNum). Uses a handshake. The
		sender sends a SYN packet. The receiver
		sends back a SYN, ACK. The sender then
		sends an ACK and the handshake is complete.
		"""


	def listen(self):
		"""listens on the given port number for 
		packets. Blocks until a SYN packet is received.
		"""
		pass

	def accept(self):
		"""accepts an incoming connection. Implements
		the receiver side of the handshake. returns
		the sender's address.
		"""
		pass

	def send(self, msg):
		"""sends a message"""
		pass

	def rcv(self):
		"""receives data"""
		pass

	def close(self):
		"""closes the connection and unbinds the port"""
		pass

class Packet:
	"""Represents a single packet and includes
	header and data.
	"""

	# maximum sequence number
	MAX_SEQ_NUM = math.pow(2, 32)
	# maximum data size for one 
	# packet (bytes)
	MAX_DATA_LENGTH = math.pow(2, 16)
	# max window size for sender
	# or receiver (packets)
	MAX_WINDOW_SIZE = math.pow(2, 16)

	def __init__(self, header=None, data=""):
		self.data = data
		self.header = header or Header()

		if len(self.data) > Packet.MAX_DATA_LENGTH:
			raise RxPException(msg="too much data")

		if len(self.data) < Packet.MAX_DATA_LENGTH:
			pass

	def createFromMessage(msg):
		"""creates an array of packets from a 
		string message.
		"""
		pass

	def createFromDatagram(dgram):
		"""creates a single packet from a single
		UDP datagram using pickling.
		"""
		pass

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

	def __str__(self):
		# TODO edit to print header data
		d = self.___dict__ 
		return str(d)

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
		
		strr = "{\n"
		for item in Header.FIELDS:
			fieldName = item[0]
			if fieldName in self.fields:
				strr += "     "
				strr += fieldName + ' : ' 
				strr += str(self.fields[fieldName]) + '\n'
		strr += "}"

		return strr

class RxPException(Exception):
	"""Exception that gives details on RxP related errors."""

	def __init__(self, msg, innerException):
		self.msg = msg
		self.innerException = innerException
    
	def __str__(self):
		str = self.msg + "\n"
		str += repr(self.innerException)
		return str

class ConnectionStatus:
	"""enum that describes the status 
	of a connection
	"""
	NO_CONN = 1
	IDLE = 2
	SENDING = 3
	RECEVING = 4

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
		return reduce(lambda x,y: x | y, attrList)

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

		return attrs

	def __str__(self):
		return repr(self.attrs)

class WrapableNum:
	""" houses a number that increments when it is read.
	when the num reaches its max, it wraps around to
	zero.
	"""

	def __init__(self, step=1, max=0):
		self.max = max
		self.step = step
		self.num = 0

	@property
	def num(self):
	    # get num and increment
		num = self._num
		self._num += self.step
		# wrap around if max has been reached
		if self._num > self.max:
			self._num = 0
		return num
	@num.setter
	def num(self, value):
		self._num = value	
