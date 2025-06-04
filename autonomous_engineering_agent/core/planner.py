"""
Task planning and project management system for the autonomous engineering agent.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ..utils.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Status of a task in the project."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class TaskPriority(Enum):
    """Priority level of a task."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """Represents a task in the project."""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    dependencies: Set[str]  # Set of task IDs this task depends on
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "dependencies": list(self.dependencies),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

class ProjectPlanner:
    """Handles task planning and project management."""
    
    def __init__(self, ollama_client: OllamaClient):
        """Initialize the project planner."""
        logger.info("Initializing ProjectPlanner")
        self.ollama_client = ollama_client
        self.tasks: Dict[str, Task] = {}
        self.title_to_id: Dict[str, str] = {}  # Map task titles to IDs
        logger.debug("ProjectPlanner initialized")
        
    def create_project_plan(self, objective: str) -> List[Task]:
        """Create a project plan from a high-level objective."""
        logger.info(f"Creating project plan for objective: {objective}")
        
        # Use Ollama to break down the objective into tasks
        prompt = f"""
        Break down the following engineering objective into specific tasks:
        
        Objective: {objective}
        
        For each task, provide:
        1. A clear title
        2. A detailed description
        3. Priority level (LOW, MEDIUM, HIGH, CRITICAL)
        4. Dependencies on other tasks (if any)
        
        Format the response as a JSON array of task objects with the following structure:
        [
            {{
                "title": "Task title",
                "description": "Detailed task description",
                "priority": "HIGH",
                "dependencies": []
            }}
        ]
        """
        
        logger.debug("Sending prompt to Ollama for task breakdown")
        response = self.ollama_client.generate(prompt)
        logger.debug(f"Received response from Ollama: {response}")
        
        try:
            # Extract the JSON array from the response
            response_text = response.get("response", "[]")
            logger.debug(f"Raw response text: {response_text}")
            
            # Find the first [ and last ] to extract the JSON array
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx == -1 or end_idx == 0:
                logger.error("No JSON array found in response")
                raise ValueError("No JSON array found in response")
            
            json_str = response_text[start_idx:end_idx]
            logger.debug(f"Extracted JSON string: {json_str}")
            
            tasks_data = json.loads(json_str)
            logger.debug(f"Parsed tasks data: {tasks_data}")
            
            # First pass: Create all tasks without dependencies
            tasks = []
            for task_data in tasks_data:
                task_id = f"task_{len(self.tasks)}"
                logger.debug(f"Creating task from data: {task_data}")
                task = Task(
                    id=task_id,
                    title=task_data["title"],
                    description=task_data["description"],
                    status=TaskStatus.PENDING,
                    priority=TaskPriority[task_data["priority"]],
                    dependencies=set(),  # Initialize empty dependencies
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    metadata=task_data.get("metadata", {})
                )
                self.tasks[task.id] = task
                self.title_to_id[task.title] = task.id
                tasks.append(task)
                logger.debug(f"Created task: {task.title} (ID: {task.id})")
            
            # Second pass: Add dependencies using task IDs
            for task_data, task in zip(tasks_data, tasks):
                if "dependencies" in task_data:
                    # Convert dependency titles to IDs
                    dependency_ids = set()
                    for dep_title in task_data["dependencies"]:
                        if dep_title in self.title_to_id:
                            dependency_ids.add(self.title_to_id[dep_title])
                        else:
                            logger.warning(f"Dependency task '{dep_title}' not found")
                    task.dependencies = dependency_ids
                    logger.debug(f"Added dependencies for task {task.id}: {dependency_ids}")
                
            logger.info(f"Successfully created {len(tasks)} tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Error parsing task data: {str(e)}", exc_info=True)
            # Create a single default task if parsing fails
            logger.info("Creating default task due to parsing error")
            default_task = Task(
                id="task_0",
                title="Main Task",
                description=objective,
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                dependencies=set(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={}
            )
            self.tasks[default_task.id] = default_task
            self.title_to_id[default_task.title] = default_task.id
            logger.debug(f"Created default task: {default_task.title} (ID: {default_task.id})")
            return [default_task]
        
    def get_next_tasks(self) -> List[Task]:
        """Get the next tasks that can be executed."""
        logger.debug("Getting next tasks to execute")
        ready_tasks = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                if all(
                    self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                ):
                    ready_tasks.append(task)
                    logger.debug(f"Task {task.id} is ready for execution")
                else:
                    logger.debug(f"Task {task.id} has pending dependencies")
                    
        # Sort by priority (highest first)
        sorted_tasks = sorted(ready_tasks, key=lambda t: t.priority.value, reverse=True)
        logger.info(f"Found {len(sorted_tasks)} ready tasks")
        return sorted_tasks
        
    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update the status of a task."""
        logger.debug(f"Updating task {task_id} status to {status.value}")
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = status
            task.updated_at = datetime.now()
            logger.debug(f"Task {task_id} status updated successfully")
        else:
            logger.warning(f"Task {task_id} not found")
            
    def get_task_dependencies(self, task_id: str) -> List[Task]:
        """Get all dependencies of a task."""
        logger.debug(f"Getting dependencies for task {task_id}")
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found")
            return []
            
        dependencies = [
            self.tasks[dep_id]
            for dep_id in self.tasks[task_id].dependencies
            if dep_id in self.tasks
        ]
        logger.debug(f"Found {len(dependencies)} dependencies for task {task_id}")
        return dependencies
        
    def get_blocked_tasks(self) -> List[Task]:
        """Get all tasks that are blocked by dependencies."""
        logger.debug("Getting blocked tasks")
        blocked_tasks = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                # Check if any dependency is not completed
                if any(
                    self.tasks[dep_id].status != TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                ):
                    blocked_tasks.append(task)
                    logger.debug(f"Task {task.id} is blocked")
                    
        logger.info(f"Found {len(blocked_tasks)} blocked tasks")
        return blocked_tasks
        
    def get_project_status(self) -> Dict[str, Any]:
        """Get the current status of the project."""
        logger.debug("Getting project status")
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        blocked = sum(1 for t in self.tasks.values() if t.status == TaskStatus.BLOCKED)
        
        status = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress,
            "blocked_tasks": blocked,
            "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
        logger.debug(f"Project status: {status}")
        return status 