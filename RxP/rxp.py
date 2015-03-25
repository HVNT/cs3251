import ctypes, socket

# define types for use in header fields
c_uint8 = ctypes.c_uint8
c_uint16 = ctypes.c_uint16
c_uint32 = ctypes.c_uint32

class Socket:
	"""Socket contains all API methods needed
	to bind to a port, create a connection, send
	and receive data, and close the connection.
	"""

	def ConnectionStatus(Enum):
		NOT_CONNECTED = 1
		IDLE = 2
		SENDING = 3
		RECEIVING = 4

	def __init__(self):
		self.timeout = 0
		self.sendWindow = 0
		self.rcvWindow = 0
		self.connStatus = ConnectionStatus.NOT_CONNECTED
		self.port = 0

	def __del__(self):
		self.close()

	def create(self):
		"""creates a socket bound to the given port"""

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

class Connection:
	"""Represents a connection. Contains a UDP
	socket that is used to send and receive data.
	"""

	# nextSeqNum and nextAckNum are properties that
	# auto-increment and auto-wrap 

	@property
	def nextSeqNum(self):
		# get next seq num and increment
		seqNum = self._nextSeqNum++
		# wrap around if max has been reached
		if self._nextSeqNum > math.pow(2,32):
			self._nextSeqNum = 0
	    return seqNum
	@nextSeqNum.setter
	def nextSeqNum(self, value):
	    self._nextSeqNum = value

	@property
	def nextAckNum(self):
	    # get next ack num and increment
		ackNum = self._nextAckNum++
		# wrap around if max has been reached
		if self._nextAckNum > math.pow(2,32):
			self._nextAckNum = 0
	    return ackNum
	@nextAckNum.setter
	def nextAckNum(self, value):
	    self._nextAckNum = value
	
	def __init__(self):
		# public fields
		self.socket = socket.socket(
			socket.AF_INET, socket.SOCK_DGRAM)
		self.srcPort = 0
		self.destAddr = ()
		self.nextSeqNum = 0
		self.nextAckNum = 0

	def __del__(self):
		self.close()

	def open(self):
		"""opens a new connection"""

	def send(self, packetArray):
		"""sends an array of packets"""

	def rcv(self):
		"""receives data"""

	def close(self):
		"""closes the connection"""


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

class HEADER(Structure):
	"""Encapsulation of the header fields
	associated with a packet. See API docs
	for descriptions of each header field.
	"""

	__fields__ = [("srcPort", c_uint16),
				  ("destPort", c_uint16),
				  ("seqNum", c_uint32),
				  ("ackNum", c_uint32),
				  ("rcvWindow", c_uint16),
				  ("checksum", c_uint16),
				  ("opts", c_uint32)]


class RxPException(Exception):
	"""Exception that gives details on RxP related errors."""

	def __init__(self, msg, innerException):
        self.msg = msg
        self.innerException = innerException
    
    def __str__(self):
        return self.msg + '\n' + repr(self.innerException)
