import socket, datetime, json, time

#if query empty
class STUB:
	def __init__(self):
		"""Create a stub (which in this case rather acts as a iterative resolver)
		"""
		#DGRAM for UDP
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#Queries that take longer than 60 seconds to get a answer will be ignored
		self.sock.settimeout(60)
		self.run()

	def help(self):
		self.say("To perform a DNS query, you just gotta give me a name and I will ask my friend the resolver for it!", False)
		self.say("If you wan't to specify a server IP or a Server Port, you can do so by using @IP and/or -p PORT.", False)
		self.say("If you wan't me to be quiet and stop me, just type '/q'", False)
		self.say("If you wan't me to execute a test against every milestone, type '/test'", False)
		self.say("If you wan't me to repeat this, just type '/help'", False)
		self.say("If you wan't me to give you an example you can try out, just type '/example'", False)

	def test(self):
		self.say("Oh, you wan't me to show what I got, huh?")
		self.say("Alright, let's test milestone for milestone, shall we?")
		self.say("INITIATING TEST SEQUENCE FOR MILESTONE (A)")
		self.say("I will now first ask 'switch.telematik.' for it's webserver, after that I will ask 'pcpools.fuberlin.' for their HannahMontanaOS System, so you'll se a success and an error")
		self.say("Feel free to look into the .log and .dump files of the Servers!")
		ip = '127.0.0.13'
		port = 53053
		domain = "www.switch.telematik."
		self.connect(ip, port)
		query = self.buildQuery(domain, 1, 1)
		self.send(query, ip, port)
		self.listen()
		self.say("If you now look into dns.a, you'll se we got 127.0.0.14. THAT'S ACTUALLY WHAT WE WERE LOOKING FOR, YAY!")
		ip = "127.0.0.23"
		domain = "hannahmontana.pcpools.fuberlin."
		self.connect(ip, port)
		query = self.buildQuery(domain, 1, 1)
		self.send(query, ip, port)
		self.listen()
		self.say("Look into dns.flags.rcode you'll see, we have an rcode from 3. So the server understood what our query was, but just refused to give us any information. How rude!")
		self.say("Well at least, we know we can ask authoritative Servers directly")
		self.say("By the way: did you know you can ask them too? Just ask me 'request @IP -p PORT' with what you're looking for!")
		self.say("Let's move on, shall we?")
		self.say("INITIATING TEST SEQUENCE FOR MILESTONE (B)")
		self.say("I will now ask my pal the recursive Resolver for 'news.router.telematik' and 'medium.homework.fuberlin' so you'll have another example how we get answers and receivers here")
		self.say("As always you can just look into the log and dump files!")
		self.say("Beware this could take a while :(")
		ip = "127.0.0.10"
		domain = "news.router.telematik."
		self.connect(ip, port)
		query = self.buildQuery(domain, 1, 1)
		self.send(query, ip, port)
		self.listen()
		domain = "medium.homework.fuberlin."
		self.connect(ip, port)
		query = self.buildQuery(domain, 1, 1)
		self.send(query, ip, port)
		self.listen()
		self.say("Looks nice right? But it takes sooooo long. Maybe the server cached it?")
		self.say("INITIATING TEST SEQUENCE FOR MILESTONE (C)")
		self.say("Let's ask for the same two requests again. You'll see, we get an answer way faster than before!")
		ip = "127.0.0.10"
		domain = "news.router.telematik."
		self.connect(ip, port)
		query = self.buildQuery(domain, 1, 1)
		self.send(query, ip, port)
		self.listen()
		domain = "medium.homework.fuberlin."
		self.connect(ip, port)
		query = self.buildQuery(domain, 1, 1)
		self.send(query, ip, port)
		self.listen()
		self.say("See how much faster that was? Caching works!")
		self.say("This concludes me showing you what I got. Try me for yourself now!")

	def run(self):
		"""Keep socket alive until user types /q
		"""
		self.say("Hello there! I'm Stubby, your little chatty friendly guide for today. If you have any problems, just ask me! :)", False)
		self.help()
		while 1:
			request = input("Query: ").replace(" ", "")
			if not request:
				self.say("Hey! Maybe try with an input next time?", False)
				continue
			if(request == "/q"):
				self.say("Until next time!", False)
				break
			if request == "/help":
				self.help()
				continue
			if request == "/test":
				self.test()
				continue
			if request == "/example":
				self.say("Maybe try asking for 'www.switch.telematik.'?", False)
				continue
			#Spilt domain.name.@IP-p
			if "@" not in request and "-p" not in request:
				domain = request
				ip = "127.0.0.10"
				port = 53053
			elif "@" in request and "-p" not in request:
				domain, ip = request.split("@")
				port = 53053
			else:
				domain, ip = request.split("@")
				ip, port = ip.split("-p")
				port = int(port)
			
			if not domain.endswith('.'):
				domain = domain + '.'

			#Connect to server
			self.connect(ip, port)
			query = self.buildQuery(domain, 1, 1)
			self.send(query, ip, port)
			self.listen()

	def say(self, message, delay=True):
		print()
		if delay:
			time.sleep(2.5)
		print("Stubby:", message)

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
		self.say("Connecting to" + str((ip, port)), False)
		self.sock.connect((ip, port))
		self.say("Successfully connected to %s:%s" % (ip,port), False)

	def send(self, data, ip, port):
		"""send data to server

		Args:
			data (str): Formatted JSON String
			ip (str): Server IP
			port (int): Server Port
		"""
		time.sleep(5)
		self.say("I'm asking %s:%s for %s" %(ip,port,data), False)
		#Don't forget to encode!
		self.sock.send(data.encode('utf-8'))
		self.say("I've successfully transmitted your data!", False)

	def listen(self):
		"""Wait for response
		"""
		self.say("Let's wait for the response!", False)
		try:
			data, addr = self.sock.recvfrom(512)
			if(data.decode('utf-8').startswith("Error")):
				self.say("Oh no! Got %s from as a result from %s" % (data.decode('utf-8'), addr), False)
			else:
				self.say("%s told me you're looking for %s" % (addr, data.decode('utf-8')), False)
		except socket.timeout:
			self.say("Timed out while trying to get a server response. Maybe your query was wrong?", False)


stubby = STUB()