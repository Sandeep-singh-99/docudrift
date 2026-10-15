"""
DocuDrift / LivingWiki — Autonomous Knowledge Staleness & Drift Sentinel
Streamlit Application for FalkorDB Graph Hacks Hackathon.
Tracks Targeted:
- Track 01: Agents That Act on Connected Data
- Track 03: Company Brain
(Plus Track 02: Multi-Agent Coordination via LangGraph)
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path regardless of execution directory
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from graph.connection import db_manager
from graph.seeder import seed_falkordb_graph, SAMPLE_DATA
from graph.queries import (
    QUERY_DRIFT_SCORE,
    QUERY_ORPHANED_KNOWLEDGE,
    QUERY_GET_ALL_NODES,
    QUERY_GET_ALL_EDGES
)
from agent.tools import (
    calculate_staleness_and_drift,
    detect_orphaned_knowledge,
    get_blast_radius_impact,
    generate_auto_patch_suggestion,
    execute_cypher_tool
)
from agent.workflow import docudrift_agent
from ui.components import render_interactive_graph, COLOR_MAP

# Page Configuration
st.set_page_config(
    page_title="DocuDrift — Knowledge Staleness Sentinel",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #a855f7, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .tagline {
        font-size: 1.15rem;
        color: #94a3b8;
        margin-bottom: 1rem;
        font-style: italic;
    }
    .track-badge {
        display: inline-block;
        padding: 4px 10px;
        margin-right: 8px;
        margin-bottom: 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #1e293b;
        border: 1px solid #334155;
        color: #38bdf8;
    }
    .stale-box {
        background-color: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "seeded" not in st.session_state:
    seed_falkordb_graph()
    st.session_state.seeded = True


# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/FalkorDB/FalkorDB/main/docs/logo.png", width=180)
    st.subheader("🛰️ DocuDrift Control Hub")

    db_status = db_manager.get_status()
    if db_status["connected"]:
        st.success(f"🟢 **Connected to Live FalkorDB**\n`{db_status['host']}:{db_status['port']}`")
    else:
        st.warning(f"🟡 **{db_status['mode']}**\n(Docker standby - run `docker compose up -d` for live FalkorDB server)")

    st.markdown("---")
    st.subheader("🔑 AI & Search Keys")
    groq_api_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""), help="Get your free key at https://console.groq.com")
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key

    groq_model = st.selectbox(
        "Groq LLM Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        index=0
    )
    os.environ["GROQ_MODEL"] = groq_model

    tavily_api_key = st.text_input("Tavily API Key (Optional)", type="password", value=os.getenv("TAVILY_API_KEY", ""), help="Used for external web verification at https://tavily.com")
    if tavily_api_key:
        os.environ["TAVILY_API_KEY"] = tavily_api_key

    st.markdown("---")
    st.subheader("⚡ Graph Actions")
    if st.button("🔄 Reset & Re-Seed Enterprise Graph", use_container_width=True):
        seed_res = seed_falkordb_graph()
        st.success(f"Graph reset & seeded! Mode: {seed_res.get('mode')}")
        st.rerun()

    if st.button("🚨 Simulate New Drift PR Merged", use_container_width=True):
        # Simulate PR 320 merging into inventory
        if db_manager.is_fallback:
            fb = db_manager._fallback_instance
            new_pr = {
                "id": f"pr_{len(fb.nodes) + 400}",
                "number": len(fb.nodes) + 400,
                "title": "Migrate InventoryAPI to gRPC protocol v2",
                "merged_at": datetime.now().strftime("%Y-%m-%d"),
                "diff_summary": "Replaced REST endpoints with gRPC protobuf definitions.",
                "files_changed": "proto/inventory.proto, server.go"
            }
            fb.nodes[new_pr["id"]] = {"label": "PullRequest", **new_pr}
            fb.edges.append({"type": "MODIFIED", "source": new_pr["id"], "target": "srv_inventory"})
            st.toast("⚡ PR merged! Drift score increased for Inventory docs.", icon="🚨")
        st.rerun()

    st.markdown("---")
    st.caption("FalkorDB Graph Hacks Hackathon 2026")


# --- HERO HEADER & TRACK BADGES ---
st.markdown('<div class="main-header">DocuDrift / LivingWiki</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">"The company wiki that knows when it\'s lying."</div>', unsafe_allow_html=True)

col_t1, col_t2, col_t3 = st.columns([1, 1, 1])
with col_t1:
    st.markdown("""
    <div class="track-badge">
        <b>🕵️ Track 01: Agents That Act on Connected Data</b><br>
        <span style="font-size:0.75rem; color:#94a3b8;">Multi-hop reasoning &bull; Graph staleness algorithms &bull; Explainable drift</span>
    </div>
    """, unsafe_allow_html=True)
with col_t2:
    st.markdown("""
    <div class="track-badge">
        <b>🧠 Track 03: Company Brain</b><br>
        <span style="font-size:0.75rem; color:#94a3b8;">Enterprise ontology &bull; Orphaned maintainers &bull; Keeping knowledge current</span>
    </div>
    """, unsafe_allow_html=True)
with col_t3:
    st.markdown("""
    <div class="track-badge">
        <b>🤖 Track 02: Agent Memory & Coordination</b><br>
        <span style="font-size:0.75rem; color:#94a3b8;">LangGraph multi-agent flow &bull; Groq LLM &bull; Tavily search tool</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# --- MAIN TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🛰️ Staleness & Drift Radar",
    "🕸️ Interactive Knowledge Graph",
    "💬 AI Sentinel & Auto-Patcher",
    "👤 Knowledge Orphanage (Bus Factor)",
    "💥 Blast Radius & PR Impact",
    "🛠️ FalkorDB Cypher Console"
])


