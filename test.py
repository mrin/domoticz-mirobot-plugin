#!/usr/bin/python3
import argparse
import os
import sys

module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
for mp in module_paths:
    sys.path.append(mp)
    print('test: python modules path: %s' % mp)

from msgpack import Unpacker
import socket
import msgpack

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=22222)
args = parser.parse_args()

print('test: trying connect to %s:%s' % (args.host, args.port))

client = socket.create_connection((args.host, args.port))
client.sendall(msgpack.packb(['status'], use_bin_type=True))

print("test: sent request to server [status]")
print("test: reading response...")

unpacker = Unpacker(encoding='utf-8')

while True:
    data = client.recv(4096)

    if not data:
        print('test: connection closed')
        break

    unpacker.feed(data)

    for msg in unpacker:
        print('test: got server reply', msg)
        sys.exit(0)

