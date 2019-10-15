curl -X POST -H 'Content-Type: application/json' http://localhost:9200/syslog-ng-app/_mapping/app_name -d '
{
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
            }
}
}'


docker run --network host -v /tmp/syslog-ng.conf:/etc/syslog-ng/syslog-ng.conf balabit/syslog-ng -d

# qiming3
sudo /tmp/venv/bin/aidockermon query containers -l -f DianAI