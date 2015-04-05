import Queue
import threading
import sys, argparse

parser = argparse.ArgumentParser(description='Transfer files.')
parser.add_argument('X', metavar='N', type=int, nargs='+',
                   help='an integer for the accumulator')
parser.add_argument('A', dest='accumulate', action='store_const',
                   const=sum, default=max,
                   help='sum the integers (default: find the max)')
parser.add_argument('P', dest='accumulate', action='store_const',
                   const=sum, default=max,
                   help='sum the integers (default: find the max)')

args = parser.parse_args()


class FxA:
	def __init__(self, X, A, P):
		self.X = X
		self.A = A
		self.P = P
		self.queue = Queue.Queue()
		self.running = True

		self.ithread = threading.Thread(target = self.userinput)
		ithread.start()
	def userinput(self):
		while self.running:
			uinput = input(">>>")
			self.queue.put(str(uinput))
