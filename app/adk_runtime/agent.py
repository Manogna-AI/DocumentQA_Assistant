"""DocQA Assistant — ADK Entry Point. Exports root_agent."""

from .orchestrator import orchestrator

# Orchestrator IS the root_agent
root_agent = orchestrator
