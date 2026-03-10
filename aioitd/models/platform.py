from aioitd.models.base import ITDBaseModel


class Version(ITDBaseModel):
    changes: list[str]
    date: str
    version: str


__all__ = ['Version']
