"""Job Repository Interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from job_service.domain.entities.job import Job


class IJobRepository(ABC):
    @abstractmethod
    async def save(self, job: Job) -> Job:
        pass

    @abstractmethod
    async def find_by_id(self, job_id: UUID) -> Optional[Job]:
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 10) -> List[Job]:
        pass

    @abstractmethod
    async def find_by_video_id(self, video_id: UUID) -> Optional[Job]:
        pass

    @abstractmethod
    async def update(self, job: Job) -> Job:
        pass

    @abstractmethod
    async def count_by_user_id(self, user_id: UUID) -> int:
        pass
