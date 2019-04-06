import logging

DEBUG = False

LOGGING = {
    'version': 1,
    'level': logging.DEBUG,
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
            # 'address': '/var/log/aidockermon',

            # Use ip & port to enable packet sniff. (For debug purpose)
            'address': ('127.0.0.1', 1514),

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
