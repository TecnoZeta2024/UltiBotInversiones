"""
Base MCP Adapter - Re-export para conveniencia.

Este módulo simplemente re-exporta la clase BaseMCPAdapter del core
para facilitar las importaciones en los adaptadores específicos.
"""

from ...core.services.mcp_tool_hub import BaseMCPAdapter

__all__ = ["BaseMCPAdapter"]
