#!/usr/bin/env python3

import os
import io
import sys
import csv
import docker
import psutil
import logging
import platform
import subprocess


def fastfail_call(args):
    try:
        # print('fastfail_call %s' % args)
        output = subprocess.check_output(args, timeout=10).decode()
    except subprocess.CalledProcessError as e:
        print(e)
        sys.exit(1)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
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
    driver_version = re.search(
        'Driver Version[\s\S]+?(\d+\.\d+)', output).group(1)
    cuda_version = re.search('CUDA Version[\s\S]+?(\d+\.\d+)', output).group(1)
    gpu_num = re.search('Attached GPUs[\s\S]+?(\d+)', output).group(1)
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
        'hostname': uname.node,
        'kernel': uname.release,
        'cpu_num': psutil.cpu_count(),
        'mem_tot': psutil.virtual_memory().total,
        'gpu': nvidia_info(),
        'docker': docker_info(),
    }


def container_pids(container_name):
    return fastfail_call(['docker', 'top', container_name, '-eo', 'pid']).split()[1:-1]


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
    reader = csv.reader(io.StringIO(output))
    next(reader)  # Skip csv header

    return [{
            'gpu_usage': row[0],
            'mem_usage': row[1],
            'mem_used': row[2],
            'mem_free': row[3],
            'mem_tot': row[4],
            'gpu_temperature': row[5],
            } for row in reader]


def nvidia_smi_query_apps():
    '''
    nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv,noheader,nounits
    15185, python3, 9089

    nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv,noheader
    15185, python3, 9089 MiB
    '''
    output = fastfail_call(['nvidia-smi',
                            '--query-compute-apps=pid,name,used_memory',
                            '--format=csv,noheader,nounits'
                            ])
    reader = csv.reader(io.StringIO(output))
    return [{
            'pid': row[0],
            'proc_name': row[1],
            'mem_used': row[2],
            } for row in reader]


def docker_stats():
    '''
    docker stats --no-stream --format {{.Name}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}
    DianAI,171.47%,5.43%,3.408GiB / 62.78GiB,62.5GB / 23.2GB,14.7GB / 3.82GB,109
    MrHei2,0.00%,0.00%,716KiB / 62.78GiB,6.35GB / 164MB,20.3GB / 9.1GB,1
    '''
    output = fastfail_call(['docker',
                            'stats',
                            '--no-stream',
                            '--format',
                            "{{.Name}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}"
                            ])
    reader = csv.reader(io.StringIO(output))

    def _convert_row(row):
        mem_used, _, mem_limit = row[3].split()
        net_input, _, net_output = row[4].split()
        block_input, _, block_output = row[5].split()

        return {
            'name': row[0],
            'cpu_perc': row[1],
            'mem_used': mem_used,
            'mem_limit': mem_limit,
            'net_input': net_input,
            'net_output': net_output,
            'block_input': block_input,
            'block_output': block_output,
        }

    return [_convert_row(row) for row in reader]


def disk_usage(mountpoints=['/', '/disk']):
    devices = psutil.disk_partitions()
    mount_device = {}
    for m in mountpoints:
        for d in devices:
            if m == d.mountpoint:
                mount_device[m] = d.device

    def _disk_usage(m):
        du = psutil.disk_usage(m)
        return {
            'disk': m,
            'total': du.total,
            'used': du.used,
            'free': du.free,
            'percent': du.percent,
        }
    return [_disk_usage(m) for m in mountpoints]


def sys_load():
    vm = psutil.virtual_memory()

    return {
        'cpu_perc': psutil.cpu_percent(),
        'mem_tot': vm.total,
        'mem_used': vm.used,
        'mem_free': vm.free,
        'mem_avail': vm.available,
    }


def sys_dynamic_info():
    apps = nvidia_smi_query_apps()
    container_stats = docker_stats()

    for s in container_stats:
        s['pids'] = container_pids(s['name'])
        s['apps'] = []

    for app in apps:
        for s in container_stats:
            if app['pid'] in s['pids']:
                s['apps'].append(app)

    for s in container_stats:
        del s['pids']

    return {
        'containers': container_stats,
        'gpu_info': nvidia_smi_query_gpu(),
        'sys_load': sys_load(),
        'disk_usage': disk_usage(),
    }


USAGE = '''
Usage: %s <option>

Option:
    --static    Collect static info
    --dynamic   Collect dynamic info
'''

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(USAGE % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == '--dynamic':
        info = sys_dynamic_info()
    elif sys.argv[1] == '--static':
        info = sys_static_info()
    else:
        print('Invalid option %s' % sys.argv[1])
        sys.exit(1)

    import json

    print(json.dumps(info, indent=4))
