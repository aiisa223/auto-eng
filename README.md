# Autonomous Engineering AI Agent

An advanced, fully autonomous AI system powered by Ollama Gemma 3 for executing complex engineering projects with minimal user input.

## Features

- **Autonomous Project Planning**: Breaks down complex objectives into manageable tasks
- **Persistent Memory System**: Short-term and long-term memory using FAISS/ChromaDB
- **Expert Reasoning & Simulation**: Advanced mathematical modeling and simulation capabilities
- **Auto-Code Generation**: Dynamic Python code generation for engineering simulations
- **Self-Critique System**: Autonomous review and improvement of solutions
- **Document Compilation**: Professional-grade technical documentation generation

## Prerequisites

- Python 3.9+
- Ollama with Gemma 3 model installed
- wkhtmltopdf (for PDF generation)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd autonomous-engineering-agent
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Ollama and Gemma 3:
```bash
# Follow instructions at https://ollama.ai to install Ollama
ollama pull gemma:3b
```

## Project Structure

```
autonomous_engineering_agent/
├── core/
│   ├── planner.py          # Task planning and management
│   ├── memory_manager.py   # Memory system implementation
│   ├── reasoner.py         # Core reasoning engine
│   ├── executor.py         # Code execution and validation
│   ├── critique_engine.py  # Self-review system
│   └── document_compiler.py # Documentation generation
├── utils/
│   ├── ollama_client.py    # Ollama API interface
│   ├── code_generator.py   # Code generation utilities
│   └── visualization.py    # Plotting and visualization
├── memory/
│   ├── short_term/        # Short-term memory storage
│   └── long_term/         # Long-term memory storage
├── tests/                 # Test suite
├── examples/             # Example projects
└── docs/                # Documentation
```

## Usage

1. Start the agent:
```bash
python main.py
```

2. Input your engineering task:
```python
task = "Design an advanced fluid delivery system"
agent.execute_task(task)
```

3. The agent will:
   - Plan the project
   - Execute simulations
   - Generate code
   - Create documentation
   - Provide results

### GUI

You can interact with the agent using a minimal PyQt6 GUI:

```bash
python -m autonomous_engineering_agent.gui.simple_gui
```

The GUI provides a dashboard with project metrics and a Kanban style task board.

## Development

- Run tests: `pytest tests/`
- Format code: `black .`
- Type checking: `mypy .`

## License

MIT License

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests. 