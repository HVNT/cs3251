# cs3251
 
**Authors**

	Benjamin Newcomer
	Wataru Uneo

**Usage**

	rxp required python3, therefore any programs using the rxp module must use python 3.4.3. A python 3.4.3 environment is provided in py3env. To activate the environment, enter "source py3env/bin/activate" on the command line. Then use the command line as your normally would.

	NetEmu requires python 2, so you must execute it in an environment equipped with python 2.x.x. Because NetEmu was provided by the professors, no environments have been provided for running NetEmu.

	Maximum packet size is 1000 bytes

**Known Problems**

	On random runs, NetEmu routes packets from one socket back to the same socket. This results in the sender receiving data packets rather than ACKS and effectively results in the data packets being dropped (in the eyes of the receiver).

