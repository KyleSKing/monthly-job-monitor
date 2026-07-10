"""Job model, aligned with the iOS `Job.swift` shape.

Fields mirror the backend API (`api/jobs.py` `_map_job`) and the iOS model,
including the legacy `salary` -> `salaryRange` compatibility.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    score: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    summary: str = ""
    source: str = ""
    published_date: str | None = None
    salary_range: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        """Decode a backend/report payload. Tolerant like the iOS decoder."""
        try:
            score = int(float(data.get("score", 0)))
        except (TypeError, ValueError):
            score = 0
        return cls(
            id=str(data.get("id") or uuid.uuid4()),
            title=data.get("title", ""),
            company=data.get("company", ""),
            location=data.get("location", ""),
            url=data.get("url", ""),
            score=score,
            summary=data.get("summary") or "",
            source=data.get("source") or "",
            published_date=data.get("publishedDate"),
            salary_range=data.get("salaryRange") or data.get("salary"),
        )

    def to_dict(self) -> dict:
        """Encode a write payload, normalizing to `salaryRange` like iOS."""
        payload = {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "url": self.url,
            "score": self.score,
            "summary": self.summary,
            "source": self.source,
        }
        if self.published_date is not None:
            payload["publishedDate"] = self.published_date
        if self.salary_range is not None:
            payload["salaryRange"] = self.salary_range
        return payload
