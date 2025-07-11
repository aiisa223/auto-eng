from setuptools import setup, find_packages

setup(
    name="autonomous_engineering_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "sympy>=1.12.0",
        "matplotlib>=3.7.0",
        "plotly>=5.18.0",
        "faiss-cpu>=1.7.4",
        "chromadb>=0.4.22",
        "pylatex>=1.4.1",
        "python-docx>=1.0.0",
        "markdown>=3.5.0",
        "pdfkit>=1.0.0",
        "cvxpy>=1.4.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "pytest>=7.4.0",
        "black>=23.12.0",
        "isort>=5.13.0",
        "mypy>=1.8.0"
    ],
    python_requires=">=3.9",
) 