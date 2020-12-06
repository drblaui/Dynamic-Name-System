import socket, json, datetime, time

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
		self.run()

	def loadOrCreateCache(self):
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
		print(datetime.datetime.now(), "RESOLVER", "BINDING SOCKET")

	def run(self):
		"""Keep server alive until program throws error
		"""
		try:
			print(datetime.datetime.now(), "RESOLVER", "WAITING FOR MSGS")
			while 1:
				# Recieve 512 bytes Max as per ietf standard, also recieve address
				data, addr = self.sock.recvfrom(512)
				print(datetime.datetime.now(), "RESOLVER", "MSG RECEIVED" , data.decode('utf-8'), "from Client", addr)
				response = self.getResponse(data, self.root)
				print(datetime.datetime.now(), "RESOLVER", "SENDING MSG", response, "to Client", addr)
				#Send response to sender
				self.sock.sendto(response.encode('utf-8'), addr)
		except KeyboardInterrupt:
			pass
		finally:
			self.sock.close()

	def send(self, message, server):
		time.sleep(5)
		print(datetime.datetime.now(), "RESOLVER", "SENDING MSG", message.decode('utf-8'), "to Server", server)
		self.sock.sendto(message, server)
		
	def listen(self):
		data, addr = self.sock.recvfrom(512)
		print(datetime.datetime.now(), "RESOLVER", "MSG RECEIVED", data.decode('utf-8'), "from Server", addr)

		return [data, addr]

	def overwriteCache(self, newContent):
		with open("cache.json", "w") as cache:
			cache.write(json.dumps(newContent, indent=4))

	def checkCache(self, domain):
		domain = self.biggestSuffix(domain)
		if domain == "":
			return None
		if self.cache[domain]["dieTime"] > int(time.time()):
			return (domain, self.cache[domain]["A"])
		elif self.cache[domain]["dieTime"] == int(time.time()):
			temp = self.cache[domain]
			self.cache.pop(domain)
			self.overwriteCache(self.cache)
			return (domain, temp["A"])
		elif self.cache[domain]["dieTime"] < int(time.time()):
			self.cache.pop(domain)
			self.overwriteCache(self.cache)
			return None
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

	def generateSuffixes(self, domain):
		domains = domain.split(".")
		res = []
		
		for i in range(1, len(domains) + 1):
			res.append(".".join(domains[-i:-1]) + ".")

	def getResponse(self, data, server):
		#TODO Cache
		data = json.loads(data.decode('utf-8'))
		cacheCheck = self.checkCache(data["dns.qry.name"])
		if(cacheCheck is not None and cacheCheck[0] == data["dns.qry.name"]):
			print("Hell yeah")
			return cacheCheck[1]
		elif(cacheCheck is not None): 
			server = (cacheCheck[1], self.PORT)
		self.send(json.dumps(data,indent=4).encode('utf-8'), server)
		data, addr = self.listen()
		data = json.loads(data.decode('utf-8'))
		if data["dns.flags.rcode"] == 3 or data["dns.flags.rcode"] == 2:
			return "Error"
		try:
			# we have a reroute
			data["dns.count_auth_rr"]
			exampleData = json.dumps({"dns.flags.response": 0, "dns.flags.recdesired": 1, "dns.qry.name": data["dns.qry.name"], "dns.qry.type": data["dns.qry.type"]}, indent=4)
			newServer = {"A": data["dns.a"], "TTL": data["dns.resp.ttl"], "dieTime": int(time.time()) + data["dns.resp.ttl"]}
			self.cache[data["dns.name"]] = newServer
			self.overwriteCache(self.cache)
			return self.getResponse(exampleData.encode('utf-8'), (data["dns.a"], self.PORT))
		except KeyError:
			newServer = {"A": data["dns.a"], "TTL": data["dns.resp.ttl"], "dieTime": int(time.time()) + data["dns.resp.ttl"]}
			self.cache[data["dns.name"]] = newServer
			self.overwriteCache(self.cache)
			return data["dns.a"]
	


# Create Resolver
Resolver = RESOLVER()