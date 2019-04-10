#!/usr/bin/env python3

import os
import io
import sys
import csv
import json
import docker
import psutil
import logging
import platform
import argparse
import subprocess
import logging.config

from string import Template
from aidockermon import utils
from aidockermon import settings
from rfc5424logging import Rfc5424SysLogHandler

from aidockermon import __version__


logging.config.dictConfig(settings.LOGGING)
logger_runtime = logging.getLogger('runtime')
logger_monitor = logging.getLogger('monitor')


g_pre_stats = {}


class DeltaTemplate(Template):
    delimiter = '%'


def strfdelta(tdelta, fmt='%D %H:%M:%S'):
    d = {"D": tdelta.days}
    d['H'], rem = divmod(tdelta.seconds, 3600)
    d['M'], d['S'] = divmod(rem, 60)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


def strfcreate(tcreate, fmt='%D %H:%M:%S'):
    import datetime

    now = datetime.datetime.now()
    start = datetime.datetime.fromtimestamp(tcreate)
    return strfdelta(now - start)


def get_running_time(tcreate):
    import time

    tnow = time.time()
    return int(tnow - tcreate)


def fastfail_call(args):
    output = None
    try:
        output = subprocess.check_output(args, timeout=10).decode()
    except subprocess.CalledProcessError as e:
        logger_runtime.error(e)
    except OSError as e:
        logger_runtime.error(e)
    return output


def docker_info():
    client = docker.from_env()
    version = client.version()

    return {
        'version': version['Version'],  # client version
    }


def nvidia_info():
    '''
    nvidia-smi -q --display=COMPUTE

    ==============NVSMI LOG==============

    Timestamp                           : Sun Mar 31 09:55:41 2019
    Driver Version                      : 410.78
    CUDA Version                        : 10.0

    Attached GPUs                       : 2
    GPU 00000000:01:00.0
        Compute Mode                    : Default

    GPU 00000000:02:00.0
        Compute Mode                    : Default
    '''
    import re

    output = fastfail_call(['nvidia-smi', '-q', '--display=COMPUTE'])
    if output is None:
        return {}

    driver_version = re.search(
        'Driver Version[\s\S]+?(\d+\.\d+)', output).group(1)
    cuda_version = re.search('CUDA Version[\s\S]+?(\d+\.\d+)', output).group(1)
    gpu_num = int(re.search('Attached GPUs[\s\S]+?(\d+)', output).group(1))
    return {
        'driver_version': driver_version,
        'cuda_version': cuda_version,
        'gpu_num': gpu_num,
    }


def sys_static_info():
    import platform
    uname = platform.uname()

    return {
        'system': uname.system,
        'kernel': uname.release,
        'cpu_num': psutil.cpu_count(),
        'mem_tot': psutil.virtual_memory().total,
        'gpu': nvidia_info(),
        'docker': docker_info(),
    }


def container_pids(container_name):
    output = fastfail_call(['docker', 'top', container_name, '-eo', 'pid'])
    if output is None:
        return []

    return [int(x) for x in output.split()[1:]]


def nvidia_smi_query_gpu():
    '''
    nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.free,memory.total,temperature.gpu --format=csv,noheader,nounits
    0, 0, 0, 11178, 11178, 45
    100, 69, 9099, 2079, 11178, 63

    nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.free,memory.total,temperature.gpu --format=csv,noheader
    0 %, 0 %, 0 MiB, 11178 MiB, 11178 MiB, 45
    82 %, 28 %, 9099 MiB, 2079 MiB, 11178 MiB, 63
    '''
    output = fastfail_call(['nvidia-smi',
                            '--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.free,memory.total,temperature.gpu',
                            '--format=csv,noheader,nounits'
                            ])
    if output is None:
        return []

    reader = csv.reader(io.StringIO(output), skipinitialspace=True)

    return [{
            'gpu_id': i,
            'gpu_perc': float(row[0]),
            'mem_perc': float(row[1]),
            'mem_used': int(row[2]),
            'mem_free': int(row[3]),
            'mem_tot': int(row[4]),
            'gpu_temperature': float(row[5]),
            } for i, row in enumerate(reader)]


