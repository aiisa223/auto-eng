"""
Command-line interface for running engineering tasks.
"""

import argparse
import logging
from autonomous_engineering_agent.core.agent import EngineeringAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the command-line interface."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run an engineering task")
    parser.add_argument("task", help="Description of the engineering task to execute")
    args = parser.parse_args()
    
    # Initialize the engineering agent
    agent = EngineeringAgent(
        ollama_url="http://localhost:11434",
        ollama_model="gemma3:latest",
        memory_dir="memory",
        docs_dir="docs"
    )
    
    # Execute the task
    logger.info(f"Executing task: {args.task}")
    result = agent.execute_task(args.task)
    
    if result["success"]:
        print("\nTask completed successfully!")
        print(f"Report generated at: {result['report']}\n")
        
        print("Detailed Task Results:")
        for task_result in result["results"]:
            task = task_result["task"]
            print(f"\nTask: {task['title']}")
            # Handle status which could be either a string or TaskStatus enum
            status = task['status']
            if isinstance(status, str):
                print(f"Status: {status}")
            else:
                print(f"Status: {status.value}")
            print(f"Description: {task['description']}")
            
            if "result" in task_result:
                print("\nResults:")
                result_data = task_result["result"]
                if isinstance(result_data, dict):
                    for key, value in result_data.items():
                        print(f"- {key}: {value}")
                elif isinstance(result_data, (list, tuple)):
                    for item in result_data:
                        print(f"- {item}")
                else:
                    print(f"- {result_data}")
                    
            if "review" in task_result:
                print("\nReview:")
                review = task_result["review"]
                if isinstance(review, dict):
                    print(f"- Overall Score: {review.get('overall_score', 'N/A')}")
                    if review.get("improvement_suggestions"):
                        print("- Improvement Suggestions:")
                        for suggestion in review["improvement_suggestions"]:
                            print(f"  * {suggestion}")
                else:
                    print(f"- {review}")
    else:
        print(f"\nTask failed: {result['error']}")

if __name__ == "__main__":
    main() 