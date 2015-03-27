import ctypes, socket, math, struct
import logging

# define types for use in header fields
c_uint8 = ctypes.c_uint8
c_uint16 = ctypes.c_uint16
c_uint32 = ctypes.c_uint32

# describes the status of a 
# connection (Enum)
class ConnectionStatus:
	NO_CONN = 1
	IDLE = 2
	SENDING = 3
	RECEVING = 4

class Socket:
	"""Socket contains all API methods needed
	to bind to a port, create a connection, send
	and receive data, and close the connection.
	"""

	# static fields
	MAX_SEQ_NUM = math.pow(2, 32)

	# constructor
	def __init__(self):

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

		# create UDP socket
		self._socket = socket.socket(
			socket.AF_INET, socket.SOCK_DGRAM)

	def __del__(self):
		# close connection if 
		# object is destroyed
		self.close()
	
	# properties with special behavior
	@property
	def nextSeqNum(self):
		
		# get next seq num and increment
		seqNum = self._nextSeqNum
		self._nextSeqNum += 1
		
		# wrap around if max has been reached
		if self._nextSeqNum > Socket.MAX_SEQ_NUM:
			self._nextSeqNum = 0

		return seqNum

	@nextSeqNum.setter
	def nextSeqNum(self, value):
	    self._nextSeqNum = value

	@property
	def nextAckNum(self):
	    
	    # get next ack num and increment
		ackNum = self._nextAckNum
		self._nextAckNum += 1
		
		# wrap around if max has been reached
		if self._nextAckNum > Socket.MAX_SEQ_NUM:
			self._nextAckNum = 0
		
		return ackNum

	@nextAckNum.setter
	def nextAckNum(self, value):
	    self._nextAckNum = value

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
				logging.info('error binding: ' + \
					repr(self.srcAddr) + \
					' already in use') 
				raise e


	def connect(self, destAddr):
		"""connects to destAddr given in format
		(ipaddr, portNum)
		"""

	def listen(self):
		"""listens on the given port number for 
		packets.
		"""

	def send(self, msg):
		"""sends a message"""

	def rcv(self):
		"""receives data"""

	def close(self):
		"""closes the connection and unbinds the port"""


class Packet:
	"""Represents a single packet and includes
	header and data.
	"""

	def __init__(self):
		self.data = None
		self.header = HEADER()

	def createFromMessage(msg):
		"""creates an array of packets from a 
		string message.
		"""

	def createFromDatagram(dgram):
		"""creates a single packet from a single
		UDP datagram using pickling.
		"""

	def pickle(self):
		""" returns a byte string representation
		using pickling"""
		return pickle.dumps(self)

class Header:
	"""Encapsulation of the header fields
	associated with a packet. See API docs
	for descriptions of each header field.
	"""

	def __init__(self, *args, **kwargs):
		self.srcPort = kwargs.srcPort
		self.destPort = kwargs.destPort
		self.seqNum = kwargs.seqNum
		self.ackNum = kwargs.ackNum
		self.rcvWindow = kwargs.rcvWindow
		self.checksum = kwargs.checksum
		self.varLength = kwargs.varLength

class RxPException(Exception):
	"""Exception that gives details on RxP related errors."""

	def __init__(self, msg, innerException):
		self.msg = msg
		self.innerException = innerException
    
	def __str__(self):
		return self.msg + '\n' + repr(self.innerException)
