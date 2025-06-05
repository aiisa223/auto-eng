"""
Main agent class that coordinates all components of the autonomous engineering system.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .critique_engine import CritiqueEngine
from .document_compiler import DocumentCompiler
from .executor import CodeExecutor
from .memory_manager import MemoryManager
from .planner import ProjectPlanner, Task, TaskStatus
from .reasoner import EngineeringReasoner
from ..utils.ollama_client import OllamaClient

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EngineeringAgent:
    """Main agent class that coordinates all components."""
    
    def __init__(self,
                 ollama_url: str = "http://localhost:11434",
                 ollama_model: str = "gemma3:latest",
                 memory_dir: str = "memory",
                 docs_dir: str = "docs"):
        """Initialize the engineering agent.
        
        Args:
            ollama_url: URL for the Ollama API
            ollama_model: Model to use with Ollama
            memory_dir: Directory for memory storage
            docs_dir: Directory for document storage
        """
        logger.info(f"Initializing EngineeringAgent with model: {ollama_model}")
        
        # Initialize components
        logger.debug("Initializing OllamaClient...")
        self.ollama_client = OllamaClient(ollama_url, ollama_model)
        
        logger.debug("Initializing MemoryManager...")
        self.memory_manager = MemoryManager(memory_dir)
        
        logger.debug("Initializing ProjectPlanner...")
        self.planner = ProjectPlanner(self.ollama_client)
        
        logger.debug("Initializing EngineeringReasoner...")
        self.reasoner = EngineeringReasoner(self.ollama_client)
        
        logger.debug("Initializing CodeExecutor...")
        self.executor = CodeExecutor()
        
        logger.debug("Initializing CritiqueEngine...")
        self.critique_engine = CritiqueEngine(self.ollama_client)
        
        logger.debug("Initializing DocumentCompiler...")
        self.document_compiler = DocumentCompiler(docs_dir)
        
        # Check if Ollama is available
        logger.debug("Checking Ollama model availability...")
        if not self.ollama_client.check_model_availability():
            error_msg = f"Ollama model {ollama_model} is not available"
            logger.error(error_msg)
            raise RuntimeError(
                f"{error_msg}. Please install it using 'ollama pull {ollama_model}'"
            )
        logger.info("EngineeringAgent initialization complete")
            
    def execute_task(self, task_input: str) -> Dict[str, Any]:
        """Execute an engineering task.
        
        Args:
            task_input: High-level task description as a string
            
        Returns:
            Task execution results
        """
        logger.info(f"Starting task execution: {task_input}")
        max_attempts = 3  # Maximum number of attempts per task
        attempt = 0
        previous_attempts = []  # Store previous attempts and their feedback
        
        while attempt < max_attempts:
            attempt += 1
            logger.info(f"Attempt {attempt} of {max_attempts}")
            
            try:
                # Create a Task object from the input string
                current_time = datetime.now()
                logger.debug("Creating main task object...")
                task = Task(
                    id="main_task",
                    title="Main Engineering Task",
                    description=task_input,
                    status=TaskStatus.PENDING,
                    priority=1,  # Highest priority
                    dependencies=[],  # No dependencies for main task
                    created_at=current_time,
                    updated_at=current_time,
                    metadata={
                        "requirements": {},
                        "analysis_type": "general",
                        "requires_code": True,
                        "system_type": "structural",
                        "parameters": {},
                        "previous_attempts": previous_attempts  # Include previous attempts in metadata
                    }
                )
                logger.debug(f"Main task created with ID: {task.id}")
                
                # Create project plan
                logger.info("Creating project plan...")
                tasks = self.planner.create_project_plan(task_input)
                logger.info(f"Created project plan with {len(tasks)} tasks")
                
                # Execute tasks
                logger.info("Starting task execution loop...")
                results = []
                for task in tasks:
                    result = self._execute_single_task(task)
                    results.append(result)
                    
                    # Store task result in memory
                    logger.debug("Storing task result in memory...")
                    self.memory_manager.add_to_short_term({
                        "type": "task_result",
                        "content": {
                            "task_id": task.id,
                            "result": result
                        }
                    })
                    
                    # Review the result
                    logger.debug("Reviewing task result...")
                    review = self.critique_engine.review_solution(
                        result,
                        task.metadata.get("requirements", {})
                    )
                    
                    # Check if the task passed
                    if review.get("overall_score", 0) >= 0.7:  # Threshold for passing
                        logger.info(f"Task {task.id} passed with score {review.get('overall_score')}")
                        self.planner.update_task_status(task.id, TaskStatus.COMPLETED)
                    else:
                        logger.warning(f"Task {task.id} failed to meet requirements")
                        self.planner.update_task_status(task.id, TaskStatus.FAILED)
                        
                        # Store the attempt and its feedback for learning
                        previous_attempts.append({
                            "attempt": attempt,
                            "result": result,
                            "review": review,
                            "improvement_suggestions": review.get("improvement_suggestions", [])
                        })
                        
                        # If this was the last attempt, break the loop
                        if attempt == max_attempts:
                            break
                            
                        # Otherwise, prepare for next attempt
                        logger.info("Preparing for next attempt with improvements...")
                        # Use the improvement suggestions to modify the task
                        if review.get("improvement_suggestions"):
                            task_input = self._incorporate_improvements(
                                task_input,
                                review.get("improvement_suggestions", [])
                            )
                        continue
                
                # If we get here, all tasks passed
                if all(r.get("overall_score", 0) >= 0.7 for r in results):
                    logger.info("All tasks completed successfully")
                    return {
                        "success": True,
                        "results": results,
                        "attempts": attempt
                    }
                    
            except Exception as e:
                logger.error(f"Error executing task: {str(e)}", exc_info=True)
                if attempt == max_attempts:
                    return {
                        "success": False,
                        "error": str(e),
                        "attempts": attempt
                    }
                continue
                
        return {
            "success": False,
            "error": "Maximum attempts reached without success",
            "attempts": max_attempts,
            "previous_attempts": previous_attempts
        }
        
    def _execute_single_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            Task execution result
        """
        logger.debug(f"Starting execution of task: {task.title}")
        
        try:
            # Analyze the task
            logger.debug("Analyzing task...")
            analysis = self.reasoner.analyze_system(
                task.description,
                task.metadata.get("analysis_type", "general")
            )
            logger.debug(f"Analysis result: {analysis}")
            
            # Generate code if needed
            if task.metadata.get("requires_code", False):
                logger.debug("Generating simulation code...")
                code = self.reasoner.generate_simulation_code(
                    task.metadata.get("system_type", "general"),
                    task.metadata.get("parameters", {})
                )
                logger.debug(f"Generated code: {code}")
                
                # Validate and execute code
                logger.debug("Validating code...")
                is_valid, issues = self.executor.validate_code(code)
                if not is_valid:
                    logger.error(f"Code validation failed: {issues}")
                    raise ValueError(f"Generated code is invalid: {issues}")
                    
                logger.debug("Executing code...")
                success, output, result = self.executor.execute_code(code)
                if not success:
                    logger.error(f"Code execution failed: {output}")
                    raise RuntimeError(f"Code execution failed: {output}")
                    
                analysis["code_result"] = result
                logger.debug(f"Code execution result: {result}")
                
            # Optimize if needed
            if task.metadata.get("requires_optimization", False):
                logger.debug("Starting optimization...")
                optimization_result = self.reasoner.optimize_design(
                    task.metadata.get("objective", ""),
                    task.metadata.get("constraints", []),
                    task.metadata.get("variables", []),
                    task.metadata.get("bounds", None)
                )
                analysis["optimization_result"] = optimization_result
                logger.debug(f"Optimization result: {optimization_result}")
            
            # Review the solution
            logger.debug("Reviewing solution...")
            review = self.critique_engine.review_solution(
                analysis,
                task.metadata.get("requirements", {})
            )
            logger.debug(f"Review result: {review}")
            
            # Update task status based on review
            if review.get("overall_score", 0) >= 0.8:
                logger.info(f"Task {task.id} completed successfully")
                self.planner.update_task_status(task.id, TaskStatus.COMPLETED)
            else:
                logger.warning(f"Task {task.id} failed to meet requirements")
                self.planner.update_task_status(task.id, TaskStatus.FAILED)
            
            # Combine analysis and review
            result = {
                "analysis": analysis,
                "review": review
            }
            
            logger.debug(f"Task execution complete: {task.title}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing task {task.id}: {str(e)}", exc_info=True)
            self.planner.update_task_status(task.id, TaskStatus.FAILED)
            return {
                "error": str(e),
                "analysis": {},
                "review": {
                    "overall_score": 0.0,
                    "improvement_suggestions": [f"Task failed: {str(e)}"]
                }
            }
        
    def _generate_final_report(self,
                             original_task: str,
                             results: List[Dict[str, Any]]) -> str:
        """Generate the final project report.
        
        Args:
            original_task: Original task description
            results: List of task results
            
        Returns:
            Path to the generated report
        """
        # Prepare report content
        content = {
            "title": f"Project Report: {original_task}",
            "author": "Engineering AI",
            "sections": [
                {
                    "title": "Project Overview",
                    "content": f"Original Task: {original_task}\n\n"
                              f"Total Tasks: {len(results)}\n"
                              f"Completed Tasks: {len([r for r in results if r['task']['status'] == 'completed'])}"
                },
                {
                    "title": "Task Results",
                    "content": self._format_task_results(results)
                },
                {
                    "title": "Analysis and Conclusions",
                    "content": self._generate_conclusions(results)
                }
            ]
        }
        
        # Generate the report in markdown format
        return self.document_compiler.generate_report(content, "md")
        
    def _format_task_results(self, results: List[Dict[str, Any]]) -> str:
        """Format task results for the report.
        
        Args:
            results: List of task results
            
        Returns:
            Formatted results text
        """
        text = ""
        for result in results:
            task = result["task"]
            text += f"### {task['title']}\n\n"
            # Handle status which could be either a string or TaskStatus enum
            status = task['status']
            if isinstance(status, str):
                text += f"Status: {status}\n\n"
            else:
                text += f"Status: {status.value}\n\n"
            
            text += f"Description: {task['description']}\n\n"
            
            if "result" in result:
                text += "Results:\n"
                result_data = result["result"]
                if isinstance(result_data, dict):
                    for key, value in result_data.items():
                        text += f"- {key}: {value}\n"
                elif isinstance(result_data, (list, tuple)):
                    for item in result_data:
                        text += f"- {item}\n"
                else:
                    text += f"- {result_data}\n"
                text += "\n"
                
            if "review" in result:
                text += "Review:\n"
                review = result["review"]
                if isinstance(review, dict):
                    text += f"- Overall Score: {review.get('overall_score', 'N/A')}\n"
                    if review.get("improvement_suggestions"):
                        text += "- Improvement Suggestions:\n"
                        for suggestion in review["improvement_suggestions"]:
                            text += f"  * {suggestion}\n"
                else:
                    text += f"- {review}\n"
                text += "\n"
                
        return text
        
    def _generate_conclusions(self, results: List[Dict[str, Any]]) -> str:
        """Generate conclusions from task results.
        
        Args:
            results: List of task results
            
        Returns:
            Conclusions text
        """
        # Use Ollama to generate conclusions
        prompt = f"""
        Analyze the following engineering project results and generate conclusions:
        
        {results}
        
        Consider:
        1. Overall project success
        2. Key findings and insights
        3. Potential improvements
        4. Recommendations for future work
        
        Format the response as a structured text with sections.
        """
        
        response = self.ollama_client.generate(prompt)
        return response.get("response", "")
        
    def _incorporate_improvements(self,
                                task_input: str,
                                improvements: List[str]) -> str:
        """Incorporate improvement suggestions into the task input.
        
        Args:
            task_input: Original task input
            improvements: List of improvement suggestions
            
        Returns:
            Modified task input
        """
        prompt = f"""
        Original task: {task_input}
        
        Improvement suggestions from previous attempt:
        {chr(10).join(f'- {imp}' for imp in improvements)}
        
        Please modify the task to address these improvements while maintaining the original requirements.
        Focus on making the task more specific and addressing the identified issues.
        """
        
        response = self.ollama_client.generate(prompt)
        modified_task = response.get("response", task_input)
        
        logger.info(f"Modified task input: {modified_task}")
        return modified_task 