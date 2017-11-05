import os
import sys

module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
for mp in module_paths:
    sys.path.append(mp)

from gevent import monkey
monkey.patch_all()

import msgpack
from gevent.queue import Queue
from gevent.pool import Group
from gevent.server import StreamServer
import argparse
from miio import Vacuum, DeviceException
from msgpack import Unpacker
from logging.handlers import RotatingFileHandler
import logging

parser = argparse.ArgumentParser()
parser.add_argument('ip', type=str, help='vacuum ip address', default='192.168.1.12"')
parser.add_argument('token', type=str, help='token', default='476e6b70343055483230644c53707a12')
parser.add_argument('--host', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=22222)
args = parser.parse_args()

send = Queue()
receive = Queue()
sockets = {}

#### LOGGING

# fh = RotatingFileHandler(os.path.join(os.path.dirname(__file__), '.', 'log/server.log'), maxBytes=1024 * 1024, backupCount=5)
# fh.setLevel(logging.DEBUG)
# fh.setFormatter(logging.Formatter("%(asctime)s [%(process)s]:%(levelname)s:%(name)-10s| %(message)s", datefmt='%Y-%m-%d %H:%M:%S'))

s = logging.StreamHandler(sys.stdout)
s.setLevel(logging.DEBUG)
s.setFormatter(logging.Formatter("%(message)s"))

logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)
# logger.addHandler(fh)
logger.addHandler(s)

#### ./LOGGING

def socket_incoming_connection(socket, address):

    logger.debug('connected %s', address)

    sockets[address] = socket

    unpacker = Unpacker(encoding='utf-8')
    while True:
        data = socket.recv(4096)

        if not data:
            logger.debug('closed connection %s', address)
            break

        unpacker.feed(data)

        for msg in unpacker:
            receive.put(InMsg(msg, address))
            # logger.debug('got socket msg: %s', msg)

    sockets.pop(address)

def socket_msg_sender(sockets, q):
    while True:
        msg = q.get()
        if isinstance(msg, OutMsg) and msg.to in sockets:
            sockets[msg.to].sendall(msgpack.packb(msg, use_bin_type=True))
            # logger.debug('send reply %s', msg.to)



def vacuum_commands_handler(ip, token, q):
    vac = Vacuum(ip, token, 0)
    vac.manual_seqnum = 0

    while True:
        msg = q.get()
        try:
            cmd = msg.pop(0)
            if hasattr(VacuumCommand, cmd):
                result = getattr(VacuumCommand, cmd)(vac, *msg)
            else:
                result = {'error': 'command [%s] not found' % cmd}
        except (DeviceException, Exception) as e:
            result = {'error': 'python-miio: %s' % e}
        finally:
            result.update({'cmd': cmd})
            # logger.debug('vac result %s', result)
            send.put(OutMsg(result, msg.to))



class VacuumCommand(object):

    @classmethod
    def status(cls, vac):
        res = vac.status()
        if not res:
            return {
                'error': 'no response'
            }

        if res.error_code:
            return {
                'error': res.error
            }

        return {
            'state_code': res.state_code,
            'battery': res.battery,
            'fan_level': res.fanspeed,
            'clean_seconds': res.data["clean_time"],
            'clean_area': res.clean_area
        }

    @classmethod
    def start(cls, vac):
        return {'code': vac.start()}

    @classmethod
    def stop(cls, vac):
        return {'code': vac.stop()}

    @classmethod
    def spot(cls, vac):
        return {'code': vac.spot()}

    @classmethod
    def pause(cls, vac):
        return {'code': vac.pause()}

    @classmethod
    def home(cls, vac):
        return {'code': vac.home()}

    @classmethod
    def find(cls, vac):
        return {'code': vac.find()}

    @classmethod
    def set_fan_level(cls, vac, level):
        return {'code': vac.set_fan_speed(int(level))}

    @classmethod
    def consumable_status(cls, vac):
        res = vac.consumable_status()
        return {
            'main_brush': res.data['main_brush_work_time'],
            'side_brush': res.data['side_brush_work_time'],
            'filter': res.data['filter_work_time'],
            'sensor': res.data['sensor_dirty_time']
        }

    @classmethod
    def care_reset_main_brush(cls, vac):
        return {'code': vac.send('reset_consumable', ['main_brush_work_time'])}

    @classmethod
    def care_reset_side_brush(cls, vac):
        return {'code': vac.send('reset_consumable', ['side_brush_work_time'])}

    @classmethod
    def care_reset_filter(cls, vac):
        return {'code': vac.send('reset_consumable', ['filter_work_time'])}

    @classmethod
    def care_reset_sensor(cls, vac):
        return {'code': vac.send('reset_consumable', ['sensor_dirty_time'])}


class InMsg(list):
    def __init__(self, data, to, **kwargs):
        super(InMsg, self).__init__(**kwargs)
        self.extend(data)
        self.to = to


class OutMsg(dict):
    def __init__(self, data, to, **kwargs):
        super(OutMsg, self).__init__(**kwargs)
        self.update(data)
        self.to = to


if __name__ == '__main__':

    server = StreamServer((args.host, args.port), socket_incoming_connection)
    logger.debug('Starting server on %s %s' % (args.host, args.port))

    services = Group()
    services.spawn(server.serve_forever)
    services.spawn(vacuum_commands_handler, args.ip, args.token, receive)
    services.spawn(socket_msg_sender, sockets, send)
    services.join()
