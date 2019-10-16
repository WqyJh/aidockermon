# aidockermon

[![Build Status](https://travis-ci.org/WqyJh/aidockermon.svg?branch=master)](https://travis-ci.org/WqyJh/aidockermon)
[![license](https://img.shields.io/badge/LICENCE-GPLv3-brightgreen.svg)](https://raw.githubusercontent.com/WqyJh/aidockermon/master/LICENSE)

Monitor system load of the server running the nvidia/cuda docker containers.

## Feature

- sysinfo: system static info
- sysload: system cpu/memory load
- gpu: nvidia gpu load
- disk: disk load
- containers: containers' load that based on the nvidia/cuda image

## Prerequisite

Python >= 3

## Installation

```bash
pip install aidockermon
```

Or use `setuptools`
```bash
python setup.py install
```

## Usage

```
$ aidockermon -h
usage: aidockermon [-h] [-v] {query,create-esindex,delete-esindex} ...

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit

command:
  {query,create-esindex,delete-esindex}
    query               Query system info, log them via syslog protocol
    create-esindex      Create elasticsearch index
    delete-esindex      Delete elasticsearch index
```

```
$ aidockermon query -h
usage: aidockermon query [-h] [-l] [-r REPEAT] [-f FILTERS [FILTERS ...]] type

positional arguments:
  type                  info type: sysinfo, sysload, gpu, disk, containers

optional arguments:
  -h, --help            show this help message and exit
  -l, --stdout          Print pretty json to console instead of send a log
  -r REPEAT, --repeat REPEAT
                        n/i repeat n times every i seconds
  -f FILTERS [FILTERS ...], --filters FILTERS [FILTERS ...]
                        Filter the disk paths for disk type; filter the
                        container names for containers type
```

**For example:**

Show sysinfo

```bash
$ aidockermon query -l sysinfo
{
    "gpu": {
        "gpu_num": 2,
        "driver_version": "410.104",
        "cuda_version": "10.0"
    },
    "mem_tot": 67405533184,
    "kernel": "4.4.0-142-generic",
    "cpu_num": 12,
    "docker": {
        "version": "18.09.3"
    },
    "system": "Linux"
}
```

Show sys load

```bash
$ aidockermon query -l sysload
{
    "mem_free": 11866185728,
    "mem_used": 8023793664,
    "cpu_perc": 57.1,
    "mem_perc": 12.8,
    "mem_avail": 58803163136,
    "mem_tot": 67405533184
}
```

Show gpu load

```bash
$ aidockermon query -l gpu
{
    "mem_tot": 11177,
    "gpu_temperature": 76.0,
    "mem_free": 1047,
    "mem_used": 10130,
    "gpu_perc": 98.0,
    "gpu_id": 0,
    "mem_perc": 46.0
}
{
    "mem_tot": 11178,
    "gpu_temperature": 66.0,
    "mem_free": 3737,
    "mem_used": 7441,
    "gpu_perc": 95.0,
    "gpu_id": 1,
    "mem_perc": 44.0
}
```

Show disk usage

```bash
$ aidockermon query disk -l -f /
{
    "path": "/",
    "device": "/dev/nvme0n1p3",
    "total": 250702176256,
    "used": 21078355968,
    "free": 216865271808,
    "percent": 8.9
}

$ aidockermon query disk -l -f / /disk
{
    "path": "/",
    "device": "/dev/nvme0n1p3",
    "total": 250702176256,
    "used": 21078355968,
    "free": 216865271808,
    "percent": 8.9
}
{
    "path": "/disk",
    "device": "/dev/sda1",
    "total": 1968874311680,
    "used": 1551374692352,
    "free": 317462949888,
    "percent": 83.0
}
```

Show containers' load

Note that the `app_name` would be read from environment variable `APP_NAME`, which
is a short description for this training program.

```bash
$ aidockermon query containers -l -f DianAI
{
    "proc_name": "python3 test_run.py",
    "app_name": "测试程序",
    "pid": 13540,
    "container": "DianAI",
    "started_time": 1554698236,
    "running_time": 9343,
    "mem_used": 9757
}
{
    "proc_name": "python train.py",
    "app_name": "",
    "pid": 15721,
    "container": "DianAI",
    "started_time": 1554698236,
    "running_time": 19343,
    "mem_used": 1497
}
{
    "mem_limit": 67481047040,
    "net_output": 47863240948,
    "block_read": 1327175626752,
    "net_input": 18802869033,
    "mem_perc": 14.637655604461704,
    "block_write": 132278439936,
    "name": "DianAI",
    "cpu_perc": 0.0,
    "mem_used": 9877643264
}
```

## Config

### logging
```yaml
debug: false
log:
  version: 1

  # This is the default level, which could be ignored.
  # CRITICAL = 50
  # FATAL = CRITICAL
  # ERROR = 40
  # WARNING = 30
  # WARN = WARNING
  # INFO = 20
  # DEBUG = 10
  # NOTSET = 0
  #level: 20
  disable_existing_loggers: false
  formatters:
    simple:
      format: '%(levelname)s %(message)s'
    monitor:
      format: '%(message)s'
  filters:
    require_debug_true:
      (): 'aidockermon.handlers.RequireDebugTrue'
  handlers:
    console:
      level: DEBUG
      class: logging.StreamHandler
      formatter: simple
      filters: [require_debug_true]
    monitor:
      level: INFO
      class: rfc5424logging.handler.Rfc5424SysLogHandler
      address: [127.0.0.1, 1514]
      enterprise_id: 1
  loggers:
    runtime:
      handlers: [console]
      level: DEBUG
      propagate: false
    monitor:
      handlers: [monitor, console]
      level: INFO
      propagate: false

```

This is the default config, which should be located at `/etc/aidockermon/config.yml`.

You can modify the `address` value to specify the logging target.
- `address: [127.0.0.1, 1514]`: UDP to 127.0.0.1:1514
- `address: /var/log/aidockermon`: unix domain datagram socket

If you add an `socktype` argument, you can specify whether to use UDP or TCP as transport protocol.
- `socktype: 1`: TCP
- `socktype: 2`: UDP

Enable TLS/SSL:
```yaml
tls_enable: true
tls_verify: true
tls_ca_bundle: /path/to/ca-bundle.pem
```

Set `debug` as `true`, you can see message output in the console.

### Cronjob

```bash
sudo cp etc/cron.d/aidockermon /etc/cron.d
sudo systemctl restart cron
```

### syslog-ng

Using syslog-ng to collect logs and send them to elasticsearch 
for future use such as visualization with kibana.

```bash
cp etc/syslog-ng/syslog-ng.conf /etc/syslog-ng/
sudo systemctl restart syslog-ng
```

Sample config:

```bash
@version: 3.20

destination d_elastic {
	elasticsearch2(
		index("syslog-ng")
		type("${.SDATA.meta.type}")
		flush-limit("0")
		cluster("es-syslog-ng")
		cluster-url("http://localhost:9200")
		client-mode("http")
		client-lib-dir(/usr/share/elasticsearch/lib)
		template("${MESSAGE}\n")
	);
};

source s_python {
  #unix-dgram("/var/log/aidockermon");
	syslog(ip(127.0.0.1) port(1514) transport("udp") flags(no-parse));
};

log {
	source (s_python);
  parser { syslog-parser(flags(syslog-protocol)); };
	destination (d_elastic);
};
```
Modify it to specify the elasticsearch server and the log source's port and protocol.

