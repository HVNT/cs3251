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

class FxA:
	def __init__(self, X, A, P):
		self.port = X
		self.ip = A
		self.destport = P
		self.queue = Queue.Queue()
		self.running = True
		self.server = (X & 1) == 1 	#Checks the parity and determines if server
		self.window = 10
		self.connected = False

	def start(self):
		self.ithread = threading.Thread(target = self.userinput)
		self.ithread.start()

		self.setupSocket(self.port, self.ip, self.destport)
		while self.running:
			uin = self.queue.get()
			if(len(uin) > 0 and len(uin.split(' ')) > 0):
				uin = uin.split(' ')
				command = uin[0]
				if(not self.server and command == "connect"):
					self.connect()
				elif(not self.server and command == "get"):
					self.get(uin[1])
				elif(not self.server and command == "post"):
					self.post(uin[1])
				elif(not self.server and command == "disconnect"):
					self.disconnect()
				elif(command == "window"):
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
		while self.running and uinput != "terminate" and i < 10:
			try:
				uinput = raw_input(">>>")
				self.queue.put(str(uinput))
			except EOFError:
				i += 1

	def connect(self):
		self.socket.listen()

	def disconnect(self):
		self.socket.close()

	def get(self, F):
		self.socket.send("GET:"+F)
		self.socket.rcv()
		
		
	def post(self, F):
		print "implement"

	def runserver(self):
		self.socket.timeout = 1000
		if(self.server and not self.connected):
			self.socket.listen()
			self.socket.accept()
		recvd = self.socket.rcv(1024)
		recvd = recvd.split(':')
		if(len(recvd)>1 and recvd[0] == "GET"):
			filename = recvd[1]
			f = open(filename)
			print "length: " + len(f)
			print "size:" + sys.getsizeof(f)



	def terminate(self):
		self.socket.close()
		self.running = False

	def window(self, W):
		self.window = W
		#self.socket.sendWindow = W

def main():
	port = 5001
	ip = "127.0.0.1"
	destport = 5002
	f = FxA(port, ip, destport)
	f.start()
if __name__ == "__main__":
    main()



