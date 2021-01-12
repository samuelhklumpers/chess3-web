import json

from server.gameserver import thread_loop


with open("server_config.json") as f:
    config = json.load(f)

port = config["port"]

if __name__ == "__main__":
    thread_loop(port)
