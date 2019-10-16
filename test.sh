curl -X POST -H 'Content-Type: application/json' http://localhost:9200/syslog-ng-app/_mapping/app -d '
{
    "properties": {
        "app": {
            "properties": {
                "app_name": {
                    "type": "text",
                    "fielddata" : true,
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "proc_name": {
                    "type": "text",
                    "fielddata" : true,
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
                "create_time": {
                    "type": "long"
                },
                "running_time": {
                    "type": "long"
                },
                "mem_used": {
                    "type": "long"
                },
                "timestamp": {
                    "type": "date"
                },
                "host": {
                    "type": "text",
                    "fielddata" : true,
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                }
            }
        }
    }
}'


docker run --network host -v /tmp/syslog-ng.conf:/etc/syslog-ng/syslog-ng.conf balabit/syslog-ng -d

# qiming3
sudo /tmp/venv/bin/aidockermon query containers -l -f DianAI