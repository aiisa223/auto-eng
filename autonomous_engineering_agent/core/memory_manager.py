"""
Memory management system for the autonomous engineering agent.
Handles both short-term and long-term memory using FAISS and ChromaDB.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import chromadb
import faiss
import numpy as np
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages both short-term and long-term memory for the agent."""
    
    def __init__(self, memory_dir: str = "memory"):
        """Initialize the memory manager.
        
        Args:
            memory_dir: Directory to store memory files
        """
        self.memory_dir = memory_dir
        self.short_term_dir = os.path.join(memory_dir, "short_term")
        self.long_term_dir = os.path.join(memory_dir, "long_term")
        
        # Create directories if they don't exist
        os.makedirs(self.short_term_dir, exist_ok=True)
        os.makedirs(self.long_term_dir, exist_ok=True)
        
        # Initialize short-term memory
        self.short_term_memory: List[Dict[str, Any]] = []
        self.short_term_index = faiss.IndexFlatL2(384)  # Using 384-dim vectors for embeddings
        
        # Initialize long-term memory (ChromaDB)
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=self.long_term_dir,
            anonymized_telemetry=False
        ))
        self.long_term_collection = self.chroma_client.get_or_create_collection(
            name="engineering_memory",
            metadata={"description": "Long-term memory for engineering projects"}
        )
        
    def add_to_short_term(self, 
                         content: Dict[str, Any],
                         embedding: Optional[np.ndarray] = None) -> None:
        """Add an item to short-term memory.
        
        Args:
            content: The content to store
            embedding: Optional vector embedding for similarity search
        """
        timestamp = datetime.now().isoformat()
        memory_item = {
            "content": content,
            "timestamp": timestamp,
            "type": content.get("type", "general")
        }
        
        self.short_term_memory.append(memory_item)
        
        if embedding is not None:
            self.short_term_index.add(embedding.reshape(1, -1))
            
        # Save to disk
        self._save_short_term_memory()
        
    def get_recent_short_term(self, 
                            n: int = 10,
                            memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent items from short-term memory.
        
        Args:
            n: Number of items to retrieve
            memory_type: Optional filter by memory type
            
        Returns:
            List of recent memory items
        """
        if memory_type:
            filtered_memory = [
                item for item in self.short_term_memory 
                if item["type"] == memory_type
            ]
        else:
            filtered_memory = self.short_term_memory
            
        return filtered_memory[-n:]
        
    def search_short_term(self,
                         query_embedding: np.ndarray,
                         k: int = 5) -> List[Dict[str, Any]]:
        """Search short-term memory using vector similarity.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            List of similar memory items
        """
        if self.short_term_index.ntotal == 0:
            return []
            
        distances, indices = self.short_term_index.search(
            query_embedding.reshape(1, -1), k
        )
        
        return [self.short_term_memory[i] for i in indices[0]]
        
    def add_to_long_term(self,
                        content: Dict[str, Any],
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add an item to long-term memory.
        
        Args:
            content: The content to store
            metadata: Optional metadata for the item
            
        Returns:
            ID of the stored item
        """
        if metadata is None:
            metadata = {}
            
        # Generate a unique ID
        item_id = f"{datetime.now().timestamp()}_{len(self.long_term_collection.get()['ids'])}"
        
        # Store in ChromaDB
        self.long_term_collection.add(
            documents=[json.dumps(content)],
            metadatas=[metadata],
            ids=[item_id]
        )
        
        return item_id
        
    def search_long_term(self,
                        query: str,
                        n_results: int = 5,
                        where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search long-term memory.
        
        Args:
            query: Search query
            n_results: Number of results to return
            where: Optional filter conditions
            
        Returns:
            List of matching memory items
        """
        results = self.long_term_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        return [
            {
                "id": id_,
                "content": json.loads(doc),
                "metadata": metadata
            }
            for id_, doc, metadata in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0]
            )
        ]
        
    def _save_short_term_memory(self) -> None:
        """Save short-term memory to disk."""
        memory_file = os.path.join(self.short_term_dir, "short_term_memory.json")
        with open(memory_file, "w") as f:
            json.dump(self.short_term_memory, f)
            
    def _load_short_term_memory(self) -> None:
        """Load short-term memory from disk."""
        memory_file = os.path.join(self.short_term_dir, "short_term_memory.json")
        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
                self.short_term_memory = json.load(f)
                
    def clear_short_term_memory(self) -> None:
        """Clear short-term memory."""
        self.short_term_memory = []
        self.short_term_index = faiss.IndexFlatL2(384)
        self._save_short_term_memory() 