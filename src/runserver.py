import sys
from lib import rxp
from lib import fxa

def main():
	if(len(sys.argv)!=4):
		print("Unexpected number of arguements (" + str(len(sys.argv)-1) + ")")
		return
	port = int(sys.argv[1])
	ip = sys.argv[2]
	destport = int(sys.argv[3])
	socket = rxp.Socket()
	f = fxa.FxA(socket, port, ip, destport)
	f.run()

if __name__ == "__main__":
    main()