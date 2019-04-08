import json
import requests
import pkg_resources

ES_URL = 'http://localhost:9200'

ES_MAPPINGS = json.loads(pkg_resources.resource_string('etc', 'mappings.json').decode())

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
