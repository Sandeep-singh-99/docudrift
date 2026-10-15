import os
import re
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class FalkorDBResultMock:
    """Mock result set that mirrors falkordb-py result structure."""
    def __init__(self, result_set: List[List[Any]], header: Optional[List[str]] = None):
        self.result_set = result_set
        self.header = header or []

    def __iter__(self):
        return iter(self.result_set)

    def __len__(self):
        return len(self.result_set)


class InMemoryFalkorFallback:
    """
    Robust in-memory fallback store simulating FalkorDB graph behavior.
    Ensures that DocuDrift runs out of the box even before `docker compose up` is started.
    """
    def __init__(self, graph_name: str = "DocuDrift"):
        self.graph_name = graph_name
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []

    def select_graph(self):
        return self

    def query(self, query_str: str, params: Optional[Dict[str, Any]] = None) -> FalkorDBResultMock:
        q = query_str.strip()

        # Handle simple MATCH queries by pattern or return all
        if "MATCH (d:Developer" in q and "LEFT_COMPANY" in q:
            # Query for orphaned knowledge
            orphaned = []
            for n_id, n in self.nodes.items():
                if n.get("label") == "Developer" and n.get("status") == "inactive":
                    dev_name = n.get("name")
                    # find docs authored by this dev
                    for edge in self.edges:
                        if edge.get("type") == "AUTHORED_BY" and edge.get("target") == n_id:
                            doc = self.nodes.get(edge.get("source"), {})
                            doc_id = doc.get("id")
                            # check if doc has other active authors
                            authors = [e.get("target") for e in self.edges if e.get("type") == "AUTHORED_BY" and e.get("source") == doc_id]
                            active_authors = [aid for aid in authors if self.nodes.get(aid, {}).get("status") == "active"]
                            if len(active_authors) == 0:
                                orphaned.append([
                                    doc.get("title", "Untitled"),
                                    doc.get("id", ""),
                                    dev_name,
                                    doc.get("last_updated", ""),
                                    doc.get("service", "Unknown")
                                ])
            return FalkorDBResultMock(orphaned, ["doc_title", "doc_id", "author_name", "last_updated", "service_name"])

        if "stale" in q.lower() or "drift" in q.lower() or "FLAGGED_STALE" in q:
            # Return alerts or stale docs
            rows = []
            for n_id, n in self.nodes.items():
                if n.get("label") == "Alert":
                    rows.append([
                        n.get("id"),
                        n.get("doc_id"),
                        n.get("reason"),
                        n.get("severity"),
                        n.get("created_at"),
                        n.get("suggested_patch")
                    ])
            return FalkorDBResultMock(rows, ["id", "doc_id", "reason", "severity", "created_at", "suggested_patch"])

        if "RETURN count(n)" in q or "count(*)" in q:
            return FalkorDBResultMock([[len(self.nodes)]], ["count"])

        # Default fallback: return all nodes or empty
        rows = []
        for n_id, n in self.nodes.items():
            rows.append([n])
        return FalkorDBResultMock(rows, ["node"])


class FalkorDBManager:
    """Singleton manager for connecting to FalkorDB or falling back gracefully."""
    def __init__(self):
        self.host = os.getenv("FALKORDB_HOST", "localhost")
        self.port = int(os.getenv("FALKORDB_PORT", "6379"))
        self.password = os.getenv("FALKORDB_PASSWORD", None) or None
        self.graph_name = os.getenv("FALKORDB_GRAPH_NAME", "DocuDrift")
        self.client = None
        self.graph = None
        self.is_connected = False
        self.is_fallback = False
        self._fallback_instance = InMemoryFalkorFallback(self.graph_name)
        self.connect()

    def connect(self) -> bool:
        try:
            import falkordb
            self.client = falkordb.FalkorDB(
                host=self.host,
                port=self.port,
                password=self.password
            )
            # Test ping
            self.graph = self.client.select_graph(self.graph_name)
            # Try a lightweight query to verify connectivity
            self.graph.query("RETURN 1 AS ping")
            self.is_connected = True
            self.is_fallback = False
            return True
        except Exception:
            self.is_connected = False
            self.is_fallback = True
            self.graph = self._fallback_instance
            return False

    def query(self, cypher_query: str, params: Optional[Dict[str, Any]] = None):
        """Execute a Cypher query on FalkorDB or the fallback engine."""
        if not self.is_connected or self.is_fallback:
            # Try reconnecting in case Docker just spun up
            if self.connect():
                return self.graph.query(cypher_query, params)
            return self._fallback_instance.query(cypher_query, params)
        try:
            return self.graph.query(cypher_query, params)
        except Exception as e:
            # If connection dropped, retry once
            if self.connect():
                return self.graph.query(cypher_query, params)
            raise e

    def get_status(self) -> Dict[str, Any]:
        return {
            "connected": self.is_connected,
            "is_fallback": self.is_fallback,
            "host": self.host,
            "port": self.port,
            "graph_name": self.graph_name,
            "mode": "FalkorDB (Live Server)" if self.is_connected else "FalkorDB In-Memory Standby Engine"
        }

# Global singleton
db_manager = FalkorDBManager()
