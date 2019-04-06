import io
import yaml
import logging

DEBUG = False

LOGGING = {
    'version': 1,
    'level': logging.INFO,
    'disable_existing_loggers': False,
    'formatters': {
        # 'verbose': {
        #     'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        # },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'monitor': {
            'format': '%(message)s'
        }
    },
    'filters': {
        'require_debug_true': {
            '()': 'aidockermon.handlers.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['require_debug_true'],
        },
        'monitor': {
            'level': 'INFO',
            'class': 'rfc5424logging.handler.Rfc5424SysLogHandler',
            # 'class': 'logging.handlers.SysLogHandler',

            # Use unix domain socket for better performance. (For production purpose)
            'address': '/var/log/aidockermon',

            # Use ip & port to enable packet sniff. (For debug purpose)
            # 'address': ('127.0.0.1', 1514),

            # `enterprise_id` MUST be set if you want to send structured_data.
            # Value of it would be ignored if you send data under
            # the predefined key like `meta`, which is unimportant
            # and could be any value in this case.
            'enterprise_id': 1,
        },
    },
    'loggers': {
        'runtime': {
            'handlers': ['console', ],
            'level': 'DEBUG',
            'propagate': False,
        },
        'monitor': {
            'handlers': ['monitor', 'console'],
            'level': 'INFO',
            'propagate': False,
        }
    },
}

CFG_FILE = '/etc/aidockermon/config.yml'


def load_yaml_compat(f):
    conf = yaml.load(f, Loader=yaml.SafeLoader)

    def _compat_log(log_conf):
        '''
        Because the Rfc5424SysLogHandler support tuple instead of
        list as it's address argument, we have to convert the
        address to tuple.
        '''
        if 'handlers' in log_conf:
            for k, v in log_conf['handlers'].items():
                if 'address' in v and isinstance(v['address'], list):
                    v['address'] = tuple(v['address'])

    if conf and 'log' in conf:
        _compat_log(conf['log'])

    return conf


try:
    with io.open(CFG_FILE, 'r') as f:
        conf = load_yaml_compat(f)

        if conf:
            DEBUG = conf.get('debug', False)
            LOGGING = conf.get('log', LOGGING)
except OSError as e:
    # print('Failed to parse config file: %s, use default config' % CFG_FILE)
    # Be quiet about it. No config file is a common scene.
    pass
