import Queue
import threading
import sys
import socket
from array import array
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
reload(sys)
sys.setdefaultencoding('utf-8')

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
		self.ithread.daemon = True
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

	def setupSocket(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind((self.ip, self.port))


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
			self.setupSocket()
			print "connecting"
			self.socket.connect((self.ip, self.destport))
			print "connected"
			self.connected = True
		except socket.error, (value,message):
			print "error connecting: " + message
			self.connected = False

	def disconnect(self):
		self.socket.send("CLOSE:DONE")
		self.socket.close()
		self.connected = False

	def get(self, F):
		self.socket.send("GET:"+F)
		resp = self.socket.recv(32) #receive the number of packets
		if(resp.split(':')[0] == "ERR"):
			print "File not found on server"
			return
		elif(resp.split(':')[0] == "SND"):
			size = int(resp.split(':')[1])

		print "Size:" + str(size)

		filename = "new " + F

		#Set the file to be empty
		f = open(filename, 'w+')
		f.write("")
		f.close()

		f = open(filename, 'a+')

		recvd = 0
		size = int(size)
		while(recvd < size):
			if(size - recvd < 1024):
				temp = self.socket.recv(size-recvd)
			else:
				temp = self.socket.recv(1024)
			recvd+=1024
			f.write(temp)

		f.close()
		
	def post(self, F):
		self.socket.send("POST:"+F)
		resp = self.socket.recv(1024)

		try:
			f = open(F)
		except IOError:
			print "File error.." 
			self.socket.send("ERR:File error")
			return

		fdata = f.read()
		a = array("B", fdata)

		self.socket.send("SND:" + str(len(a)))
		sent = 0
		while(sent < len(a)):
			if(len(a) - sent < 1024):
				self.socket.send(a[sent:len(a)])
			else:
				self.socket.send(a[sent:sent+1024])
			sent+=1024
		f.close()

	def runserver(self):
		#self.socket.timeout = 1000
		print "running" + str(self.connected)
		if(not self.connected):
			self.setupSocket()
			print "listening"
			self.socket.listen(MAX_QUEUE_CONNECTIONS)
			print "accepting"
			(self.socket, addr) = self.socket.accept()
			print "accepted"
			self.connected = True
		recvd = self.socket.recv(1024)
		print "received:" + recvd
		recvd = recvd.split(':')
		if(len(recvd)>1 and recvd[0] == "GET"):
			filename = recvd[1]
			
			try:
				f = open(filename)
			except IOError:
				print "File error.." 
				self.socket.send("ERR:File error")
				return

			fdata = f.read()
			a = array("B", fdata)

			self.socket.send("SND:" + str(len(a)))
			sent = 0
			while(sent < len(a)):
				if(len(a) - sent < 1024):
					self.socket.send(a[sent:len(a)])
				else:
					self.socket.send(a[sent:sent+1024])
				sent+=1024
			f.close()

		if(len(recvd)>1 and recvd[0] == "POST"):
			filename = recvd[1]
			f = open(filename)
			fdata = f.read 
			print "length: " + len(fdata)
			print "size:" + sys.getsizeof(fdata)
			#recv shitt
			f.close()

		if(len(recvd)>1 and recvd[0] == "CLOSE"):
			self.socket.close()
			self.connected = False

	def terminate(self):
		self.socket.send("CLOSE:DONE")
		self.socket.close()
		self.running = False

	def window(self, W):
		self.window = W
		#self.socket.sendWindow = W

def main():
	reload(sys)
	sys.setdefaultencoding('utf-8')

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



