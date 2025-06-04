"""
Example script demonstrating the engineering agent's capabilities for a complex real-world problem.
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
        ollama_model="gemma3:latest",
        memory_dir="memory",
        docs_dir="docs"
    )
    
    # Define a complex engineering task
    task = """
    Design and optimize a solar-powered water pumping system for a rural community with the following requirements:
    
    System Requirements:
    - Daily water demand: 5000 liters
    - Pumping head: 20 meters
    - Water source: Well with static water level at 15 meters
    - Location: Rural area with good solar irradiance (5.5 kWh/m²/day average)
    - System lifetime: 20 years
    - Reliability: 95% uptime
    
    Design Tasks:
    1. Calculate daily energy requirements
    2. Size the solar PV system
    3. Select appropriate pump type and specifications
    4. Design the water storage system
    5. Calculate system efficiency and losses
    6. Perform economic analysis (LCOE, payback period)
    7. Generate system layout and specifications
    8. Create maintenance schedule
    9. Perform reliability analysis
    10. Generate complete technical documentation
    
    Optimization Goals:
    - Minimize system cost while meeting requirements
    - Maximize system efficiency
    - Ensure long-term reliability
    - Minimize maintenance requirements
    
    Constraints:
    - Budget: $15,000 maximum
    - Space available: 50m² for solar panels
    - Local regulations compliance
    - Environmental impact considerations
    """
    
    # Execute the task
    print("Executing complex engineering task...")
    result = agent.execute_task(task)
    
    # Print results
    if result["success"]:
        print("\nTask completed successfully!")
        print(f"Report generated at: {result['report']}")
        
        # Print detailed results
        print("\nDetailed Task Results:")
        for task_result in result["results"]:
            task = task_result["task"]
            print(f"\nTask: {task['title']}")
            print(f"Status: {task['status'].value}")
            print(f"Score: {task_result['review']['overall_score']:.2f}")
            
            # Print key findings
            if "result" in task_result:
                print("\nKey Findings:")
                for key, value in task_result["result"].items():
                    if isinstance(value, (int, float)):
                        print(f"- {key}: {value:.2f}")
                    else:
                        print(f"- {key}: {value}")
            
            # Print improvement suggestions
            if "review" in task_result and task_result["review"].get("improvement_suggestions"):
                print("\nImprovement Suggestions:")
                for suggestion in task_result["review"]["improvement_suggestions"]:
                    print(f"- {suggestion}")
    else:
        print(f"\nTask failed: {result['error']}")

if __name__ == "__main__":
    main() 