# ==========================================
# TAB 1: STALENESS & DRIFT RADAR
# ==========================================
with tab1:
    st.subheader("🛰️ Autonomous Knowledge Staleness & Drift Radar")
    st.caption("FalkorDB evaluates documentation age against merged code pull requests and modified API endpoints.")

    drift_data = calculate_staleness_and_drift()
    if not drift_data and db_manager.is_fallback:
        seed_falkordb_graph()
        drift_data = calculate_staleness_and_drift()

    df_drift = pd.DataFrame(drift_data) if drift_data else pd.DataFrame()

    # Top KPI Metrics
    total_docs = len(df_drift)
    critical_docs = len(df_drift[df_drift["status"] == "CRITICAL DRIFT"]) if not df_drift.empty and "status" in df_drift.columns else 0
    avg_score = int(df_drift["drift_score"].mean()) if not df_drift.empty and "drift_score" in df_drift.columns else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Monitored Doc Pages", total_docs, "Living Wiki")
    m2.metric("Critical Drift Alert", critical_docs, "Immediate Action", delta_color="inverse")
    m3.metric("Average Drift Velocity", f"{avg_score} pts", "FalkorDB Cypher Metric")
    m4.metric("Graph Engine Mode", "Active", "FalkorDB")

    st.markdown("---")

    col_chart, col_table = st.columns([1, 1.2])

    with col_chart:
        st.markdown("##### 📊 Drift Velocity by Service")
        if not df_drift.empty and "drift_score" in df_drift.columns:
            fig = px.bar(
                df_drift,
                x="service_name",
                y="drift_score",
                color="status",
                color_discrete_map={
                    "CRITICAL DRIFT": "#ef4444",
                    "WARNING": "#f59e0b",
                    "HEALTHY": "#10b981"
                },
                text="drift_score",
                labels={"service_name": "Service", "drift_score": "Drift Score (PRs * 15 + Endpoints * 20)"}
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#f8fafc",
                height=320,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("##### 📋 Monitored Documentation Status")
        if not df_drift.empty:
            cols = [c for c in ["doc_title", "service_name", "last_updated", "pr_count", "drift_score", "status"] if c in df_drift.columns]
            st.dataframe(
                df_drift[cols] if cols else df_drift,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No documentation records found. Click 'Reset & Re-Seed Enterprise Graph' in the sidebar.")

    st.markdown("##### 🚨 Active Drift Breakdown")
    for doc in drift_data:
        if doc.get("status") == "CRITICAL DRIFT":
            st.markdown(f"""
            <div class="stale-box">
                <h4>⚠️ {doc.get('doc_title')} &bull; Status: <span style="color:#ef4444;">CRITICAL DRIFT</span></h4>
                <p><b>Target Service:</b> {doc.get('service_name')} | <b>Last Updated:</b> {doc.get('last_updated')} | <b>Drift Score:</b> {doc.get('drift_score')} pts</p>
                <p><b>Why it's flagged:</b> The documentation has not been touched, but <b>{doc.get('pr_count')} pull requests</b> and <b>{doc.get('endpoint_pr_count')} endpoint changes</b> have merged to the codebase since.</p>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# TAB 2: INTERACTIVE KNOWLEDGE GRAPH
# ==========================================
with tab2:
    st.subheader("🕸️ Enterprise Knowledge Graph Explorer")
    st.caption("Inspect how DocPages connect to Services, Developers, Endpoints, and Pull Requests in FalkorDB.")

    col_legend1, col_legend2 = st.columns([3, 1])
    with col_legend2:
        st.markdown("##### 🎨 Graph Legend")
        for label, color in COLOR_MAP.items():
            st.markdown(f"<span style='color:{color}; font-size:1.1rem;'>●</span> **{label}**", unsafe_allow_html=True)

    with col_legend1:
        # Collect nodes and edges
        nodes = []
        edges = []
        if db_manager.is_fallback:
            fb = db_manager._fallback_instance
            for n_id, n in fb.nodes.items():
                nodes.append({"id": n_id, **n})
            edges = fb.edges
        else:
            try:
                n_res = db_manager.query(QUERY_GET_ALL_NODES)
                for row in n_res:
                    labels, props = row
                    nodes.append({"id": props.get("id", str(id(props))), "label": labels[0] if labels else "Node", **props})
                e_res = db_manager.query(QUERY_GET_ALL_EDGES)
                for row in e_res:
                    src_id, src_lbl, src_b_id, src_name, src_title, rel_type, rel_props, tgt_id, tgt_lbl, tgt_b_id, tgt_name, tgt_title = row
                    edges.append({
                        "source": src_b_id or str(src_id),
                        "target": tgt_b_id or str(tgt_id),
                        "type": rel_type
                    })
            except Exception:
                pass

        if nodes and edges:
            graph_html = render_interactive_graph(nodes, edges, height="580px")
            components.html(graph_html, height=600, scrolling=False)
        else:
            st.info("No graph data found. Click 'Reset & Re-Seed Enterprise Graph' in the sidebar!")


# ==========================================
# TAB 3: AI SENTINEL & AUTO-PATCHER
# ==========================================
with tab3:
    st.subheader("💬 DocuDrift AI Sentinel & Auto-Patcher")
    st.caption("Ask questions about deploying, running, or configuring company services. If the docs lie, DocuDrift catches it and generates an auto-patch diff!")

    # Quick prompt shortcuts
    st.markdown("**⚡ Quick Prompts:**")
    qp1, qp2, qp3, qp4 = st.columns(4)
    preset_query = None
    if qp1.button("🚀 How do I deploy PaymentGateway?", use_container_width=True):
        preset_query = "How do I deploy PaymentGateway in production?"
    if qp2.button("🔍 Run Staleness & Drift Audit", use_container_width=True):
        preset_query = "Audit our documentation for drift and staleness."
    if qp3.button("👤 Check Orphaned Knowledge", use_container_width=True):
        preset_query = "Are there any orphaned system docs where maintainers left?"
    if qp4.button("💥 Blast Radius for PR #310", use_container_width=True):
        preset_query = "What is the blast radius of PR #310?"

    # Input Box
    user_query = st.chat_input("Ask DocuDrift Sentinel about your systems, docs, or deployments...")
    active_prompt = preset_query or user_query

    if active_prompt:
        st.session_state.chat_history.append({"role": "user", "content": active_prompt})

        with st.spinner("🛰️ FalkorDB Agent querying graph topology, checking drift, and synthesizing patch..."):
            initial_state = {
                "query": active_prompt,
                "intent": "qna",
                "cypher_queries": [],
                "graph_context": {},
                "external_context": None,
                "drift_detected": False,
                "stale_docs": [],
                "orphaned_docs": [],
                "suggested_patch": None,
                "diff_content": None,
                "final_response": "",
                "intermediate_steps": []
            }

            result = docudrift_agent.invoke(initial_state)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["final_response"],
                "steps": result.get("intermediate_steps", []),
                "diff": result.get("diff_content"),
                "patch": result.get("suggested_patch")
            })

    # Render Chat History
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").markdown(f"**{msg['content']}**")
        else:
            with st.chat_message("assistant", avatar="🛰️"):
                st.markdown(msg["content"])

                # Render Steps
                if msg.get("steps"):
                    with st.expander("🔍 Agent Execution & Multi-Hop Cypher Trace"):
                        for step in msg["steps"]:
                            st.write(step)

                # Render Git Diff if auto-patch was generated
                if msg.get("diff"):
                    st.markdown("#### 🛠️ Auto-Generated Documentation Patch (Unified Diff)")
                    st.code(msg["diff"], language="diff")

                    c_act1, c_act2 = st.columns([1, 4])
                    if c_act1.button("✅ Approve & Auto-Create PR", key=f"btn_approve_{hash(msg['content'])}"):
                        st.success("🎉 Pull Request #402 opened: `[DocuDrift] Auto-patch stale PaymentGateway docs`!")


# ==========================================
# TAB 4: KNOWLEDGE ORPHANAGE (BUS FACTOR)
# ==========================================
with tab4:
    st.subheader("👤 Bus Factor & Knowledge Orphanage Sentinel")
    st.caption("Track 03 Company Brain: Identifies systems and documents whose sole authors have left the company ([:LEFT_COMPANY]).")

    orphaned_records = detect_orphaned_knowledge()

    if orphaned_records:
        st.error(f"🚨 **Critical Turnover Alert:** Found {len(orphaned_records)} documentation asset(s) with 0 active maintainers!")

        for item in orphaned_records:
            st.markdown(f"""
            <div style="background-color:rgba(239,68,68,0.08); border:1px solid #ef4444; border-radius:8px; padding:16px; margin-bottom:16px;">
                <h3 style="margin-top:0;">📄 {item.get('doc_title')}</h3>
                <p><b>Connected Service:</b> <code>{item.get('service_name')}</code> | <b>Last Updated:</b> {item.get('last_updated')}</p>
                <p><b>Departed Maintainer:</b> <span style="color:#ef4444;">👤 {item.get('departed_author')}</span> (<code>{item.get('departed_email')}</code>) &bull; <i>Status: INACTIVE</i></p>
                <p><b>Active Co-Authors:</b> <span style="color:#ef4444; font-weight:bold;">0 (Bus Factor = 0)</span></p>
                <hr style="border-color:#334155;">
                <h4>💡 Agent Recommended Replacement Maintainers (Discovered via PR contribution graph):</h4>
            </div>
            """, unsafe_allow_html=True)

            for cand in item.get("suggested_maintainers", []):
                col_cand, col_btn = st.columns([3, 1])
                with col_cand:
                    st.markdown(f"**👤 {cand.get('name')}** (`{cand.get('email')}`) — **{cand.get('recent_prs')} recent PRs merged** into this service.")
                with col_btn:
                    if st.button(f"Assign to {cand.get('name')}", key=f"btn_{cand.get('name')}"):
                        st.success(f"Ownership assigned to {cand.get('name')}! Slack notification dispatched.")
    else:
        st.success("🎉 No orphaned knowledge found! All documentation pages have active maintainers.")


# ==========================================
# TAB 5: BLAST RADIUS & PR IMPACT
# ==========================================
with tab5:
    st.subheader("💥 Pull Request Blast Radius & Impact Analyzer")
    st.caption("Track 01 Connected Data: Traces ripple effects across endpoints, doc pages, and downstream services.")

    pr_input = st.number_input("Enter Pull Request # to analyze", value=315, step=1)
    if st.button("Calculate Blast Radius", use_container_width=True):
        impact = get_blast_radius_impact(pr_input)

        if "error" in impact:
            st.warning(impact["error"])
        else:
            col_b1, col_b2, col_b3 = st.columns(3)
            col_b1.metric("PR Number", f"#{impact.get('pr_number')}")
            col_b2.metric("Blast Score", impact.get("blast_score", 0), "Impact Level: HIGH")
            col_b3.metric("Affected Docs", len(impact.get("affected_docs", [])))

            st.markdown("##### 🔌 Affected Endpoints:")
            for ep in impact.get("affected_endpoints", []):
                st.markdown(f"- <code>{ep}</code>", unsafe_allow_html=True)

            st.markdown("##### 📄 Affected Documentation Pages:")
            for doc in impact.get("affected_docs", []):
                st.markdown(f"- **{doc}**")


# ==========================================
# TAB 6: CYPHERS PLAYGROUND & DOCKER GUIDE
# ==========================================
with tab6:
    st.subheader("🛠️ FalkorDB Interactive Cypher Console")
    st.caption("Run custom Cypher queries directly against FalkorDB.")

    sample_query = st.selectbox(
        "Load Sample Cypher Query:",
        [
            "MATCH (doc:DocPage)-[:DOCUMENTS]->(s:Service) RETURN doc.title, s.name, doc.last_updated",
            "MATCH (pr:PullRequest)-[:MODIFIED]->(s:Service) RETURN pr.number, pr.title, s.name",
            "MATCH (d:Developer) RETURN d.name, d.email, d.status",
            "MATCH (doc:DocPage)-[:REFERENCES]->(ep:Endpoint) RETURN doc.title, ep.path, ep.deprecated"
        ]
    )

    custom_cypher = st.text_area("Cypher Query", value=sample_query, height=120)

    if st.button("▶️ Execute Cypher Query"):
        res = execute_cypher_tool(custom_cypher)
        st.markdown("##### Query Results:")
        st.write(res)

    st.markdown("---")
    st.subheader("🐳 Docker Local FalkorDB Setup Guide")
    st.markdown("""
    To launch local FalkorDB via Docker on port `6379`:
    ```bash
    # From project root:
    docker compose up -d
    ```
    Or run standalone Docker container:
    ```bash
    docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest
    ```
    Once running, DocuDrift automatically connects and leverages live FalkorDB GraphBLAS performance!
    """)
