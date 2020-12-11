# Who worked on this project?
Alexander Rudolph, Simon Franke and Florian Formanek

# Which component does what?
As you can see, right now we have 4 Python files `dnssy.py`, `resolve.py`, `stubby.py` and `run.py`. From each name, you can probably guess what they do, but here is a little overview: 

- `dnssy.py`
	- A skeleton for all 7 DNS Servers. It provides basic functionality, like loading in it's zones, receiving requests and answering accordingly. All Servers will create a Log and Dumpfile which will be saved in a logfiles and dumps folder respectively. Logfiles will give short little information about what is going on right now. So they only contain important information. However dumpfiles will contain the full received/sent message.
	> Tip: Create your own DNS Server by adding a zone file and another line to `run.py`!
- `resolve.py`
	- The recursive resolver. It receives a message from our stub and gives an answer by either checking it's cache or by iterating over the nameservers until it either get's a fulfilling answer or an error
	> Tip: The resolver also generates a log and dumpfile similar to the DNS Servers. You can find the logfile after running `run.py` under `logs/resolver.log` and the dumpfile after the resolver received it's first request under `dumps/resolver.dump`
	- The resolver will also generate a file named `cache.json` where it saves queried Nameservers until their Time to Live has ended

- `stubby.py`
	- The stub resolver, which supports varying type of syntax. It supports querys like:
		- `domain` e.g `www.switch.telematik.` Asks the resolver for the A record of `www.switch.telematik.`
		- `domain @IP` e.g `www.switch.telematik. @127.0.0.13` Asks the `switch.telematik.` Nameserver for the A record of the Webserver
		- `domain @IP -p PORT` e.g `www.switch.telematik. @127.0.0.13 -p 53035` Asks the `switch.telematik.` Nameserver running on Port 53053 for the A record of the Webserver
		> The @IP and -p Tag are optional and if they are not provided, we always ask the resolver on Port 53053 for the domain
	
	- This file features a small dumb little guy called `stubby` he will tell you any other vital information

- `run.py`
	- The file that executes it all! `run.py` will open two python console windows. One will be left blank, because we couldn't solve it any different. The other one will open an instance of `stubby.py` that window is where the magic happens!
	> Note: We thought about hiding the first console window, but then you'd have to kill the python process to stop the servers

# What works, what does not?
As far as milestones go, every one except (d) is implemented and should work about 95%. 

## What works
Milestone (a) works. As described in ***Which component does what? > `stubby.py`*** you can directly query any Nameserver with `domain @IP -p PORT`

Milestone (b) and (c) also work because of `resolve.py`, which resolves requests from stubby and writes them to the cache

## What doesn't work
It is quite possible, that Nameservers deliver an error, when they shouldn't, because our suffix matching has a little error margin.

Results will only be cached if we have a successful query. We do not know what causes this

The proxy (and thus all dns.srv.* keys) are not implemented at all, mainly because we didn't really find the right way to access this problem, so we left it out.

# Important IPs
If you wan't to query any Nameserver directly, use these (You could also find these IPs in the `zone` Folder):

- `Stub`: 127.0.0.10
- `ROOT`: 127.0.0.11
	- `telematik.`: 127.0.0.12
		- `switch.telematik.`: 127.0.0.13
		- `router.telematik.`: 127.0.0.16
	- `fuberlin.`: 127.0.0.19
		- `homework.fuberlin.`: 127.0.0.20
		- `pcpools.fuberlin.`: 127.0.0.23

## Not so important IPs
These IPs aren't bound to anything, because we don't run any services, but if you wan't to check if you get the right answer you can find them here

- `www.switch.telematik.`: 127.0.0.14
- `mail.switch.telematik.`: 127.0.0.15
- `news.router.telematik.`: 127.0.0.17
- `shop.router.telematik.`: 127.0.0.18
- `easy.homework.fuberlin.`: 127.0.0.21
- `hard.homework.fuberlin.`: 127.0.0.22
- `linux.pcpools.fuberlin.`: 127.0.0.24
- `macos.pcpools.fuberlin.`: 127.0.0.25
- `windows.pcpools.fuberlin.`: 127.0.0.26
