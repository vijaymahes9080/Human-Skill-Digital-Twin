import logging
from typing import Dict, Any, Callable

logger = logging.getLogger("PluginSDK")
logger.setLevel(logging.INFO)

class PluginRegistry:
    def __init__(self):
        self.agents: Dict[str, Callable] = {}
        self.algorithms: Dict[str, Callable] = {}
        self.dashboards: Dict[str, Callable] = {}
        self.assessment_engines: Dict[str, Callable] = {}
        self.memory_models: Dict[str, Callable] = {}

    def register_agent(self, name: str):
        """Decorator to register a custom AI Agent."""
        def decorator(func: Callable):
            self.agents[name] = func
            logger.info(f"Registered Plugin Agent: {name}")
            return func
        return decorator

    def register_algorithm(self, name: str):
        """Decorator to register a custom learning path/recommendation algorithm."""
        def decorator(func: Callable):
            self.algorithms[name] = func
            logger.info(f"Registered Plugin Algorithm: {name}")
            return func
        return decorator

    def register_dashboard_view(self, name: str):
        """Decorator to register a custom analytics layout/component."""
        def decorator(func: Callable):
            self.dashboards[name] = func
            logger.info(f"Registered Plugin Dashboard: {name}")
            return func
        return decorator

    def register_assessment_engine(self, name: str):
        """Decorator to register a custom quiz/test compiler."""
        def decorator(func: Callable):
            self.assessment_engines[name] = func
            logger.info(f"Registered Plugin Assessment: {name}")
            return func
        return decorator

    def register_memory_model(self, name: str):
        """Decorator to register a custom memory decay simulator (e.g. Halflife, Leitner)."""
        def decorator(func: Callable):
            self.memory_models[name] = func
            logger.info(f"Registered Plugin Memory Model: {name}")
            return func
        return decorator

# Global SDK Plugin Registry instance
plugin_sdk = PluginRegistry()
