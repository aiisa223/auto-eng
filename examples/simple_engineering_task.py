"""
Example script demonstrating how to use the engineering agent for a simple task.
"""

import logging
from autonomous_engineering_agent.core.agent import EngineeringAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Initialize the engineering agent
    agent = EngineeringAgent(
        ollama_url="http://localhost:11434",
        ollama_model="gemma:3b",
        memory_dir="memory",
        docs_dir="docs"
    )
    
    # Define a simple engineering task
    task = """
    Design and analyze a simple cantilever beam with the following specifications:
    - Length: 2 meters
    - Material: Steel (E = 200 GPa)
    - Cross-section: Rectangular (width = 50mm, height = 100mm)
    - Load: 1000 N at the free end
    
    Tasks:
    1. Calculate the maximum deflection
    2. Calculate the maximum stress
    3. Check if the design meets safety requirements (max stress < yield strength)
    4. Generate a visualization of the beam and its deflection
    """
    
    # Execute the task
    print("Executing engineering task...")
    result = agent.execute_task(task)
    
    # Print results
    if result["success"]:
        print("\nTask completed successfully!")
        print(f"Report generated at: {result['report']}")
        
        # Print summary of results
        print("\nTask Results Summary:")
        for task_result in result["results"]:
            task = task_result["task"]
            print(f"\nTask: {task['title']}")
            print(f"Status: {task['status'].value}")
            print(f"Score: {task_result['review']['overall_score']:.2f}")
    else:
        print(f"\nTask failed: {result['error']}")

if __name__ == "__main__":
    main() 