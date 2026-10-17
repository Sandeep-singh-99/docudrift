import os
import re
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class FalkorDBResultWrapper:
    """
    Universal wrapper ensuring full compatibility between live falkordb.QueryResult,
    FalkorDBResultMock, and standard Python iterable/sequence interfaces.
    """
    def __init__(self, raw_result: Any):
        if hasattr(raw_result, "result_set"):
            self.result_set = raw_result.result_set if raw_result.result_set is not None else []
            self.header = getattr(raw_result, "header", []) or []
        elif isinstance(raw_result, list):
            self.result_set = raw_result
            self.header = []
        else:
            self.result_set = []
            self.header = []

    def __iter__(self):
        return iter(self.result_set)

    def __len__(self):
        return len(self.result_set)

    def __getitem__(self, idx):
        return self.result_set[idx]

    def __bool__(self):
        return len(self.result_set) > 0

    def __repr__(self):
        return f"FalkorDBResultWrapper(rows={len(self.result_set)}, header={self.header})"


class FalkorDBResultMock:
    """Mock result set that mirrors falkordb-py result structure."""
    def __init__(self, result_set: List[List[Any]], header: Optional[List[str]] = None):
        self.result_set = result_set or []
        self.header = header or []

    def __iter__(self):
        return iter(self.result_set)

    def __len__(self):
        return len(self.result_set)

    def __getitem__(self, idx):
        return self.result_set[idx]

    def __bool__(self):
        return len(self.result_set) > 0


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
        params = params or {}

        # 0. DETACH DELETE
        if "DETACH DELETE" in q:
            self.nodes.clear()
            self.edges.clear()
            return FalkorDBResultMock([], ["result"])

        # 1. Ping / simple return
        if q == "RETURN 1 AS ping" or q == "RETURN 1":
            return FalkorDBResultMock([[1]], ["ping"])

        # 2. Count queries
        if "count(n)" in q.lower() or "count(*)" in q.lower():
            return FalkorDBResultMock([[len(self.nodes)]], ["count"])

        # 3. Sample query: Developer listing
        if "MATCH (d:Developer)" in q and "status" in q:
            rows = []
            for n in self.nodes.values():
                if n.get("label") == "Developer":
                    rows.append([n.get("name"), n.get("email"), n.get("status")])
            return FalkorDBResultMock(rows, ["d.name", "d.email", "d.status"])

        # 4. Sample query: Docs -> Services
        if "[:DOCUMENTS]->" in q:
            rows = []
            for edge in self.edges:
                if edge.get("type") == "DOCUMENTS":
                    doc = self.nodes.get(edge.get("source"), {})
                    srv = self.nodes.get(edge.get("target"), {})
                    rows.append([doc.get("title", "Untitled"), srv.get("name", "Unknown"), doc.get("last_updated", "")])
            return FalkorDBResultMock(rows, ["doc.title", "s.name", "doc.last_updated"])

        # 5. Sample query: PRs -> Services
        if "[:MODIFIED]->" in q:
            rows = []
            for edge in self.edges:
                if edge.get("type") == "MODIFIED":
                    pr = self.nodes.get(edge.get("source"), {})
                    srv = self.nodes.get(edge.get("target"), {})
                    rows.append([pr.get("number", 0), pr.get("title", ""), srv.get("name", "Unknown")])
            return FalkorDBResultMock(rows, ["pr.number", "pr.title", "s.name"])

        # 6. Sample query: Docs -> Endpoints
        if "[:REFERENCES]->" in q:
            rows = []
            for edge in self.edges:
                if edge.get("type") == "REFERENCES":
                    doc = self.nodes.get(edge.get("source"), {})
                    ep = self.nodes.get(edge.get("target"), {})
                    rows.append([doc.get("title", "Untitled"), ep.get("path", ""), ep.get("deprecated", False)])
            return FalkorDBResultMock(rows, ["doc.title", "ep.path", "ep.deprecated"])

        # 7. Query all nodes for visualization
        if "labels(n)" in q and "properties(n)" in q:
            rows = []
            for n_id, n in self.nodes.items():
                lbl = [n.get("label", "Node")]
                props = {k: v for k, v in n.items() if k != "label"}
                rows.append([lbl, props])
            return FalkorDBResultMock(rows, ["labels", "props"])

        # 8. Query all edges for visualization
        if "-[r]->" in q and "source_label" in q:
            rows = []
            for idx, edge in enumerate(self.edges):
                src_id = edge.get("source")
                tgt_id = edge.get("target")
                src = self.nodes.get(src_id, {})
                tgt = self.nodes.get(tgt_id, {})
                rows.append([
                    idx,
                    src.get("label", "Node"),
                    src_id,
                    src.get("name", ""),
                    src.get("title", ""),
                    edge.get("type", "RELATED_TO"),
                    {},
                    idx + 1000,
                    tgt.get("label", "Node"),
                    tgt_id,
                    tgt.get("name", ""),
                    tgt.get("title", "")
                ])
            return FalkorDBResultMock(rows, ["source_id", "source_label", "source_business_id", "source_name", "source_title", "rel_type", "rel_props", "target_id", "target_label", "target_business_id", "target_name", "target_title"])

        # 9. Orphaned knowledge query
        if "MATCH (d:Developer" in q and "LEFT_COMPANY" in q or "QUERY_ORPHANED_KNOWLEDGE" in q:
            orphaned = []
            for n_id, n in self.nodes.items():
                if n.get("label") == "Developer" and n.get("status") == "inactive":
                    dev_name = n.get("name")
                    for edge in self.edges:
                        if edge.get("type") == "AUTHORED_BY" and edge.get("target") == n_id:
                            doc = self.nodes.get(edge.get("source"), {})
                            doc_id = doc.get("id")
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

        # 10. Alerts or stale docs query
        if "stale" in q.lower() or "drift" in q.lower() or "FLAGGED_STALE" in q:
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

        # Default fallback: return all nodes as rows with id and props
        rows = []
        for n_id, n in self.nodes.items():
            rows.append([n_id, n.get("label", "Node"), n.get("name") or n.get("title") or n_id, n])
        return FalkorDBResultMock(rows, ["id", "label", "name_or_title", "properties"])


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

    def query(self, cypher_query: str, params: Optional[Dict[str, Any]] = None) -> FalkorDBResultWrapper:
        """Execute a Cypher query on FalkorDB or the fallback engine."""
        if not self.is_connected or self.is_fallback:
            # Try reconnecting in case Docker just spun up
            if self.connect():
                raw = self.graph.query(cypher_query, params)
                return FalkorDBResultWrapper(raw)
            raw = self._fallback_instance.query(cypher_query, params)
            return FalkorDBResultWrapper(raw)
        try:
            raw = self.graph.query(cypher_query, params)
            return FalkorDBResultWrapper(raw)
        except Exception as e:
            # If connection dropped, retry once
            if self.connect():
                raw = self.graph.query(cypher_query, params)
                return FalkorDBResultWrapper(raw)
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
