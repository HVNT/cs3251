import queue
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
DEBUG_MODE = False
lock = threading.Lock()
cond = threading.Condition(lock)
blocking = False



class FxA:
	def __init__(self, X, A, P):
		self.port = X
		self.ip = A
		self.destport = P
		self.iqueue = queue.Queue()
		self.running = True
		self.server = (X & 1) == 1 	#Checks the parity and determines if server
		self.W = 10
		self.accepting = False
		self.connected = False

	def run(self):
		self.getuserinput()
		while self.running:
			if(self.running and self.server): 
				self.runserver()

			uinp = False
			if(not blocking and not self.iqueue.empty()):
				uinp = True
				uin = self.iqueue.get()
			if(uinp and len(uin) > 0 and len(uin.split(' ')) > 0):
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
					if(DEBUG_MODE):
						print("Unknown command")

	def setupSocket(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((self.ip, self.port))

	def getuserinput(self):
		self.ithread = threading.Thread(target = self.userinput, args=(self.iqueue,lock))
		self.ithread.daemon = True
		self.ithread.start()

	def startServer(self):
		self.ithread = threading.Thread(target = self.runserver)
		self.ithread.daemon = True
		self.ithread.start()

	def userinput(self, queue, lock):
		i = 0
		uinput = ""
		while self.running and uinput != "terminate":
			try:
				blocking = True
				uinput = input(">>>")
				queue.put(str(uinput))
				blocking = False
			except EOFError:
				i += 1

	def connect(self):
		if(self.connected):
			return
		try:
			self.setupSocket()
			if(DEBUG_MODE):
				print("connecting")
			self.socket.connect((self.ip, self.destport))
			if(DEBUG_MODE):
				print("connected")
			self.connected = True
		except socket.error:
			if(DEBUG_MODE):
				print("error connecting..")
			self.connected = False

	def disconnect(self):
		if(not self.connected):
			if(DEBUG_MODE):
				print("Not connected")
			return
		resp = "CLOSE:DONE"
		self.socket.send(str.encode(resp))
		self.socket.close()
		self.connected = False

	def get(self, F):
		if(not self.connected):
			if(DEBUG_MODE):
				print("Not connected")
			return
		resp = "GET:"+F
		self.socket.send(str.encode(resp))

		recvd = False
		while(not recvd):
			if(DEBUG_MODE):
				print("receiving size..")
			resp = self.socket.recv(32) #receive the size of packets
			resp = bytes.decode(resp)
			if(DEBUG_MODE):
				print("received")
			if(resp.split(':')[0] == "ERR"):
				if(DEBUG_MODE):
					print("File not found on server")
				return
				recvd = True
			elif(resp.split(':')[0] == "SND"):
				try:
					size = int(resp.split(':')[1])
					recvd = True
					resp = "GOT:"+str(size)
					self.socket.send(str.encode(resp))
					if(DEBUG_MODE):
						print("Got size:" + resp.split(':')[1])
				except ValueError:
					resp = "ERR:VALUE_ERROR"
					self.socket.send(str.encode(resp))
					if(DEBUG_MODE):
						print("Did not get a proper size:" + resp.split(':')[1])
			elif(resp.split(':')[0] == "CLOSE"):
				recvd = True
				self.socket.close()
				self.connected = False
				if(DEBUG_MODE):
					print("Server closed")
				return

		if(DEBUG_MODE):
			with lock: 
				print("Size:" + str(size))

		filename = "new " + F

		#Set the file to be empty
		f = open(filename, 'w+')
		f.write("")
		f.close()

		f = open(filename, 'a+b')

		recvd = 0
		size = int(size)
		while(recvd < size):
			if(DEBUG_MODE):
				print("received:" + str(recvd) + " bytes")
			if(size - recvd < 1024):
				temp = self.socket.recv(size-recvd)
			else:
				temp = self.socket.recv(1024)
			recvd+=1024
			#f.write(bytes.decode(temp))
			f.write(temp)
		if(DEBUG_MODE):
			with lock: 
				print("Transfered file successfully")

		f.close()
		
	def post(self, F):
		try:
			f = open(F, 'rb')
		except IOError:
			if(DEBUG_MODE):
				print("File error..")
			return

		a = f.read()

		if(DEBUG_MODE):
			print("Sending size..")
		resp = "POST:" + str(len(a)) + ":" + F
		self.socket.send(str.encode(resp))
		
		crecvd = False
		while(not crecvd):
			try:
				resp = self.socket.recv(32)
				resp = bytes.decode(resp).split(':')[0]
				if(resp == "GOT"):
					crecvd = True
				else:
					crecvd = False
			except ValueError:
				crecvd = False

		sent = 0
		while(sent < len(a)):
			if(len(a) - sent < 1024):
				self.socket.send(a[sent:len(a)])
			else:
				self.socket.send(a[sent:sent+1024])
			sent+=1024
		if(DEBUG_MODE):
			print("Transfered file successfully")
		f.close()

	def runserver(self):
		#self.socket.timeout = 1000
		if(DEBUG_MODE):
			print("running" + str(self.connected))
		if(not self.connected):
			if(not self.accepting):
				self.setupSocket()
				if(DEBUG_MODE):
					print("listening")
				self.socket.listen(MAX_QUEUE_CONNECTIONS)
				if(DEBUG_MODE):
					print("accepting")
				self.accepting = True
			try:
				self.socket.settimeout(1.0)
				(self.socket, addr) = self.socket.accept()
			except socket.timeout:
				return	
			self.accepting = False
			if(DEBUG_MODE):
				print("accepted")
			self.connected = True

		if(DEBUG_MODE):
			print("receiving..")
		try:
			self.socket.settimeout(1.0)
			recvd = self.socket.recv(1024)
		except socket.timeout:
			return	
		recvd = bytes.decode(recvd)

		if(DEBUG_MODE):
			print("received:" + recvd)
		recvd = recvd.split(':')
		if(len(recvd)>1 and recvd[0] == "GET"):
			filename = recvd[1]
			
			try:
				f = open(filename, 'rb')
			except IOError:
				if(DEBUG_MODE):
					print("File error..")
				resp = "ERR:File error"
				self.socket.send(str.encode(resp))
				return

			fdata = f.read()
			#a = str.encode(fdata)
			a = fdata

			crecvd = False
			while(not crecvd):
				if(DEBUG_MODE):
					print("Sending size..")
				resp = "SND:" + str(len(a))
				self.socket.send(str.encode(resp))
				try:
					resp = self.socket.recv(32)
					resp = bytes.decode(resp).split(':')[0]
					if(resp == "GOT"):
						crecvd = True
					else:
						crecvd = False
				except ValueError:
					crecvd = False

			sent = 0
			while(sent < len(a)):
				if(len(a) - sent < 1024):
					self.socket.send(a[sent:len(a)])
				else:
					self.socket.send(a[sent:sent+1024])
				sent+=1024
			if(DEBUG_MODE):
				print("Transfered file successfully")
			f.close()

		if(len(recvd)>1 and recvd[0] == "POST"):
			try:
				size = int(recvd[1])
				filename = recvd[2]

				resp = "GOT:"+str(size)
				self.socket.send(str.encode(resp))
				if(DEBUG_MODE):
					print("Got size:" + size)
			except ValueError:
				resp = "ERR:VALUE_ERROR"
				self.socket.send(str.encode(resp))
				if(DEBUG_MODE):
					print("Did not get a proper size:" + resp.split(':')[1])
				return

			if(DEBUG_MODE):
				print("Size:" + str(size))

			filename = "new " + filename

			#Set the file to be empty
			f = open(filename, 'w+')
			f.write("")
			f.close()

			f = open(filename, 'a+b')

			brecvd = 0
			size = int(size)
			while(brecvd < size):
				if(DEBUG_MODE):
					print("received:" + str(brecvd) + " bytes")
				if(size - brecvd < 1024):
					temp = self.socket.recv(size-brecvd)
				else:
					temp = self.socket.recv(1024)
				brecvd+=1024
				#f.write(bytes.decode(temp))
				f.write(temp)
			if(DEBUG_MODE):
				with lock: 
					print("Transfered file successfully")

			f.close()

		if(len(recvd)>1 and recvd[0] == "CLOSE"):
			self.socket.close()
			self.connected = False


	def terminate(self):
		try:
			resp = str.encode("CLOSE:DONE")
			self.socket.send(resp)
		except:
			if(DEBUG_MODE):
				print("Send \"CLOSE\" timed out")
		finally:
			self.socket.close()
		self.running = False

	def window(self, W):
		self.W = W
		#self.socket.sendWindow = W

def main():

	if(len(sys.argv)!=4):
		print("Unexpected number of arguements (" + str(len(sys.argv)-1) + ")")
		return
	port = int(sys.argv[1])
	ip = sys.argv[2]
	destport = int(sys.argv[3])
	f = FxA(port, ip, destport)
	f.run()
if __name__ == "__main__":
    main()



