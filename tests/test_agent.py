"""
Tests for the engineering agent's core functionality.
"""

import os
import pytest
from autonomous_engineering_agent.core.agent import EngineeringAgent
from autonomous_engineering_agent.core.planner import TaskStatus

@pytest.fixture
def agent():
    """Create a test agent instance."""
    return EngineeringAgent(
        ollama_url="http://localhost:11434",
        ollama_model="gemma:3b",
        memory_dir="test_memory",
        docs_dir="test_docs"
    )

@pytest.fixture
def cleanup():
    """Clean up test directories after tests."""
    yield
    for dir_name in ["test_memory", "test_docs"]:
        if os.path.exists(dir_name):
            for root, dirs, files in os.walk(dir_name, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(dir_name)

def test_agent_initialization(agent):
    """Test that the agent initializes correctly."""
    assert agent.ollama_client is not None
    assert agent.memory_manager is not None
    assert agent.planner is not None
    assert agent.reasoner is not None
    assert agent.executor is not None
    assert agent.critique_engine is not None
    assert agent.document_compiler is not None

def test_simple_task_execution(agent, cleanup):
    """Test execution of a simple engineering task."""
    task = """
    Calculate the natural frequency of a simple spring-mass system with:
    - Mass: 1 kg
    - Spring constant: 100 N/m
    """
    
    result = agent.execute_task(task)
    
    assert result["success"] is True
    assert "results" in result
    assert "report" in result
    
    # Check that tasks were created and executed
    assert len(result["results"]) > 0
    
    # Check that at least one task was completed
    completed_tasks = [
        r for r in result["results"]
        if r["task"]["status"] == TaskStatus.COMPLETED
    ]
    assert len(completed_tasks) > 0

def test_memory_management(agent, cleanup):
    """Test that the agent properly manages memory."""
    task = "Calculate the area of a circle with radius 5 meters"
    
    # Execute task
    result = agent.execute_task(task)
    assert result["success"] is True
    
    # Check short-term memory
    short_term_memories = agent.memory_manager.get_recent_short_term(10)
    assert len(short_term_memories) > 0
    
    # Check that project plan was stored
    project_plans = [
        m for m in short_term_memories
        if m["type"] == "project_plan"
    ]
    assert len(project_plans) > 0
    
    # Check that task results were stored
    task_results = [
        m for m in short_term_memories
        if m["type"] == "task_result"
    ]
    assert len(task_results) > 0

def test_error_handling(agent, cleanup):
    """Test that the agent handles errors gracefully."""
    # Test with invalid task
    result = agent.execute_task("")
    assert result["success"] is False
    assert "error" in result
    
    # Test with malformed task
    result = agent.execute_task("This is not a valid engineering task")
    assert result["success"] is False
    assert "error" in result

def test_report_generation(agent, cleanup):
    """Test that the agent generates proper reports."""
    task = """
    Calculate the power output of a wind turbine with:
    - Blade length: 20 meters
    - Wind speed: 10 m/s
    - Air density: 1.225 kg/m³
    - Efficiency: 0.4
    """
    
    result = agent.execute_task(task)
    assert result["success"] is True
    
    # Check that report was generated
    assert os.path.exists(result["report"])
    
    # Check report content
    with open(result["report"], "r") as f:
        content = f.read()
        assert "Project Report" in content
        assert "Task Results" in content
        assert "Analysis and Conclusions" in content

def test_task_validation(agent, cleanup):
    """Test that the agent validates tasks properly."""
    # Test with missing requirements
    task = "Design a bridge"
    result = agent.execute_task(task)
    assert result["success"] is False
    assert "error" in result
    
    # Test with incomplete specifications
    task = """
    Design a bridge with:
    - Length: 100 meters
    """
    result = agent.execute_task(task)
    assert result["success"] is False
    assert "error" in result

def test_optimization_capabilities(agent, cleanup):
    """Test the agent's optimization capabilities."""
    task = """
    Optimize a rectangular beam for minimum weight while supporting:
    - Load: 1000 N
    - Length: 2 meters
    - Material: Steel (E = 200 GPa)
    - Maximum deflection: 5 mm
    
    Constraints:
    - Width between 50mm and 200mm
    - Height between 50mm and 200mm
    """
    
    result = agent.execute_task(task)
    assert result["success"] is True
    
    # Check that optimization was performed
    optimization_tasks = [
        r for r in result["results"]
        if "optimization_result" in r["result"]
    ]
    assert len(optimization_tasks) > 0
    
    # Check optimization results
    for task_result in optimization_tasks:
        opt_result = task_result["result"]["optimization_result"]
        assert "optimal_values" in opt_result
        assert "objective_value" in opt_result
        assert "constraints_satisfied" in opt_result 