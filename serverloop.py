from server.gameserver import thread_loop

PORT = 3 ** 9 + 1

if __name__ == "__main__":
    thread_loop(PORT)
