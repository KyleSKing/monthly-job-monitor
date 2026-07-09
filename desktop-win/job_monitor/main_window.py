"""Main application window: job list, score filter, CRUD, and open-to-apply."""

from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .api_client import APIClient
from .job_dialog import JobDialog
from .models import Job
from .settings import load_base_url, save_base_url


class FetchThread(QThread):
    """Fetch the latest report's jobs off the UI thread."""

    done = Signal(list)
    failed = Signal(str)

    def __init__(self, client: APIClient):
        super().__init__()
        self._client = client

    def run(self):
        try:
            self.done.emit(self._client.fetch_latest_report())
        except Exception as exc:  # noqa: BLE001 - surface any network/parse error
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    COLUMNS = ["Score", "Title", "Company", "Location", "Salary"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Job Monitor")
        self.resize(900, 600)

        self.client = APIClient(load_base_url())
        self.jobs: list[Job] = []
        self.min_score = 0
        self._thread: FetchThread | None = None

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)

        # Toolbar
        toolbar = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.add_btn = QPushButton("Add")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.apply_btn = QPushButton("Apply (open URL)")
        self.settings_btn = QPushButton("Settings")
        self.refresh_btn.clicked.connect(self.refresh)
        self.add_btn.clicked.connect(self.add_job)
        self.edit_btn.clicked.connect(self.edit_job)
        self.delete_btn.clicked.connect(self.delete_job)
        self.apply_btn.clicked.connect(self.apply_job)
        self.settings_btn.clicked.connect(self.edit_settings)
        for btn in (
            self.refresh_btn,
            self.add_btn,
            self.edit_btn,
            self.delete_btn,
            self.apply_btn,
        ):
            toolbar.addWidget(btn)
        toolbar.addStretch()
        toolbar.addWidget(self.settings_btn)
        layout.addLayout(toolbar)

        # Score filter
        filter_row = QHBoxLayout()
        self.score_label = QLabel("Minimum Score: 0")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 10)
        self.slider.valueChanged.connect(self._on_score_changed)
        filter_row.addWidget(self.score_label)
        filter_row.addWidget(self.slider)
        layout.addLayout(filter_row)

        # Table
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.apply_job)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.status = QLabel("")
        layout.addWidget(self.status)

        self.setCentralWidget(central)

    # --- data ---

    def refresh(self):
        self.status.setText("Loading…")
        self.refresh_btn.setEnabled(False)
        self._thread = FetchThread(self.client)
        self._thread.done.connect(self._on_fetched)
        self._thread.failed.connect(self._on_fetch_failed)
        self._thread.start()

    def _on_fetched(self, jobs: list):
        self.jobs = jobs
        self.refresh_btn.setEnabled(True)
        self._render()
        self.status.setText(f"{len(jobs)} jobs loaded")

    def _on_fetch_failed(self, message: str):
        self.refresh_btn.setEnabled(True)
        self.status.setText(f"Error: {message}")
        QMessageBox.warning(self, "Load failed", message)

    def _visible_jobs(self) -> list[Job]:
        return [j for j in self.jobs if j.score >= self.min_score]

    def _render(self):
        visible = self._visible_jobs()
        self.table.setRowCount(len(visible))
        for row, job in enumerate(visible):
            values = [
                str(job.score),
                job.title,
                job.company,
                job.location,
                job.salary_range or "",
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def _selected_job(self) -> Job | None:
        row = self.table.currentRow()
        visible = self._visible_jobs()
        if 0 <= row < len(visible):
            return visible[row]
        return None

    def _on_score_changed(self, value: int):
        self.min_score = value
        self.score_label.setText(f"Minimum Score: {value}")
        self._render()

    # --- actions ---

    def apply_job(self):
        job = self._selected_job()
        if not job:
            return
        if job.url:
            webbrowser.open(job.url)
        else:
            QMessageBox.information(self, "No URL", "This job has no application URL.")

    def add_job(self):
        dialog = JobDialog(self)
        if dialog.exec():
            try:
                self.client.create_job(dialog.result_job())
            except Exception as exc:  # noqa: BLE001
                QMessageBox.warning(self, "Create failed", str(exc))
                return
            self.refresh()

    def edit_job(self):
        job = self._selected_job()
        if not job:
            return
        dialog = JobDialog(self, job)
        if dialog.exec():
            try:
                self.client.update_job(dialog.result_job())
            except Exception as exc:  # noqa: BLE001
                QMessageBox.warning(self, "Update failed", str(exc))
                return
            self.refresh()

    def delete_job(self):
        job = self._selected_job()
        if not job:
            return
        confirm = QMessageBox.question(
            self, "Delete", f"Delete '{job.title}'?"
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self.client.delete_job(job.id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Delete failed", str(exc))
            return
        self.refresh()

    def edit_settings(self):
        url, ok = QInputDialog.getText(
            self, "Settings", "API base URL:", text=self.client.base_url
        )
        if ok and url.strip():
            save_base_url(url)
            self.client = APIClient(load_base_url())
            self.refresh()
