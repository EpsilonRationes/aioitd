from aioitd.exceptions import *
from aioitd.models import *
from aioitd.client import AsyncITDClient
from aioitd.api import Reason, ReportTargetType

from aioitd.objects import *


def _rebuild_model_tree(cls):
    from aioitd.client import AsyncITDClient
    cls.model_rebuild()
    for sub in cls.__subclasses__():
        _rebuild_model_tree(sub)


def _rebuild_models():
    _rebuild_model_tree(UserRef)
    _rebuild_model_tree(PostRef)
    _rebuild_model_tree(CommentRef)
    _rebuild_model_tree(FileRef)
    _rebuild_model_tree(NotificationRef)
    _rebuild_model_tree(HashtagRef)

_rebuild_models()
