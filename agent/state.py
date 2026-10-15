"""
LangGraph State Definition for DocuDrift Sentinel Agent.
"""

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
import operator

class DocuDriftState(TypedDict):
    """Multi-Agent state passed through the LangGraph workflow."""
    query: str
    intent: str
    cypher_queries: Annotated[List[str], operator.add]
    graph_context: Dict[str, Any]
    external_context: Optional[str]
    drift_detected: bool
    stale_docs: List[Dict[str, Any]]
    orphaned_docs: List[Dict[str, Any]]
    suggested_patch: Optional[str]
    diff_content: Optional[str]
    final_response: str
    intermediate_steps: Annotated[List[str], operator.add]