def nvidia_smi_query_apps():
    '''
    nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits
    15185, 9089

    nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
    15185, 9089 MiB
    '''
    output = fastfail_call(['nvidia-smi',
                            '--query-compute-apps=pid,used_memory',
                            '--format=csv,noheader,nounits'
                            ])
    if output is None:
        return []

    def _convert_row(row):
        pid = int(row[0])
        mem_used = int(row[1])

        p = psutil.Process(pid)
        proc_name = ' '.join(p.cmdline())
        running_time = get_running_time(p.create_time())

        return {
            'pid': pid,
            'proc_name': proc_name,
            'mem_used': mem_used,
            'running_time': running_time,
        }

    reader = csv.reader(io.StringIO(output), skipinitialspace=True)
    return [_convert_row(row) for row in reader]


def docker_stats():
    '''
    docker stats --no-stream --format {{.Name}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}
    DianAI,171.47%,5.43%,3.408GiB / 62.78GiB,62.5GB / 23.2GB,14.7GB / 3.82GB,/109
    MrHei2,0.00%,0.00%,716KiB / 62.78GiB,6.35GB / 164MB,20.3GB / 9.1GB,1
    '''
    output = fastfail_call(['docker',
                            'stats',
                            '--no-stream',
                            '--format',
                            "{{.Name}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}"
                            ])
    reader = csv.reader(io.StringIO(output), skipinitialspace=True)

    def _convert_row(row):
        mem_used, _, mem_limit = row[3].split()
        net_input, _, net_output = row[4].split()
        block_read, _, block_write = row[5].split()

        return {
            'name': row[0],
            'cpu_perc': float(row[1]),
            'mem_perc': float(row[2]),
            'mem_used': int(mem_used),
            'mem_limit': int(mem_limit),
            'net_input': int(net_input),
            'net_output': int(net_output),
            'block_read': int(block_read),
            'block_write': int(block_write),
        }

    return [_convert_row(row) for row in reader]


def docker_stats2(filters=None):
    client = docker.from_env()
    containers = client.containers.list()

    # Filter the containers by specified container names
    if isinstance(filters, list):
        containers = [c for c in containers if c.name in filters]

    def _convert_stats(c):
        stats = c.stats(stream=False)
        if c.name in g_pre_stats:
            cpu_stats = stats['cpu_stats']
            pre_cpu_stats = g_pre_stats[c.name]['cpu_stats']
            cpu_perc = (cpu_stats['cpu_usage']['total_usage'] - pre_cpu_stats['cpu_usage']
                        ['total_usage']) / (cpu_stats['system_cpu_usage'] - pre_cpu_stats['system_cpu_usage']) * 100.0
        else:
            cpu_perc = 0

        mem_used = stats['memory_stats']['stats']['rss']
        mem_limit = stats['memory_stats']['limit']

        net_input, net_output = 0, 0
        if 'networks' in stats:
            for _, v in stats['networks'].items():
                net_input += v['rx_bytes']
                net_output += v['tx_bytes']

        blk_read, blk_write = 0, 0
        for v in stats['blkio_stats']['io_service_bytes_recursive']:
            if v['op'] == 'Read':
                blk_read += v['value']
            elif v['op'] == 'Write':
                blk_write += v['value']

        g_pre_stats[c.name] = stats

        return {
            'name': c.name,
            'cpu_perc': float(cpu_perc),
            'mem_perc': float(mem_used) / float(mem_limit) * 100,
            'mem_used': int(mem_used),
            'mem_limit': int(mem_limit),
            'net_input': int(net_input),
            'net_output': int(net_output),
            'block_read': int(blk_read),
            'block_write': int(blk_write),
        }

    return [_convert_stats(c) for c in containers]


def disk_usage(filters=['/', '/disk']):
    mountpoints = filters
    devices = psutil.disk_partitions()
    mount_device = {}
    for m in mountpoints:
        for d in devices:
            if m == d.mountpoint:
                mount_device[m] = d.device

    def _disk_usage(m):
        try:
            du = psutil.disk_usage(m)
            return {
                'path': m,
                'device': mount_device[m],
                'total': du.total,
                'used': du.used,
                'free': du.free,
                'percent': du.percent,
            }
        except OSError as e:
            logger_runtime.critical(e)
            return {
                'path': m,
                'device': '',
                'total': 0,
                'used': 0,
                'free': 0,
                'percent': 0,
            }

    return [_disk_usage(m) for i, m in enumerate(mountpoints)]


def sys_load():
    vm = psutil.virtual_memory()

    return {
        'cpu_perc': psutil.cpu_percent(),
        'mem_perc': vm.percent,
        'mem_tot': vm.total,
        'mem_used': vm.used,
        'mem_free': vm.free,
        'mem_avail': vm.available,
    }


