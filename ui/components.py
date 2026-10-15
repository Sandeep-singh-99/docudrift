"""
Streamlit UI Components: Interactive PyVis Graph Visualizer, Metric Cards,
and Unified Diff Formatter for DocuDrift.
"""

import streamlit as pd_st
from pyvis.network import Network
import tempfile
import os
from typing import Dict, Any, List

COLOR_MAP = {
    "DocPage": "#8b5cf6",       # Violet
    "Service": "#3b82f6",       # Blue
    "Endpoint": "#10b981",      # Emerald
    "Developer": "#f59e0b",     # Amber
    "PullRequest": "#06b6d4",   # Cyan
    "Alert": "#ef4444"          # Red
}

ICON_MAP = {
    "DocPage": "📄",
    "Service": "⚙️",
    "Endpoint": "🔌",
    "Developer": "👤",
    "PullRequest": "🔀",
    "Alert": "🚨"
}


def render_interactive_graph(nodes_data: List[Dict[str, Any]], edges_data: List[Dict[str, Any]], height: str = "580px"):
    """
    Renders an interactive PyVis physics graph inside Streamlit.
    """
    net = Network(height=height, width="100%", bgcolor="#0f172a", font_color="#f8fafc", directed=True)
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=120, spring_strength=0.05, damping=0.09)

    # Add nodes
    for n in nodes_data:
        n_id = n.get("id")
        label_type = n.get("label", "Node")
        color = COLOR_MAP.get(label_type, "#94a3b8")
        icon = ICON_MAP.get(label_type, "📌")

        name = n.get("name") or n.get("title") or n.get("path") or f"PR #{n.get('number', '')}" or n_id
        display_label = f"{icon} {name}"

        # Build tooltip
        tooltip_lines = [f"<b>Type:</b> {label_type}", f"<b>ID:</b> {n_id}"]
        if "drift_score" in n:
            tooltip_lines.append(f"<b>Drift Score:</b> {n['drift_score']}")
        if "last_updated" in n:
            tooltip_lines.append(f"<b>Last Updated:</b> {n['last_updated']}")
        if "status" in n:
            tooltip_lines.append(f"<b>Status:</b> {n['status']}")
        if "diff_summary" in n:
            tooltip_lines.append(f"<b>Diff:</b> {n['diff_summary']}")
        if "deprecated" in n:
            tooltip_lines.append(f"<b>Deprecated:</b> {n['deprecated']}")

        title_html = "<br>".join(tooltip_lines)

        size = 28 if label_type in ["Service", "DocPage"] else 20
        if label_type == "Alert":
            size = 32

        net.add_node(
            n_id,
            label=display_label,
            title=title_html,
            color=color,
            size=size,
            shape="box" if label_type in ["DocPage", "Service"] else "dot",
            borderWidth=2,
            borderWidthSelected=4
        )

    # Add edges
    for e in edges_data:
        src = e.get("source")
        tgt = e.get("target")
        rel = e.get("type", "RELATED_TO")

        edge_color = "#ef4444" if rel in ["FLAGGED_STALE", "LEFT_COMPANY"] else "#64748b"
        dashes = True if rel in ["LEFT_COMPANY", "FLAGGED_STALE"] else False

        net.add_edge(
            src,
            tgt,
            title=f"Relationship: {rel}",
            label=rel,
            color=edge_color,
            arrows="to",
            dashes=dashes,
            width=2
        )

    # Save to temp file and return HTML
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
        net.save_graph(f.name)
        with open(f.name, "r", encoding="utf-8") as rf:
            html = rf.read()
    try:
        os.remove(f.name)
    except Exception:
        pass

    return html
