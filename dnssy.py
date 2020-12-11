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
		self.sent = 0
		self.recv = 0
		self.sleepSec = 5
		self.run()


	def bindSock(self):
		"""Bind socket to IP and Port
		"""
		#SOCK_DGRAM for UDP, SOCK_STREAM for TCP
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((self.IP, self.PORT))
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
		"""Keep server
		"""
		self.log((self.IP, self.PORT), 0, "WAITING FOR MSGS")
		while 1:
			# Recieve 512 bytes Max as per ietf standard, also recieve address
			data, addr = self.sock.recvfrom(512)
			self.log(addr, json.loads(data.decode('utf-8')), "recv")
			self.dump(addr, data.decode('utf-8'), "recv")
			response = self.buildResponse(json.loads(data.decode('utf-8')))
			#Send response to sender after n seconds
			time.sleep(self.sleepSec)
				
			#Check for error for logging purposes
			if(json.loads(response)["dns.flags.rcode"] != 0):
				self.log(addr, json.loads(response), "error")
			else:
				self.log(addr, json.loads(response), "send")
				
			#Send answer
			self.dump(addr, response, "send")
			self.sock.sendto(response.encode('utf-8'), addr)
		

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
			#This triggers if the server is the parent of the target request
			dns_name = query["dns.qry.name"]
			self.zoneData[dns_name]
			response.update({"dns.count.answers": 1, "dns.ns": dns_name, "dns.a": self.zoneData[dns_name]["A"], "dns.resp.ttl": self.zoneData[dns_name]["TTL"]})

		except KeyError:
			# We didn't find any answer, so we look for a redirect we can give
			response.update({"dns.count.answers": 0})

			#Suffix matching
			suffix = self.biggestSuffix(query["dns.qry.name"])

			# Make sure we really don't have any answers, but we have a suffix, return said suffix
			if not response["dns.count.answers"] and suffix:
				response.update({"dns.count_auth_rr": 1, "dns.ns": suffix, "dns.a": self.zoneData[suffix]["A"], "dns.resp.ttl": self.zoneData[suffix]["TTL"]})
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
		"""Write to logfile

		Args:
			addr (tuple): Information about the target server
			data (dict): Dictonary with data
			logtype (str): describes what kinda log we have
		"""

		typeString = ""
		#else if else if else if else if
		if(logtype == "recv"):
			typeString = "Request received for name " + data["dns.qry.name"] + " from " + str(addr)
		elif(logtype == "send"):
			typeString = "Sending answer " + data["dns.a"] + " for " + data["dns.ns"] + " to " + str(addr)
		elif(logtype == "error"):
			typeString = "Sending error " + str(data["dns.flags.rcode"]) + " to " + str(addr)
		else:
			typeString = logtype

		logString = str(datetime.datetime.now()) + " | " + self.NAME + " | " + typeString + "\n"
		
		# Make sure we have a logfiles folder
		if not os.path.exists('logfiles'):
			os.makedirs('logfiles')

		#Make sure we have a NAME.log file and write to it
		name = self.NAME
		if self.NAME[-1] == ".":
			name = self.NAME[0:-1]
		try:
			with open('logfiles/%s.log' % name, "a") as logfile:
				logfile.write(logString)
		except IOError:
			with open('logfiles/%s' % name, "w+") as logfile:
				logfile.write(logString)

	def dump(self, addr, data, dumptype):
		"""Basically the log function with extra steps

		Args:
			addr (tuple): Information about the target server
			data (dict): the transferred data
			dumptype (str): Description about what type of dump we do
		"""

		typeString = ""
		# Dump only captures transferred packets, and it counts how many querys the current instance processed!
		if(dumptype == "recv"):
			typeString = "RECIEVED MSG NR(" + str(self.sent) + ")" + data + " from " + str(addr)
			self.recv += 1
		elif(dumptype == "send"):
			self.sent += 1
			typeString = "SENDING MSG NR(" + str(self.sent) + ")" + data + " to " + str(addr)
		else:
			typeString = dumptype

		dumpString = str(datetime.datetime.now()) + " | " + self.NAME + " | " + typeString + "\n"
		
		# Same as log. Make sure dumps and SERVER.dump exists and write into it
		if not os.path.exists('dumps'):
			os.makedirs('dumps')
			
		name = self.NAME
		if self.NAME[-1] == ".":
			name = self.NAME[0:-1]
		try:
		
			with open('dumps/%s.dump' % name, "a") as dumpfile:
				dumpfile.write(dumpString)
				
		except IOError:
			with open('dumps/%s' % name, "w+") as dumpfile:
				dumpfile.write(dumpString)

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
		