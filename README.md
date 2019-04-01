# aidockermon

Monitor system load of the server running the nvidia/cuda docker containers.

## Feature

- sysinfo: system static info
- sysload: system cpu/memory load
- gpu: nvidia gpu load
- disk: disk load (todo: specify disk path)
- containers: containers' load that based on the nvidia/cuda image

## Prerequisite

Python >= 3

```bash
pip install -r requirements.txt
```

## Usage

```bash
usage: main.py [-h] type

positional arguments:
  type        info type: sysinfo, sysload, gpu, disk, containers

optional arguments:
  -h, --help  show this help message and exit
```

**For example:**

Show sysinfo

```bash
$ python main.py sysinfo
{
    "kernel": "4.4.0-142-generic",
    "gpu": {
        "driver_version": "410.104",
        "gpu_num": "2",
        "cuda_version": "10.0"
    },
    "cpu_num": 12,
    "docker": {
        "version": "18.09.3"
    },
    "mem_tot": 67405533184,
    "hostname": "qiming3",
    "system": "Linux"
}
```

Show sys load

```bash
$ python main.py sysload
{
    "mem_tot": 67405533184,
    "mem_perc": 30.1,
    "cpu_perc": 83.3,
    "mem_avail": 47105003520,
    "mem_used": 19712966656,
    "mem_free": 8309858304
}
```

Show gpu load

```bash
$ python main.py gpu
[
    {
        "mem_perc": 0.0,
        "gpu_perc": 0.0,
        "mem_free": 2514,
        "mem_tot": 11178,
        "mem_used": 8664,
        "gpu_temperature": 64.0
    },
    {
        "mem_perc": 34.0,
        "gpu_perc": 56.0,
        "mem_free": 379,
        "mem_tot": 11178,
        "mem_used": 10799,
        "gpu_temperature": 65.0
    }
]

```

Show disk usage

```bash
$ python main.py disk
[
    {
        "used": 57564499968,
        "free": 181335523328,
        "disk": "/",
        "total": 251709792256,
        "percent": 24.1
    },
    {
        "used": 955389767680,
        "free": 913447927808,
        "disk": "/disk",
        "total": 1968874311680,
        "percent": 51.1
    }
]
```

Show containers' load

```bash
$ python main.py containers
[
    {
        "name": "MyContainer",
        "net_output": 16710919606,
        "mem_used": 18853982208,
        "apps": [
            {
                "pid": 20400,
                "mem_used": 1225,
                "started_time": 1554046950.09,
                "running_time": "0 18:29:15",
                "proc_name": "python3 predict.py"
            },
            {
                "pid": 5214,
                "mem_used": 7429,
                "started_time": 1554108955.34,
                "running_time": "0 1:15:50",
                "proc_name": "python3 train.py"
            },
            {
                "pid": 21218,
                "mem_used": 10789,
                "started_time": 1554058440.53,
                "running_time": "0 15:17:45",
                "proc_name": "python -u main.py -tc -e 100 -n full_tc -bms 20 -bs 80"
            }
        ],
        "net_input": 30074729518,
        "cpu_perc": 0.0,
        "block_read": 11825348608,
        "mem_limit": 67405533184,
        "block_write": 54593761280,
        "mem_perc": 27.970971101932264
    }
]
```