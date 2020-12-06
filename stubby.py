import socket, datetime, json, time

#TODO: dns.name does not exist
class STUB:
	def __init__(self):
		"""Create a stub (which in this case rather acts as a iterative resolver)
		"""
		#DGRAM for UDP
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#Querys that take longer than 10 seconds to get a answer will be ignored
		self.sock.settimeout(60)
		self.run()


	def run(self):
		"""Keep socket alive until user types \q
		"""
		print("Hi! I'm stubby, your low level Stub, what whould you like to send?")
		print("DNS Query for a Query or /q to stop the program \n Query Skeleton: Domain.Name. @IP -p PORT (if port not provided, we will use 53053) \n Example Query: switch.telematik. @127.0.0.10 -p 53\n")
		while 1:
			request = input("Query: ").replace(" ", "")
			if(request == "/q"):
				print("Stopping...")
				break
			#Spilt domain.name.@IP-p
			domain = request.split("@")[0]
			try:
				ip, port = request.split("@")[1].split("-p")
				port = int(port)
			except ValueError:
				#If user didnt enter port
				ip = request.split("@")[1]
				port = 53053

			#Connect to server
			self.connect(ip, port)
			query = self.buildQuery(domain, 1, 1)
			self.send(query, ip, port)
			self.listen()
		self.sock.close()


	def buildQuery(self, domain, recDesired, qryType):
		"""builds the query as JSON formatted string, to encode and send to server

		Args:
			domain (str): Domain we are asking for
			recDesired (int): Probably always 0
			qryType (int): Probably always 1, because it was like that in the Telematik tutorial

		Returns:
			str: JSON Query
		"""
		return json.dumps({"dns.flags.response": 0, "dns.flags.recdesired": recDesired, "dns.qry.name": domain, "dns.qry.type": qryType}, indent=4)

	def connect(self, ip, port):
		"""Creates uplink to server

		Args:
			ip (str): Server IP 
			port (int): Server Port
		"""
		print("Connecting to %s:%s ..." % (ip,port))
		self.sock.connect((ip, port))
		print("Connected to %s:%s" % (ip,port))

	def send(self, data, ip, port):
		"""send data to server

		Args:
			data (str): Formatted JSON String
			ip (str): Server IP
			port (int): Server Port
		"""
		time.sleep(5)
		print("Asking %s:%s for %s ..." %(ip,port,data))
		#Don't forget to encode!
		self.sock.send(data.encode('utf-8'))
		print("Request sent!")

	def listen(self):
		"""Wait for resopnse
		"""
		print("Listening for Server response")
		try:
			data, addr = self.sock.recvfrom(512)
			print("Got response %s from %s" % (data.decode('utf-8'), addr))
		except socket.timeout:
			print("Timed out while trying to get a server response. Maybe your query was wrong?")


stubby = STUB()