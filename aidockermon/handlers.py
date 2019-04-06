import logging
from aidockermon import settings


class RequireDebugTrue(logging.Filter):
    """
    This is a filter which only accept records when DEBUG=True.
    """

    def filter(self, record):
        return settings.DEBUG
