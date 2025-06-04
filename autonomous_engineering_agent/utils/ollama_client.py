"""
Client for interacting with Ollama API.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str, model: str):
        """Initialize the Ollama client.
        
        Args:
            base_url: Base URL for Ollama API
            model: Model name to use
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        logger.info(f"Initialized OllamaClient with model: {model}")
        
    def check_model_availability(self) -> bool:
        """Check if the specified model is available.
        
        Returns:
            True if model is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model["name"] == self.model for model in models)
            return False
        except Exception as e:
            logger.error(f"Error checking model availability: {str(e)}")
            return False
            
    def generate(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response using the Ollama model.
        
        Args:
            prompt: Input prompt
            system: Optional system message
            
        Returns:
            Generated response
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            if system:
                payload["system"] = system
                
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error generating response: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Error in generate: {str(e)}")
            return {"error": str(e)}
            
    def analyze(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze text using the Ollama model.
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis results
        """
        prompt = f"""
        Analyze the following text for {analysis_type}:
        
        {text}
        
        Provide a detailed analysis in JSON format with the following structure:
        {{
            "analysis": {{
                "key_points": [],
                "findings": [],
                "recommendations": []
            }},
            "score": 0.0,
            "confidence": 0.0
        }}
        """
        
        response = self.generate(prompt)
        if "error" in response:
            return response
            
        try:
            # Extract JSON from response
            response_text = response.get("response", "")
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            return {"error": "Could not parse JSON from response"}
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            return {"error": str(e)}
            
    def optimize(self, objective: str, constraints: list, variables: list) -> Dict[str, Any]:
        """Optimize a design using the Ollama model.
        
        Args:
            objective: Optimization objective
            constraints: List of constraints
            variables: List of variables to optimize
            
        Returns:
            Optimization results
        """
        prompt = f"""
        Optimize the following design:
        
        Objective: {objective}
        Constraints: {constraints}
        Variables: {variables}
        
        Provide optimization results in JSON format with the following structure:
        {{
            "optimal_values": {{}},
            "objective_value": 0.0,
            "constraint_satisfaction": [],
            "iterations": 0
        }}
        """
        
        response = self.generate(prompt)
        if "error" in response:
            return response
            
        try:
            # Extract JSON from response
            response_text = response.get("response", "")
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            return {"error": "Could not parse JSON from response"}
        except Exception as e:
            logger.error(f"Error parsing optimization response: {str(e)}")
            return {"error": str(e)} 