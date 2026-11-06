from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

from pymongo import AsyncMongoClient
from taskiq.abc.result_backend import AsyncResultBackend
from taskiq.depends.progress_tracker import TaskProgress
from taskiq.exceptions import ResultGetError
from taskiq.result import TaskiqResult


class ResultIsMissingError(ResultGetError):
    """Raised when a result is requested but none exists yet."""


_ReturnType = TypeVar("_ReturnType")


class MongoResultBackend(AsyncResultBackend[_ReturnType]):
    """TaskIQ async result backend: stores task results and progress in MongoDB."""

    def __init__(
        self,
        uri: str,
        database_name: str,
        collection_name: str = "task_results",
        keep_results: bool = True,
        ttl_seconds: int = 3600,
    ) -> None:
        """
        Configure the MongoDB client, database, and collection used to store results.

        :param uri: MongoDB connection URI.
        :param database_name: Database name.
        :param collection_name: Collection used for task documents.
        :param keep_results: If False, delete the document after a successful get_result.
        :param ttl_seconds: Seconds until result documents expire; 0 omits expire_at (no TTL expiry).
        """
        self.client = AsyncMongoClient(uri)
        self.database = self.client[database_name]
        self.collection = self.database[collection_name]
        self.keep_results = keep_results
        self.ttl_seconds = ttl_seconds

    async def startup(self) -> None:
        """Create a unique index on task_id; if ttl_seconds > 0, also create a TTL index on expire_at."""
        await self.collection.create_index("task_id", unique=True)
        if self.ttl_seconds > 0:
            await self.collection.create_index("expire_at", expireAfterSeconds=0)

    async def shutdown(self) -> None:
        """Close the MongoDB client."""
        await self.client.close()
        await super().shutdown()

    async def set_result(self, task_id: str, result: TaskiqResult[_ReturnType]) -> None:
        """
        Persist the final task result; sets expire_at when ttl_seconds > 0, otherwise unsets expire_at.

        :param task_id: Task id from the TaskIQ message; stored in the document field task_id.
        :param result: TaskiqResult after execution (return value, errors, timing, etc.).
        """
        fields = {
            "task_id": task_id,
            "value": result.model_dump(mode="json"),
        }
        if self.ttl_seconds > 0:
            fields["expire_at"] = datetime.now(UTC) + timedelta(
                seconds=self.ttl_seconds
            )
        update: dict[str, Any] = {"$set": fields}
        if self.ttl_seconds == 0:
            update["$unset"] = {"expire_at": None}
        await self.collection.update_one({"task_id": task_id}, update, upsert=True)

    async def is_result_ready(self, task_id: str) -> bool:
        """
        Return True if a document exists and includes the serialized result value.

        Progress-only documents do not count.

        :param task_id: Same id as used with set_result / kiq.
        :return: True when get_result can be called safely.
        """
        doc = await self.collection.find_one({"task_id": task_id})
        return doc is not None and "value" in doc

    async def get_result(
        self, task_id: str, with_logs: bool = False
    ) -> TaskiqResult[_ReturnType]:
        """
        Load and validate a TaskiqResult; raises if the document or its result value is missing.

        :param task_id: Task id to load; must match the id used when saving.
        :param with_logs: If True, keep logs on the result; if False, set log to None (smaller payload / privacy).
        :return: Deserialized TaskiqResult.
        :raises ResultIsMissingError: No document or result value written yet (e.g. only progress exists).
        """
        doc = await self.collection.find_one({"task_id": task_id})

        if not doc or "value" not in doc:
            raise ResultIsMissingError

        result = TaskiqResult[_ReturnType].model_validate(doc["value"])  # ty: ignore[invalid-argument-type]

        if not with_logs:
            result.log = None

        if not self.keep_results:
            await self.collection.delete_one({"task_id": task_id})

        return result

    async def set_progress(
        self, task_id: str, progress: TaskProgress[_ReturnType]
    ) -> None:
        """Update task progress (may coexist with a progress-only document until set_result writes the result)."""
        await self.collection.update_one(
            {"task_id": task_id},
            {"$set": {"progress": progress.model_dump(mode="json")}},
            upsert=True,
        )

    async def get_progress(self, task_id: str) -> TaskProgress[_ReturnType] | None:
        """Return current progress, or None if there is no document or no progress has been recorded."""
        doc = await self.collection.find_one({"task_id": task_id})

        if not doc or "progress" not in doc:
            return None

        return TaskProgress[_ReturnType].model_validate(doc["progress"])
