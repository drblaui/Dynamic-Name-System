import json
with open("messages.json", "r+") as jsonfile:
	data = json.load(jsonfile)

	print(data["ROOT"]["sent"])

	data["ROOT"]["sent"] += 1
	jsonfile.seek(0)
	json.dump(data, jsonfile, indent=4)
	jsonfile.truncate()