import socket, glob, json, datetime, time, os

class DNS_SERVER():
	def __init__(self, ip, server_name, authorative, port=53053):
		"""Create a DNS Server

		Args:
			ip (str): The IP the server should listen to in range from 127.0.0.10 to 127.0.0.100
			port (int): The Server port, default = 53053
			server_name (str): Name of server, should be the same as its root file
			authorative (boolean): Can give authorative answers or not
		"""
		self.PORT = port
		self.IP = ip
		self.NAME = server_name
		self.authorative = authorative
		self.bindSock()
		self.zoneData = self.loadZones()
		self.run()


	def bindSock(self):
		"""Bind socket to IP and Port
		"""
		#SOCK_DGRAM for UDP, SOCK_STREAM for TCP
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((self.IP, self.PORT))
		#print(datetime.datetime.now(), self.NAME, "BINDING SOCKET")
		self.log((self.IP, self.PORT), 0, "BINDING SOCKET")

	def loadZones(self):
		"""Load zone file corresponding to Server name

		Returns:
			dict: zone file as dictonary/JSON
		"""
		zones = {}
		name = self.NAME
		if self.NAME[-1] == ".":
			name = self.NAME[0:-1]
		with open('./zones/%s.zone' % name) as zonefile:
			zones = json.load(zonefile)
		return zones

	def run(self):
		"""Keep server alive until program throws error
		"""
		try:
			self.log((self.IP, self.PORT), 0, "WAITING FOR MSGS")
			#print(datetime.datetime.now(), self.NAME, "WAITING FOR MSGS")
			while 1:
				# Recieve 512 bytes Max as per ietf standard, also recieve address
				data, addr = self.sock.recvfrom(512)
				self.log(addr, json.loads(data.decode('utf-8')), "recv")
				#print(datetime.datetime.now(), self.NAME, "MSG RECEIVED" , data.decode('utf-8'), "from Client", addr)
				response = self.buildResponse(json.loads(data.decode('utf-8')))
				#Send response to sender
				time.sleep(5)
				#print(datetime.datetime.now(), self.NAME, "SENDING MSG", response, "to Client", addr)
				self.log(addr, json.loads(response), "send")
				self.sock.sendto(response.encode('utf-8'), addr)
		except KeyboardInterrupt:
			pass
		finally:
			self.sock.close()

	def buildResponse(self, query):
		"""Generates custom response for client

		Args:
			query (string): the domain the stub asks for

		Returns:
			str: Response as JSON Formatted string
		"""
		# Static things that every response has
		response = {
			"dns.flags.response": 1, 
			"dns.flags.recavail": 0,
			"dns.qry.name": query["dns.qry.name"],
			"dns.qry.type": query["dns.qry.type"],
			"dns.flags.rcode": 0}

		if(self.authorative):
			response.update({"dns.flags.authorative": 1})
		else:
			response.update({"dns.flags.authorative": 0})

		#Count Answers, or rather check if answer or nahw
		try:
			dns_name = query["dns.qry.name"]
			self.zoneData[dns_name]
			response.update({"dns.count.answers": 1, "dns.name": dns_name, "dns.a": self.zoneData[dns_name]["A"], "dns.resp.ttl": self.zoneData[dns_name]["TTL"]})
		except KeyError:
			# We didn't find any answer, so we look for a redirect we can give
			response.update({"dns.count.answers": 0, 
				"dns.flags.authoritative": 0})
			#Suffix matching
			suffix = self.biggestSuffix(query["dns.qry.name"])
			if not response["dns.count.answers"] and suffix:
				response.update({"dns.count_auth_rr": 1, "dns.name": suffix, "dns.a": self.zoneData[suffix]["A"], "dns.resp.ttl": self.zoneData[suffix]["TTL"]})
			else:
				# Check if we are authorative
				if self.authorative:
					#Name error
					response["dns.flags.rcode"] = 3
				else:
					#Cant process query
					response["dns.flags.rcode"] = 2


		return json.dumps(response, indent=4)


	def log(self, addr, data, logtype):
		typeString = ""
		if(logtype == "recv"):
			typeString = "Request received for name " + data["dns.qry.name"] + " from " + str(addr)
		elif(logtype == "send"):
			typeString = "Sending answer " + data["dns.a"] + " for " + data["dns.name"] + " to " + str(addr)
		else:
			typeString = logtype

		logString = str(datetime.datetime.now()) + " | " + self.NAME + " | " + typeString + "\n"
		
		if not os.path.exists('logfiles'):
			os.makedirs('logfiles')
		name = self.NAME
		if self.NAME[-1] == ".":
			name = self.NAME[0:-1]
		try:
		
			with open('logfiles/%s.log' % name, "a") as logfile:
				logfile.write(logString)
				
		except IOError:
			with open('logfiles/%s' % name, "w+") as logfile:
				logfile.write(logString)

	def biggestSuffix(self, domain):
		"""Looks through zones to find the biggest redirect we can give

		Args:
			domain (str): The Domain the Stub asked for

		Returns:
			str: Name of the longest suffix we can answer from domain
		"""
		biggestZone = ""
		for zone in self.zoneData:
			if zone in domain and len(zone) > len(biggestZone):
				biggestZone = zone
		return biggestZone
		