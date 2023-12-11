import socket, json, datetime, time, os

class RESOLVER():
	def __init__(self, ip='127.0.0.10', port=53053):
		"""Create a Resolver

		Args:
			ip (str): The IP the server should listen to in range from 127.0.0.10 to 127.0.0.100
			port (int): The Server port, default = 53053
		"""
		self.PORT = port
		self.IP = ip
		self.root = ("127.0.0.11", self.PORT)
		self.bindSock()
		self.loadOrCreateCache()
		self.sent = self.getMessages("sent")
		self.recv = self.getMessages("recv")
		self.sleepSec = 5
		self.run()


	def getMessages(self, message):
		name = "resolver"
		with open("messages.json", "r") as jsonfile:
			data = json.load(jsonfile)
			return data[name][message]

	def updateMessages(self, message):
		name = "resolver"
		with open("messages.json", "r+") as jsonfile:
			data = json.load(jsonfile)
			data[name][message] += 1
			jsonfile.seek(0)
			json.dump(data, jsonfile, indent=4)
			jsonfile.truncate()

	def loadOrCreateCache(self):
		"""Checks if we already have a cache and loads it into memory
		"""
		try:
			with open('cache.json') as cache:
				self.cache = json.load(cache)
		except IOError:
			self.cache = {}

	def bindSock(self):
		"""Bind socket to IP and Port
		"""
		#SOCK_DGRAM for UDP, SOCK_STREAM for TCP
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((self.IP, self.PORT))
		self.log((self.IP, self.PORT), 0, "BINDING SOCKET")

	def run(self):
		"""Keep server alive
		"""
		self.log((self.IP, self.PORT), 0, "WAITING FOR MSGS")
		while 1:
			# Receive 512 bytes Max as per IETF standard, also receive address
			data, addr = self.sock.recvfrom(512)
			self.log(addr, json.loads(data.decode('utf-8')), "recv")
			self.dump(addr, data.decode('utf-8'), "recv")
			response = self.getResponse(data, self.root)

			# Check if answer is error or IP, because the stub doesn't need anything except why it's query has failed or the right answer
			if(response.startswith("Error") or response.startswith('127.')):
				self.log(addr, 0, response)
				self.dump(addr, 0, response)
			else:
				self.log(addr, json.loads(response), "send")
				self.dump(addr, response, "send")

			#Send response to sender
			time.sleep(self.sleepSec)

			#If sender timed out
			try:
				self.sock.sendto(response.encode('utf-8'), addr)
			except ConnectionError:
				continue

	def send(self, message, server):
		"""Sends a message to a server

		Args:
			message (str): the encoded message
			server (tuple): server information
		"""
		time.sleep(self.sleepSec)
		self.log(server, json.loads(message.decode('utf-8')), "ask")
		self.sock.sendto(message, server)
		
	def listen(self):
		"""Listens for incoming messages

		Returns:
			list: returns list containing encoded datastring and sender address
		"""
		data, addr = self.sock.recvfrom(512)
		self.log(addr, json.loads(data.decode('utf-8')), "recv")

		return [data, addr]

	def overwriteCache(self, newContent):
		"""Because of lazyness we don't update the cache, but rather delete everything inside and write the new content into it

		Args:
			newContent (dict): new cache content
		"""
		with open("cache.json", "w") as cache:
			cache.write(json.dumps(newContent, indent=4))

	def checkCache(self, domain):
		"""Searches Cache for biggest suffix possible

		Args:
			domain (str): string of the request

		Returns:
			tuple: contains biggest Suffix and A record or is None, if cache doesn't have request
		"""
		#Suffix matching
		domain = self.biggestSuffix(domain)

		# We don't have a suffix in our cache
		if domain == "":
			return None
		
		# Entry still has time to live
		if self.cache[domain]["dieTime"] > int(time.time()):
			return (domain, self.cache[domain]["A"])

		# Entry would be old about right now (edge case, let's say it's okay to return the entry)
		#Deletes cache entry and returns the deleted one
		elif self.cache[domain]["dieTime"] == int(time.time()):
			temp = self.cache[domain]
			self.cache.pop(domain)
			self.overwriteCache(self.cache)
			return (domain, temp["A"])

		# The entry we found is too old. Deletes entry and returns
		elif self.cache[domain]["dieTime"] < int(time.time()):
			self.cache.pop(domain)
			self.overwriteCache(self.cache)
			return None
		
		# If this ever happens, something probably went wrong
		else: 
			return None
	
	def biggestSuffix(self, domain):
		"""Looks through zones to find the biggest redirect we can give

		Args:
			domain (str): The Domain the Stub asked for

		Returns:
			str: Name of the longest suffix we can answer from domain
		"""
		biggestCache = ""
		for cache in self.cache:
			if cache in domain and len(cache) > len(biggestCache):
				biggestCache = cache
		return biggestCache

	def getResponse(self, data, server):
		"""Recursively queries servers until it gets an error or a response

		Args:
			data (str): encoded json data string
			server (tuple): server information

		Returns:
			str: either returns errorstring or A record
		"""
		data = json.loads(data.decode('utf-8'))

		# Check cache. Immediately return the result if we have it cached. Or query already cached subserver
		cacheCheck = self.checkCache(data["dns.qry.name"])
		if(cacheCheck is not None and cacheCheck[0] == data["dns.qry.name"]):
			return cacheCheck[1]
		elif(cacheCheck is not None): 
			server = (cacheCheck[1], self.PORT)

		# Ask cached server or root
		try:
			self.send(json.dumps(data,indent=4).encode('utf-8'), server)
		except ConnectionError:
			return "Error your requested domain does not exist"
		data, addr = self.listen()
		data = json.loads(data.decode('utf-8'))

		# Cache result
		if "dns.ns" in data and "dns.resp.ttl" in data:
			dieTime = int(time.time() + data["dns.resp.ttl"])
			newServer = {"A": data["dns.a"], "TTL": data["dns.resp.ttl"], "dieTime": dieTime, "dieTimeHR":  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(dieTime))}
			self.cache[data["dns.ns"]] = newServer
			self.overwriteCache(self.cache)

	
		# Could also be done with "dns.count_auth_rr" in data, but I forgot about basic python syntax
		try:
			# we have a reroute
			data["dns.count_auth_rr"]
			#static data for requests
			exampleData = json.dumps({"dns.flags.response": 0, "dns.flags.recdesired": 1, "dns.qry.name": data["dns.qry.name"], "dns.qry.type": data["dns.qry.type"]}, indent=4)
		
			# Let's just say every server has the same port
			return self.getResponse(exampleData.encode('utf-8'), (data["dns.a"], self.PORT))
		except KeyError:
			# We got an answer or an error
			
			# Error handling
			if data["dns.flags.rcode"] == 2:
				return "Error " + str(data["dns.flags.rcode"]) + " Server failure - The name server was unable to process this query due to a problem with the name server"
			elif data["dns.flags.rcode"] == 3:
				return "Error " + str(data["dns.flags.rcode"]) + " Name Error - The server seems to understand your query, but refuses to answer it or it doesn't have any entries for your query"
			else:
				# Actual result
				return data["dns.a"]

	def log(self, addr, data, logtype):
		"""Look into dnssy.py for explanation
		"""
		typeString = ""
		if(logtype == "recv"):
			self.recv += 1
			self.updateMessages("recv")
			typeString = "Request received for name " + data["dns.qry.name"] + " from " + str(addr) + " [RECEIVED MESSAGE #" + str(self.sent) + "]"
		elif(logtype == "send"):
			self.sent += 1
			self.updateMessages("sent")
			typeString = "Sending answer " + data["dns.a"] + " for " + data["dns.ns"] + " to " + str(addr) + " [SENT MESSAGE #" + str(self.sent) + "]"
		elif(logtype == "ask"):
			self.sent += 1
			self.updateMessages("sent")
			typeString = "Sending request for " + data["dns.qry.name"]  + " to " + str(addr) + " [SENT MESSAGE #" + str(self.sent) + "]"
		elif(logtype == "error"):
			self.sent += 1
			self.updateMessages("sent")
			typeString = "Sending error " + str(data["dns.flags.rcode"]) + " to " + str(addr) + " [SENT MESSAGE #" + str(self.sent) + "]"
		else:
			self.sent += 1
			self.updateMessages("sent")
			typeString = "Sending " + logtype + " as answer to " + str(addr) + " [SENT MESSAGE #" + str(self.sent) + "]"

		logString = str(datetime.datetime.now()) + " | RESOLVER | " + typeString + "\n"
		
		if not os.path.exists('logfiles'):
			os.makedirs('logfiles')
		name = "resolver"
		try:
		
			with open('logfiles/%s.log' % name, "a") as logfile:
				logfile.write(logString)
				
		except IOError:
			with open('logfiles/%s' % name, "w+") as logfile:
				logfile.write(logString)
		
	def dump(self, addr, data, dumptype):
		"""refer to dnssy.py -> self.log()
		"""
		typeString = ""
		if(dumptype == "recv"):
			typeString = "RECEIVED MSG " + data + " from " + str(addr)
		elif(dumptype == "send"):
			typeString = "SENDING MSG " + data + " to " + str(addr)
		else:
			typeString = "SENDING MSG " + dumptype + " to " + str(addr)

		dumpString = str(datetime.datetime.now()) + " | RESOLVER | " + typeString + "\n \n"
		
		if not os.path.exists('dumps'):
			os.makedirs('dumps')
		name = "resolver"
		try:
		
			with open('dumps/%s.dump' % name, "a") as dumpfile:
				dumpfile.write(dumpString)
				
		except IOError:
			with open('dumps/%s' % name, "w+") as dumpfile:
				dumpfile.write(dumpString)