def get_container_stats(filters=None):
    apps = nvidia_smi_query_apps()
    container_stats = docker_stats2(filters=filters)

    for s in container_stats:
        s['pids'] = container_pids(s['name'])

    for app in apps:
        for s in container_stats:
            if app['pid'] in s['pids']:
                app['container'] = s['name']

    for s in container_stats:
        del s['pids']

    return (
        ('app', apps),
        ('containers', container_stats),
    )


TYPES_MAP = {
    'sysinfo': sys_static_info,
    'sysload': sys_load,
    'gpu': nvidia_smi_query_gpu,
    'disk': disk_usage,
    'containers': get_container_stats,
}


def parse_repeat(repeat):
    if repeat:
        r = repeat.split('/')
        n, i = int(r[0]), int(r[1])
    else:
        n, i = 1, None
    return n, i


def do_repeat(func, n, i):
    import time

    func()

    for x in range(n - 1):
        time.sleep(i)
        func()


def _do_query(type, stdout, filters=None):
    func = TYPES_MAP[type]
    data = func(filters=filters) if filters else func()

    def _handle_data(data, type):
        if stdout:
            print(json.dumps(data, indent=4))
            return

        # ${MESSAGE} = type
        # ${.SDATA.meta.*} = json data
        # logger_monitor.info(type, extra={'structured_data': {'meta': data}})

        # We prefer this one!
        # ${.SDATA.meta.type} = type
        # ${MESSAGE} = json data
        logger_monitor.info(json.dumps(data),
                            extra={'structured_data': {'meta': {'type': type}}})

    def _handle_one_or_more_data(data, type):
        if isinstance(data, list):
            for d in data:
                _handle_data(d, type)
        else:
            _handle_data(data, type)

    if isinstance(data, tuple):
        for t, d in data:
            _handle_one_or_more_data(d, t)
    else:
        _handle_one_or_more_data(data, type)


def do_query(type, stdout, repeat, filters=None):
    n, i = parse_repeat(repeat)

    def func(): return _do_query(type, stdout, filters=filters)
    do_repeat(func, n, i)


def _main(argv):
    prog = os.path.basename(sys.argv[0])
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s-' + __version__)
    subparsers = parser.add_subparsers(title='command', dest='command')

    parser_query = subparsers.add_parser(
        'query', help='Query system info, log them via syslog protocol')
    parser_query.add_argument('type', type=str, help='info type: %s' %
                              ', '.join(TYPES_MAP.keys()))
    parser_query.add_argument('-l', '--stdout', action='store_true', default=False,
                              help="Print pretty json to console instead of send a log")
    parser_query.add_argument('-r', '--repeat', type=str,
                              help='n/i repeat n times every i seconds')
    parser_query.add_argument('-f', '--filters', nargs='+', type=str,
                              help='Filter the disk paths for disk type; filter the container names for containers type')

    parser_ces = subparsers.add_parser(
        'create-esindex', help='Create elasticsearch index')
    parser_ces.add_argument('index', type=str, help='index name', nargs='?')
    parser_ces.add_argument('-l', '--esurl', help='Specify the elasticsearch url',
                            default=utils.ES_URL)
    parser_ces.add_argument(
        '-a', '--all', action='store_true', help='Create all')

    parser_des = subparsers.add_parser(
        'delete-esindex', help='Delete elasticsearch index')
    parser_des.add_argument('index', type=str, help='index name', nargs='?')
    parser_des.add_argument('-l', '--esurl', help='Specify the elasticsearch url',
                            default=utils.ES_URL)
    parser_des.add_argument(
        '-a', '--all', action='store_true', help='Create all')

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
    elif args.command == 'query':
        if args.type not in TYPES_MAP:
            parser_query.print_help()
        else:
            do_query(args.type, args.stdout, args.repeat, filters=args.filters)
    elif args.command == 'create-esindex':
        if args.all:
            utils.create_es_indicies(es_url=args.esurl)
        else:
            if args.index is None:
                parser_ces.print_help()
                return

            utils.create_es_index(args.index, es_url=args.esurl)
    elif args.command == 'delete-esindex':
        if args.all:
            utils.delete_es_indicies(es_url=args.esurl)
        else:
            if args.index is None:
                parser_des.print_help()
                return
            utils.delete_es_index(args.index, es_url=args.esurl)


def main():
    _main(sys.argv[1:])


if __name__ == '__main__':
    main()
