"""Add/edit job form dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
)

from .api_client import validate_job
from .models import Job


class JobDialog(QDialog):
    """Create a new job or edit an existing one."""

    def __init__(self, parent=None, job: Job | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Job" if job else "New Job")
        self._job = job

        self.title = QLineEdit(job.title if job else "")
        self.company = QLineEdit(job.company if job else "")
        self.location = QLineEdit(job.location if job else "")
        self.url = QLineEdit(job.url if job else "")
        self.score = QSpinBox()
        self.score.setRange(0, 10)
        self.score.setValue(job.score if job else 0)
        self.salary = QLineEdit(job.salary_range if job and job.salary_range else "")
        self.summary = QPlainTextEdit(job.summary if job else "")

        form = QFormLayout(self)
        form.addRow("Title *", self.title)
        form.addRow("Company *", self.company)
        form.addRow("Location *", self.location)
        form.addRow("URL *", self.url)
        form.addRow("Score *", self.score)
        form.addRow("Salary", self.salary)
        form.addRow("Summary", self.summary)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _on_accept(self):
        errors = validate_job(self._collect())
        if errors:
            QMessageBox.warning(self, "Invalid", "\n".join(errors))
            return
        self.accept()

    def _collect(self) -> dict:
        return {
            "title": self.title.text().strip(),
            "company": self.company.text().strip(),
            "location": self.location.text().strip(),
            "url": self.url.text().strip(),
            "score": self.score.value(),
        }

    def result_job(self) -> Job:
        """Build the Job from the form; keeps the id/source when editing."""
        job = Job(
            title=self.title.text().strip(),
            company=self.company.text().strip(),
            location=self.location.text().strip(),
            url=self.url.text().strip(),
            score=self.score.value(),
            summary=self.summary.toPlainText().strip(),
            source=self._job.source if self._job else "manual",
            published_date=self._job.published_date if self._job else None,
            salary_range=self.salary.text().strip() or None,
        )
        if self._job:
            job.id = self._job.id
        return job
