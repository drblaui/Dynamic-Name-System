from multiprocessing import Process
import dnssy, resolve, os

#This probably could've been done prettier, but "what the user doesn't see, can be spaghett-ee"

def createServer(ip, name, auth):
	dnssy.DNS_SERVER(ip, name, auth)

def resolver():
	resolve.RESOLVER()

def window():
	os.system("start python stubby.py")

if __name__ == '__main__':
	ROOT = Process(target=createServer, args=("127.0.0.11", "ROOT", False,))
	fuberlin = Process(target=createServer, args=("127.0.0.19", "fuberlin.", False))
	homework = Process(target=createServer, args=("127.0.0.20", "homework.fuberlin.", True))
	pcpools = Process(target=createServer, args=("127.0.0.23", "pcpools.fuberlin.", True))
	telematik = Process(target=createServer, args=("127.0.0.12", "telematik.", False))
	router = Process(target=createServer, args=("127.0.0.16", "router.telematik.", True))
	switch = Process(target=createServer, args=("127.0.0.13", "switch.telematik.", True))
	resolve = Process(target=resolver)
	stub = Process(target=window)

	ROOT.start()
	fuberlin.start()
	homework.start()
	pcpools.start()
	telematik.start()
	router.start()
	switch.start()
	resolve.start()
	stub.start()
	