import json
import requests

ES_URL = 'http://localhost:9200'

ES_MAPPINGS = {
    "sysinfo": {
        "properties": {
            "cpu_num": {
                "type": "long"
            },
            "docker": {
                "properties": {
                    "version": {
                        "type": "text",
                        "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                        }
                    }
                }
            },
            "gpu": {
                "properties": {
                    "gpu_num": {
                        "type": "long"
                    },
                    "driver_version": {
                        "type": "text",
                        "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                        }
                    },
                    "cuda_version": {
                        "type": "text",
                        "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                        }
                    }
                }
            },
            "hostname": {
                "type": "text",
                "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                }
            },
            "kernel": {
                "type": "text",
                "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                }
            },
            "mem_tot": {
                "type": "long"
            },
            "system": {
                "type": "text",
                "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                }
            },
            "timestamp": {
                "type": "date"
            }
        }
    },
    "sysload": {
        "properties": {
            "cpu_perc": {
                "type": "float"
            },
            "mem_avail": {
                "type": "long"
            },
            "mem_free": {
                "type": "long"
            },
            "mem_perc": {
                "type": "float"
            },
            "mem_tot": {
                "type": "long"
            },
            "mem_used": {
                "type": "long"
            },
            "timestamp": {
                "type": "date"
            }
        }
    },
    "disk": {
        "properties": {
            "disk0": {
                "properties": {
                    "disk": {
                        "type": "text",
                        "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                        }
                    },
                    "free": {
                        "type": "long"
                    },
                    "percent": {
                        "type": "float"
                    },
                    "total": {
                        "type": "long"
                    },
                    "used": {
                        "type": "long"
                    }
                }
            },
            "disk1": {
                "properties": {
                    "disk": {
                        "type": "text",
                        "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                        }
                    },
                    "free": {
                        "type": "long"
                    },
                    "percent": {
                        "type": "float"
                    },
                    "total": {
                        "type": "long"
                    },
                    "used": {
                        "type": "long"
                    }
                }
            },
            "timestamp": {
                "type": "date"
            }
        }
    },
    "gpu": {
        "properties": {
            "gpu0": {
                "properties": {
                    "gpu_perc": {
                        "type": "long"
                    },
                    "gpu_temperature": {
                        "type": "float"
                    },
                    "mem_used": {
                        "type": "long"
                    },
                    "mem_free": {
                        "type": "long"
                    },
                    "mem_tot": {
                        "type": "long"
                    },
                    "mem_perc": {
                        "type": "long"
                    }
                }
            },
            "gpu1": {
                "properties": {
                    "gpu_perc": {
                        "type": "long"
                    },
                    "gpu_temperature": {
                        "type": "float"
                    },
                    "mem_used": {
                        "type": "long"
                    },
                    "mem_free": {
                        "type": "long"
                    },
                    "mem_tot": {
                        "type": "long"
                    },
                    "mem_perc": {
                        "type": "long"
                    }
                }
            },
            "timestamp": {
                "type": "date"
            }
        }
    },
    "containers": {
        "properties": {
            "containers": {
                "properties": {
                    "block_read": {
                        "type": "long"
                    },
                    "block_write": {
                        "type": "long"
                    },
                    "cpu_perc": {
                        "type": "float"
                    },
                    "mem_limit": {
                        "type": "long"
                    },
                    "mem_perc": {
                        "type": "float"
                    },
                    "mem_used": {
                        "type": "long"
                    },
                    "name": {
                        "type": "text",
                        "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                        }
                    },
                    "net_input": {
                        "type": "long"
                    },
                    "net_output": {
                        "type": "long"
                    },
                    "apps": {
                        "properties": {
                            "running_time": {
                                "type": "text",
                                "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                }
                            },
                            "proc_name": {
                                "type": "text",
                                "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                }
                            },
                            "pid": {
                                "type": "long"
                            },
                            "started_time": {
                                "type": "float"
                            },
                            "mem_used": {
                                "type": "long"
                            }
                        }
                    }
                }
            },
            "timestamp": {
                "type": "date"
            }
        }
    }
}

INDEX_PREFIX = 'syslog-ng-'


def es_res_ack(res):
    data = json.loads(res.content.decode())
    if data.get('acknowledged', False):
        return 'Succeed'
    else:
        return 'Failed'


def create_es_index(index, mappings=ES_MAPPINGS, es_url=ES_URL):
    type = index
    index = INDEX_PREFIX + type
    print('Creating index <%s>' % (index,), end=' ')
    req_url = '%s/%s' % (es_url, index)
    data = json.dumps({
        'mappings': {
            type: mappings[type],
        },
    })
    headers = {
        'Content-Type': 'application/json',
    }
    res = requests.put(req_url, data=data, headers=headers)

    print(es_res_ack(res))


def create_es_indicies(mappings=ES_MAPPINGS, es_url=ES_URL):
    for k in mappings.keys():
        create_es_index(k, es_url=es_url)


def delete_es_index(index, es_url=ES_URL):
    index = INDEX_PREFIX + index
    print('Deleting index <%s>' % (index,), end=' ')
    req_url = '%s/%s' % (es_url, index)
    res = requests.delete(req_url)

    print(es_res_ack(res))


def delete_es_indicies(mappings=ES_MAPPINGS, es_url=ES_URL):
    for k in mappings.keys():
        delete_es_index(k, es_url=es_url)
