from typing import Annotated
from uuid import UUID

from pydantic import Field

from aioitd.models.base import ITDBaseModel, ITDDatetime


class Report(ITDBaseModel):
    id: UUID
    created_at: Annotated[ITDDatetime, Field(alias="createdAt")]


__all__ = [Report]
