"""Simple PyQt6 GUI for the Autonomous Engineering Agent.

This GUI provides a minimal interface to interact with the EngineeringAgent.
It exposes a dashboard with project metrics and a Kanban-style board for
task management.
"""

from __future__ import annotations

import os
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QTextEdit,
    QLineEdit,
    QMessageBox,
)

from ..core.agent import EngineeringAgent
from ..core.planner import Task, TaskStatus


class DashboardTab(QWidget):
    """Main dashboard displaying project metrics and recent reports."""

    def __init__(self, agent: EngineeringAgent):
        super().__init__()
        self.agent = agent
        self.layout = QVBoxLayout(self)

        # Metrics label
        self.metrics_label = QLabel("Project metrics will appear here")
        self.layout.addWidget(self.metrics_label)

        # Recent projects list
        self.recent_list = QListWidget()
        self.layout.addWidget(QLabel("Recent Reports"))
        self.layout.addWidget(self.recent_list)

        # Quick actions
        actions_layout = QHBoxLayout()
        self.new_button = QPushButton("New Project")
        self.new_button.clicked.connect(self.create_project)
        actions_layout.addWidget(self.new_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        actions_layout.addWidget(self.refresh_button)

        self.layout.addLayout(actions_layout)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tasks by title")
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_tasks)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        self.layout.addLayout(search_layout)

        self.refresh()

    def refresh(self) -> None:
        """Refresh metrics and recent projects."""
        status = self.agent.planner.get_project_status()
        metrics = (
            f"Total: {status['total_tasks']} | "
            f"Completed: {status['completed_tasks']} | "
            f"In Progress: {status['in_progress_tasks']} | "
            f"Blocked: {status['blocked_tasks']}"
        )
        self.metrics_label.setText(metrics)

        self.recent_list.clear()
        docs_dir = self.agent.document_compiler.output_dir
        if os.path.exists(docs_dir):
            for fname in sorted(os.listdir(docs_dir))[-5:]:
                self.recent_list.addItem(fname)

    def create_project(self) -> None:
        """Prompt for a new project description and run it."""
        text, ok = self.simple_input("Enter project description")
        if not ok or not text.strip():
            return
        result = self.agent.execute_task(text)
        if not result.get("success"):
            QMessageBox.critical(self, "Error", result.get("error", "Unknown"))
        self.refresh()

    def search_tasks(self) -> None:
        """Search tasks by title and highlight them."""
        query = self.search_input.text().strip().lower()
        if not query:
            return
        matches = [
            t for t in self.agent.planner.tasks.values()
            if query in t.title.lower()
        ]
        if matches:
            titles = "\n".join(t.title for t in matches)
            QMessageBox.information(self, "Search Results", titles)
        else:
            QMessageBox.information(self, "Search Results", "No matching tasks")

    def simple_input(self, prompt: str) -> tuple[str, bool]:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Input")
        dialog.setText(prompt)
        text_edit = QTextEdit()
        dialog.layout().addWidget(text_edit, 1, 0, 1, dialog.layout().columnCount())
        dialog.addButton(QMessageBox.StandardButton.Ok)
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        result = dialog.exec()
        if result == QMessageBox.StandardButton.Ok.value:
            return text_edit.toPlainText(), True
        return "", False


class TaskBoardTab(QWidget):
    """Kanban-style board showing tasks grouped by status."""

    def __init__(self, agent: EngineeringAgent):
        super().__init__()
        self.agent = agent
        self.layout = QHBoxLayout(self)

        self.columns = {}
        for status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS,
                        TaskStatus.COMPLETED, TaskStatus.FAILED]:
            col = QListWidget()
            col.setMinimumWidth(150)
            self.layout.addWidget(col)
            self.columns[status] = col

        self.refresh()

    def refresh(self) -> None:
        for col in self.columns.values():
            col.clear()
        for task in self.agent.planner.tasks.values():
            item = QListWidgetItem(task.title)
            item.setData(Qt.ItemDataRole.UserRole, task)
            self.columns[task.status].addItem(item)
        for status, col in self.columns.items():
            col.setWindowTitle(status.value.title())
            col.itemClicked.connect(self.show_details)

    def show_details(self, item: QListWidgetItem) -> None:
        task: Task = item.data(Qt.ItemDataRole.UserRole)
        deps = ", ".join(task.dependencies) if task.dependencies else "None"
        text = (
            f"Title: {task.title}\n"
            f"Description: {task.description}\n"
            f"Status: {task.status.value}\n"
            f"Priority: {task.priority.name}\n"
            f"Dependencies: {deps}"
        )
        QMessageBox.information(self, "Task Details", text)


class MainWindow(QWidget):
    def __init__(self, agent: EngineeringAgent):
        super().__init__()
        self.agent = agent
        self.setWindowTitle("Engineering Agent GUI")
        self.resize(800, 600)
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.dashboard = DashboardTab(agent)
        self.board = TaskBoardTab(agent)
        self.tabs.addTab(self.dashboard, "Dashboard")
        self.tabs.addTab(self.board, "Task Board")

        layout.addWidget(self.tabs)

        # Refresh board when dashboard refreshes
        self.dashboard.refresh_button.clicked.connect(self.board.refresh)


def main() -> None:
    app = QApplication([])
    agent = EngineeringAgent()
    window = MainWindow(agent)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
