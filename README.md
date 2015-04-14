# cs3251
 
**Authors**

	Benjamin Newcomer
	Wataru Uneo

**Usage**

	rxp required python3, therefore any programs using the rxp module must use python 3.4.3. A python 3.4.3 environment is provided in py3env. To activate the environment, enter "source py3env/bin/activate" on the command line. Then use the command line as your normally would.

	NetEmu requires python 2, so you must execute it in an environment equipped with python 2.x.x. Because NetEmu was provided by the professors, no environments have been provided for running NetEmu.

	Maximum packet size is 1000 bytes

**Known Problems**

	On certain runs, NetEmu forwards packets from one socket back to the same socket. NetEmu also continuously sends repeat packets until the client or server times out, even though the duplicate packets option is not set.

