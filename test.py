import argparse
import os
import subprocess
import sys
from time import sleep

module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
for mp in module_paths:
    sys.path.append(mp)
    print('test: python modules path: %s' % mp)

from msgpack import Unpacker
import socket
import msgpack

parser = argparse.ArgumentParser()
parser.add_argument('ip', type=str, help='vacuum ip address', default='192.168.1.12"')
parser.add_argument('token', type=str, help='token', default='476e6b70343055483230644c53707a12')
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=22222)
args = parser.parse_args()

print('test: starting server.py process')

sProc = subprocess.Popen(['python3',
                            os.path.join(os.path.dirname(__file__), '.') + '/server.py',
                            args.ip, args.token, '--host', args.host, '--port', str(args.port)],
                            shell=False)

print('test: wait server starting... 5 seconds ')
sleep(5)

print('test: trying connect to %s:%s' % (args.host, args.port))

client = socket.create_connection((args.host, args.port))
client.sendall(msgpack.packb(['status'], use_bin_type=True))

print("test: sent request to server [status]")
print("test: reading response...")

def _reader(client):
    unpacker = Unpacker(encoding='utf-8')

    while True:
        data = client.recv(4096)

        if not data:
            print('test: connection closed')
            break

        unpacker.feed(data)

        for msg in unpacker:
            print('test: got server reply', msg)
            return

_reader(client)

print('test: kill servery.py pid: %s' % sProc.pid)

sProc.kill()


