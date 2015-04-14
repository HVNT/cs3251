__RxP, FxA__

**Authors**

	Benjamin Newcomer: bnewcomer@gatech.edu
	Wataru Ueno: wataruueno@gatech.edu

	CS 3251 A
	April 13, 2015
	Programming Assignment 2

**Files**

	rxp.py
		The RxP module is a python3 implementation of the RxP protocol
	fxa.py
		The 
	runserver.py
		./run-server.py X A P 
		Arguments:
			X: the port number at which the FxA-server’s UDP socket should bind to (odd number) 
			A: the IP address of NetEmu
			P: the UDP port number of NetEmu
		Commands:
			terminate Shut-down FxA-Server gracefully
	runclient.py
		./run-client.py X A P 
		Arguments:
			X: the port number at which the FxA-server’s UDP socket should bind to (odd number) 
			A: the IP address of NetEmu
			P: the UDP port number of NetEmu
		Commands:
			connect - The FxA-client connects to the FxA-server (running at the same IP host). 
			get F - The FxA-client downloads file F from the server (if F exists in the same directory with the FxA-server program). 
			post F - The FxA-client uploads file F to the server (if F exists in the same directory with the FxA-client program). This feature will be treated as extra credit for up to 20 project points.
			disconnect - The FxA-client terminates gracefully from the FxA-server. 
	py3env/
		A python 3.4.3 environment
		Commands:
			source py3env/bin/activate - activates the python 3.4.3 environment
			deactivate - deactivates the environemnt if it is currently active

**Usage**

	RxP: this module requires python3, so any programs using the rxp module must use python 3.4.3. A python 3.4.3 environment is provided in py3env. To activate the environment, enter "source py3env/bin/activate" on the command line. Then use the command line as your normally would.

	NetEmu: this program requires python 2.x.x, so you must execute it in an environment equipped with python 2.x.x. Because NetEmu was provided by the professors, no environments have been provided for running this program.

	run-client.py/run-server.py: Because these files use the rxp module, they should be run in a python 3.4.3 environement. See RxP Usage for details.

**Protocol Description**

	RxP is a connection-oriented, reliable transport layer protocol. It operates in application space on top of UDP. RxP is a lightweight relative of TCP and focuses on the most essential components of its predecessor. RxP manages connections much the same way as TCP. It uses handshakes, maintains connections, and has states controlling the flow of communication. The application using RxP will open a connection (which is established via a handshake), then send messages with byte stream semantics (no message boundaries). On the receiver end messages are reconstructed and can be passed to the application immediately or after a full message is reconstructed.

	RxP uses window-based flow control by sending a receiver window size in each packet header that communicates the amount of data the receiver can receive. To combat connection problems, RxP sends a NOP at regular intervals to ensure the connection remains active and it attempts to reestablish lost connections for a period of time before shutting down.

	Pipelinining: 
	We are implementing a selective repeat pipelined protocol. The sender sends each packet along with a sequence number associated with that packet. The receiver then knows what sequence number to expect based on the handshake and the previous packets received. We will describe how our protocol handles lost packet and corrupt packets next.

	Lost or corrupt packets: 
	In the case that that the receiver receives corrupt packets, the receiver sends an ACK with the sequence number it is expecting (it will be the sequence number of the corrupt packet in this case). This way the sender knows which packet to send from.  If the packets are lost and the receiver never receives them, then the receiver will not send any ACKs and will be waiting for messages from the sender. The sender will eventually timeout, and resend the packets.

	Out-of-order packets:
	If one of the packets are lost or are out-of-order, then the receiver will do its best to reassemble the packets in the right order. It will do so by waiting until it receives all the packets up to the window size. If the packets are lost then, the receiver will timeout. The receiver will figure out up to what sequence number it received properly even if it is out of order and send an ACK .

	Duplicate Packets:
	If the receiver receives duplicate packets, the receiver will simply trash the latter packets and keep the first packet it received.

	Bi-directional data transfers 
	Our protocol supports bi-directional data transfers by default. Whoever is the current sender is able to send messages and can expect that the other host is receiving. The host that initiates the connection first starts off as the sender. As long as the sender is sending, they can expect the receiver to be waiting for a message. 
	The receiver can begin sending any time the current sender is listening.

**Api**

class Socket
	
	Socket is the main object used to interact with the RxP API. Socket is used to bind ports, send and receive data, and manage connections.
	
	Methods:
		socket.bind(addr)
			
			Returns a socket instance bound to the address and port number given by addr. Throws an RxPException if the port number is unavailable or invalid.

			ex. socket.bind(("127.0.0.1", 8080))
		
		socket.connect(destAddr)
			
			Connects to a device with IP address given by destAddr[0] on the port number given by destAddr[1]. Returns True if connection was made successfully. Throws an RxPException if parameters are invalid, no device was found with given ip address and port number, or if connection was not initiated successfully.
			
			ex. socket.connect(("127.0.0.1", 8080))
		
		socket.listen()
			
			Listens on the set port for a connection request. An RxPException is thrown if the socket times out.

			ex. socket.listen()

		socket.accept()

			Accepts an incoming connection. Must be used directly after socket.listen() to correctly establish a connection.

			ex. socket.accept()

		socket.send(message)

			Sends a message to the receiving device. send() throws an RxPException if the connection is closed (and cannot be opened) before or during sending.
		
			ex. socket.send("Hello World!")

		socket.recv()
			
			Receives a message (blocks until a message is received). If socket.acceptStrings is true, then socket.recv() sends data to the application as as a string, otherwise it passes back a byte string. recv() throws an RxPException if the connection times out.

			ex. msg = socket.rcv()

		socket.close()

			Closes a connection and releases the port number. Closing one end of a connection triggers the other end to close.
	
			ex. socket.close()

	Properties
		socket.srcAddr
			IP address and port number of the client.
			("127.0.0.1", 8080)
		socket.destAddr
			IP address and port number of the destination.
			("127.0.0.1", 8081)
		socket.connStatus
			Enum that denotes the status of the connection. See ConnectionStatus.
		socket.recvWindow
			The size of the receive buffer
		socket.sendWindow
			The size of the send window (the number of packets that can be sent without listening for an ACK)
		socket.timeout
			The timeout for the connection in seconds. None means no timeout.
		socket.acceptStrings
			True allows the user to pass in and receive strings. If False, the socket expects and returns byte strings. Defaults to False.

class RxPException
	
	RxPException is an Exception class that provides information about errors related to the RxP API.

	Properties
		type
			enum property that gives additional information about the type pf exception that occurred. Values are: TIMEOUT, CONN_NOT_OPEN,  INVALID_ARGUMENT, CONN_FAILURE 
		message
			Details about the error that occurred.

enum ConnectionStatus
	
	An enum that represents the current state of the socket connection. Values are: CLOSED, SENDING, RECEIVING, WAITING, LISTENING


**Known Problems**

	- When the final ACK of the connection handshake is dropped, this causes the SYNACK packet to be resent, but never received. This causes the rest of the message sending to fail.
	- For the get command, the source file must be in the same directory as the run-server.py file and the get destination file must be in the same directory as the run-client.py file.
	- For the post command, the source file must be in the same directory as the run-client.py file and the post destination file must be in the same directory as the run-server.py file.
	- Testing was only completed with send windows and receive windows of size 1. The programs may work with other sizes, but are not guaranteed.