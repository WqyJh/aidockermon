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

## Installation

```bash
pip install aidockermon
```

Or use `setuptools`
```bash
python setup.py install
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
$ aidockermon -l sysinfo
{
    "gpu": {
        "gpu_num": "2",
        "driver_version": "410.104",
        "cuda_version": "10.0"
    },
    "mem_tot": 67405533184,
    "kernel": "4.4.0-142-generic",
    "hostname": "qiming3",
    "cpu_num": 12,
    "docker": {
        "version": "18.09.3"
    },
    "system": "Linux"
}
```

Show sys load

```bash
$ aidockermon -l sysload
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
$ aidockermon -l gpu
{
    "gpus": [
        {
            "mem_used": 9169,
            "gpu_temperature": 69.0,
            "mem_free": 2009,
            "mem_tot": 11178,
            "mem_perc": 39.0,
            "gpu_perc": 83.0
        },
        {
            "mem_used": 10,
            "gpu_temperature": 35.0,
            "mem_free": 11168,
            "mem_tot": 11178,
            "mem_perc": 0.0,
            "gpu_perc": 0.0
        }
    ]
}
```

Show disk usage

```bash
$ aidockermon -l disk
{
    "disks": [
        {
            "disk": "/",
            "used": 57594474496,
            "percent": 24.1,
            "free": 181305548800,
            "total": 251709792256
        },
        {
            "disk": "/disk",
            "used": 978046386176,
            "percent": 52.3,
            "free": 890791309312,
            "total": 1968874311680
        }
    ]
}
```

Show containers' load

```bash
$ aidockermon -l containers
{
    "containers": [
        {
            "name": "DianAI",
            "net_input": 84317943005,
            "net_output": 21176290682,
            "block_write": 89450307584,
            "block_read": 16414523392,
            "mem_limit": 67405533184,
            "cpu_perc": 0.0,
            "apps": [
                {
                    "running_time": "1 12:24:37",
                    "pid": 4692,
                    "proc_name": "python3 test_run.py",
                    "started_time": 1554431776.79,
                    "mem_used": 9159
                }
            ],
            "mem_perc": 11.067838593658443,
            "mem_used": 7460335616
        }
    ]
}
```

## logging config

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

## syslog-ng

Using syslog-ng to collect logs and send them to elasticsearch 
for future use such as visualization with kibana.

```bash
cp etc/syslog-ng/aidockermon.conf /etc/syslog-ng/conf.d
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

## Contribute

Use the following command to generate `requirements.txt`, other wise there would be
one line `pkg-resources==0.0.0` which cause a failure to install dependencies.

```bash
pip freeze | grep -v "pkg-resources" > requirements.txt
```