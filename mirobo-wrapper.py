import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '.', '.vendors'))

import argparse
import mirobo
import json
import logging

parser = argparse.ArgumentParser()
parser.add_argument('ip', type=str, help='vacuum ip address')
parser.add_argument('token', type=str, help='token')
parser.add_argument('cmd', nargs='*')
parser.add_argument('--id-file', type=str, default=os.path.dirname(__file__) + 'python-mirobo.seq')
args = parser.parse_args()

def cleanup(vac, id_file):
    seqs = {'seq': vac.raw_id, 'manual_seq': vac.manual_seqnum}
    with open(args.id_file, 'w') as f:
        json.dump(seqs, f)


def get_vac():
    start_id = manual_seq = 0
    try:
        with open(args.id_file, 'r') as f:
            x = json.load(f)
            start_id = x.get("seq", 0)
            manual_seq = x.get("manual_seq", 0)
    except (FileNotFoundError, TypeError) as ex:
        pass

    vac = mirobo.Vacuum(args.ip, args.token, start_id)
    vac.manual_seqnum = manual_seq

    logging.basicConfig(level=logging.CRITICAL)
    return vac

def vac_status(vac):
    res = vac.status()
    if not res: return dict()

    if res.error_code:
        return {
            'error_message': res.error,
            'error_code': res.error_code
        }

    return {
        'state_code': res.state_code,
        'state': res.state,
        'battery': res.battery,
        'fan_speed': res.fanspeed,
        'clean_seconds': res.data["clean_time"],
        'clean_area': res.clean_area
    }

def vac_start(vac):
    return {'code': vac.start()}

def vac_stop(vac):
    return {'code': vac.stop()}

def vac_spot(vac):
    return {'code': vac.spot()}

def vac_pause(vac):
    return {'code': vac.pause()}

def vac_home(vac):
    return {'code': vac.home()}

def vac_find(vac):
    return {'code': vac.find()}


vac = get_vac()
cmd_name = args.cmd[0]

try:

    if cmd_name == 'status':
        print(json.dumps(vac_status(vac)))
    elif cmd_name == 'start':
        print(json.dumps(vac_start(vac)))
    elif cmd_name == 'stop':
        print(json.dumps(vac_stop(vac)))
    elif cmd_name == 'spot':
        print(json.dumps(vac_spot(vac)))
    elif cmd_name == 'pause':
        print(json.dumps(vac_pause(vac)))
    elif cmd_name == 'home':
        print(json.dumps(vac_home(vac)))
    elif cmd_name == 'find':
        print(json.dumps(vac_find(vac)))

except Exception as e:
    print(json.dumps({
        'exception': str(e)
    }))

cleanup(vac, args.id_file)
