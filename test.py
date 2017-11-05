import argparse
import os
import subprocess
import sys
from time import sleep

module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
for mp in module_paths:
    sys.path.append(mp)

from msgpack import Unpacker
import socket
import msgpack

parser = argparse.ArgumentParser()
parser.add_argument('ip', type=str, help='vacuum ip address', default='192.168.1.12"')
parser.add_argument('token', type=str, help='token', default='476e6b70343055483230644c53707a12')
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=22222)
args = parser.parse_args()

print('starting server.py')

FNULL = open(os.devnull, 'w')
sProc = subprocess.Popen(['python3',
                            os.path.join(os.path.dirname(__file__), '.') + '/server.py',
                            args.ip, args.token, '--host', args.host, '--port', str(args.port)],
                            shell=False, stdout=FNULL, stderr=subprocess.PIPE)
sleep(1)

print('trying connect to %s:%s' % (args.host, args.port))

client = socket.create_connection((args.host, args.port))
client.sendall(msgpack.packb(['status'], use_bin_type=True))

print("sent request to server [status]")
print("reading response...")

def _reader(client):
    unpacker = Unpacker(encoding='utf-8')

    while True:
        data = client.recv(4096)

        if not data:
            print('connection closed')
            break

        unpacker.feed(data)

        for msg in unpacker:
            print('got server reply', msg)
            return

_reader(client)

sProc.kill()


