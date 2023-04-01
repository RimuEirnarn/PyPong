# pylint: disable=all
from packs.client import Client, ClientLog
from time import sleep

test_small = "Hello, World!"
test_big = " "*2048

client = Client(('127.0.0.1', 2000))
ClientLog.debug(client)
client.start()
client.push(test_small)
data_small = client.json()['body']
ClientLog.info(f"{test_small == data_small = }")
client.push(test_big)
data_big = client.json()['body']
ClientLog.info(f"{test_big == data_big = }")

client.stop()
# from json import dumps
# from time import sleep


# sel, sock = setup_client_selectors(("127.0.0.1", 2000))
# sock.send(pack(dumps({
#     "message": "Hello, World"
# })))
# sleep(1)
# print(unpack(sock.recv(1024)))
# sock.close()

# from lib.connection import pack, unpack
# from socket import AF_INET, socket, SOCK_STREAM
# sock = socket(AF_INET, SOCK_STREAM)
# sock.connect(("127.0.0.1", 2000))
# sock.send(pack("Hello, World!"))
# sleep(1)
# print(unpack(sock.recv(1024)))
