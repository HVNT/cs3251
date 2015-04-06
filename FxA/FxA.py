import Queue
import threading
import sys
import socket
# import argparse

# parser = argparse.ArgumentParser(description='Transfer files.')
# parser.add_argument('X', metavar='N', type=int, nargs='+',
#                    help='an integer for the accumulator')
# parser.add_argument('A', dest='accumulate', action='store_const',
#                    const=sum, default=max,
#                    help='sum the integers (default: find the max)')
# parser.add_argument('P', dest='accumulate', action='store_const',
#                    const=sum, default=max,
#                    help='sum the integers (default: find the max)')

# args = parser.parse_args()

MAX_QUEUE_CONNECTIONS = 3

class FxA:
	def __init__(self, X, A, P):
		self.port = X
		self.ip = A
		self.destport = P
		self.iqueue = Queue.Queue()
		self.running = True
		self.server = (X & 1) == 1 	#Checks the parity and determines if server
		self.window = 10
		self.connected = False

	def run(self):
		self.ithread = threading.Thread(target = self.userinput)
		self.ithread.start()
		self.setupSocket(self.port, self.ip, self.destport)
		while self.running:
			uin = self.iqueue.get()
			if(len(uin) > 0 and len(uin.split(' ')) > 0):
				uin = uin.split(' ')
				command = uin[0]
				if(not self.server and command == "connect"):
					self.connect()
				elif(not self.server and command == "get" and len(uin) > 1):
					self.get(uin[1])
				elif(not self.server and command == "post" and len(uin) > 1):
					self.post(uin[1])
				elif(not self.server and command == "disconnect"):
					self.disconnect()
				elif(command == "window" and len(uin) > 1):
					self.window(uin[1])
				elif(command == "terminate"):
					self.terminate()
				else:
					print "Unknown command" 
			if(self.server): 
				self.runserver()

	def setupSocket(self, port, ip, destport):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# self.socket.bind((ip, port))

	def userinput(self):
		i = 0
		uinput = ""
		while self.running and uinput != "terminate":
			try:
				uinput = raw_input(">>>")
				self.iqueue.put(str(uinput))
			except EOFError:
				i += 1


	def connect(self):
		if(self.connected):
			return
		try:
			self.socket.bind((self.ip, self.port))
			print "connecting"
			self.socket.connect((self.ip, self.destport))
			print "connected"
			self.connected = True
		except socket.error, (value,message):
			print "error connecting: " + message
			self.connected = False

	def disconnect(self):
		self.socket.close()
		self.connected = False

	def get(self, F):
		self.socket.send("GET:"+F)
		size = int(self.socket.recv(32)) #receive the number of packets
		frecvd = self.socket.recv(size)
		f = open(F)
		f.write(frecvd)
		
	def post(self, F):
		f = open(F)
		fdata = f.read(frecvd)
		self.socket.send("POST:"+F)

	def runserver(self):
		#self.socket.timeout = 1000
		print "running"
		if(not self.connected):
			self.socket.bind((self.ip, self.port))
			print "listening"
			self.socket.listen(MAX_QUEUE_CONNECTIONS)
			print "accepting"
			(self.socket, addr) = self.socket.accept()
			print "accepted"
		recvd = self.socket.recv(1024)
		print "received:" + recvd
		recvd = recvd.split(':')
		if(len(recvd)>1 and recvd[0] == "GET"):
			filename = recvd[1]
			f = open(filename)
			fdata = f.read 
			print "length: " + len(fdata)
			print "size:" + sys.getsizeof(fdata)
			#send shittt
			self.socket.send(sys.getsizeof(fdata))
			self.socket.send(fdata)

		if(len(recvd)>1 and recvd[0] == "POST"):
			filename = recvd[1]
			f = open(filename)
			fdata = f.read 
			print "length: " + len(fdata)
			print "size:" + sys.getsizeof(fdata)
			#recv shitt

	def terminate(self):
		self.socket.close()
		self.running = False

	def window(self, W):
		self.window = W
		#self.socket.sendWindow = W

def main():

	if(len(sys.argv)!=4):
		print "Unexpected number of arguements (" + str(len(sys.argv)-1) + ")"
		return
	port = int(sys.argv[1])
	ip = sys.argv[2]
	destport = int(sys.argv[3])
	f = FxA(port, ip, destport)
	f.run()
if __name__ == "__main__":
    main()



