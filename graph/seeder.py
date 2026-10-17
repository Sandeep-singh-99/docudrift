"""
DocuDrift Knowledge Graph Seeder.
Populates FalkorDB with a realistic enterprise topology illustrating:
1. Drift detection (PR #310 switched deploy from ./deploy.sh to Docker Compose)
2. Orphaned knowledge (Bob authored NotificationWorker docs then left the company)
3. API endpoint deprecation (/v1/charge replaced with /v2/checkout)
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from graph.connection import db_manager

SAMPLE_DATA = {
    "developers": [
        {"id": "dev_alice", "name": "Alice Chen", "email": "alice@acme.corp", "role": "Staff Platform Engineer", "status": "active"},
        {"id": "dev_bob", "name": "Bob Miller", "email": "bob@acme.corp", "role": "Ex-Senior Backend Engineer", "status": "inactive"},
        {"id": "dev_charlie", "name": "Charlie Davis", "email": "charlie@acme.corp", "role": "DevOps Lead", "status": "active"},
        {"id": "dev_diana", "name": "Diana Prince", "email": "diana@acme.corp", "role": "Distributed Systems Engineer", "status": "active"},
    ],
    "services": [
        {"id": "srv_payment", "name": "PaymentGateway", "tier": "Tier-1", "repo_url": "github.com/acme/payment-gateway", "description": "Core payment processing, card tokenization, and settlement engine."},
        {"id": "srv_auth", "name": "AuthService", "tier": "Tier-1", "repo_url": "github.com/acme/auth-service", "description": "OAuth2 / OIDC authentication, session manager, and JWT issuer."},
        {"id": "srv_notify", "name": "NotificationWorker", "tier": "Tier-2", "repo_url": "github.com/acme/notification-worker", "description": "Async Kafka consumer sending transactional emails, SMS, and push notifications."},
        {"id": "srv_inventory", "name": "InventoryAPI", "tier": "Tier-2", "repo_url": "github.com/acme/inventory-api", "description": "High-throughput warehouse catalog and real-time inventory reservation."},
    ],
    "endpoints": [
        {"id": "ep_v1_charge", "path": "/v1/charge", "method": "POST", "description": "Legacy charge card API. Lacks idempotency.", "deprecated": True, "current_status": "DEPRECATED_BY_PR_315"},
        {"id": "ep_v2_checkout", "path": "/v2/checkout", "method": "POST", "description": "Modern checkout endpoint supporting multi-currency and idempotency keys.", "deprecated": False, "current_status": "PRODUCTION"},
        {"id": "ep_auth_token", "path": "/auth/token", "method": "POST", "description": "Exchange client credentials or refresh token for RS256 JWT.", "deprecated": False, "current_status": "PRODUCTION"},
        {"id": "ep_notify_dispatch", "path": "/notify/dispatch", "method": "POST", "description": "Direct message trigger queue.", "deprecated": False, "current_status": "PRODUCTION"},
        {"id": "ep_inventory_reserve", "path": "/inventory/reserve", "method": "POST", "description": "Reserve warehouse inventory during checkout.", "deprecated": False, "current_status": "PRODUCTION"},
    ],
    "doc_pages": [
        {
            "id": "doc_payment_deploy",
            "title": "Deploying Payment Gateway & Processing Payments",
            "url": "https://wiki.acme.corp/ops/payment-gateway-deploy",
            "category": "Deployment & Operations",
            "last_updated": (datetime.now() - timedelta(days=94)).strftime("%Y-%m-%d"),
            "content": """# Deploying Payment Gateway

To deploy the PaymentGateway service in production:
1. SSH into the bastion host: `ssh bastion.acme.internal`
2. Run the legacy bash deployment script:
   ```bash
   ./deploy.sh --env=production --cluster=us-east-1
   ```
3. To test a transaction, call the charge endpoint:
   ```bash
   curl -X POST https://api.acme.corp/v1/charge -d '{"amount": 1000, "currency": "USD"}'
   ```
Ensure port 8080 is accessible from the load balancer."""
        },
        {
            "id": "doc_notification_ops",
            "title": "Notification Worker Operations & Kafka Tuning",
            "url": "https://wiki.acme.corp/services/notification-worker",
            "category": "Architecture & Runbooks",
            "last_updated": (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d"),
            "content": """# Notification Worker Runbook

NotificationWorker consumes events from Kafka topic `transaction.events`.
Authored solely by Bob Miller.

### Key Configurations:
- Thread Pool Size: 16
- Retries: 3 with exponential backoff
- Alerting channel: #ops-notifications
If messages lag > 5000, scale the pod replica count to 5."""
        },
        {
            "id": "doc_auth_guide",
            "title": "Authentication & JWT Onboarding",
            "url": "https://wiki.acme.corp/security/auth-service-onboarding",
            "category": "Security & Identity",
            "last_updated": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
            "content": """# AuthService Guide

AuthService generates HS256 tokens valid for 24 hours.
Services authenticate via `POST /auth/token` with client credentials."""
        },
        {
            "id": "doc_inventory_guide",
            "title": "Inventory Management & Stock Reservation Runbook",
            "url": "https://wiki.acme.corp/services/inventory-guide",
            "category": "API & Runbooks",
            "last_updated": (datetime.now() - timedelta(days=75)).strftime("%Y-%m-%d"),
            "content": """# Inventory Management Guide

InventoryAPI maintains real-time catalog stock levels and reservations.
Maintained by Charlie Davis.

### REST Endpoints:
- `POST /inventory/reserve` - Reserve item stock during checkout flow."""
        }
    ],
    "pull_requests": [
        {
            "id": "pr_310",
            "number": 310,
            "title": "Migrate PaymentGateway deploy from ./deploy.sh to Docker Compose",
            "merged_at": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "diff_summary": "Deleted ./deploy.sh. Added docker-compose.prod.yml. Production deployments now execute: docker compose -f docker-compose.prod.yml up -d --build",
            "files_changed": "deploy.sh, docker-compose.prod.yml, Dockerfile"
        },
        {
            "id": "pr_315",
            "number": 315,
            "title": "Deprecate /v1/charge in favor of /v2/checkout with Idempotency",
            "merged_at": (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d"),
            "diff_summary": "Marked /v1/charge as 410 Gone / Deprecated. Introduced /v2/checkout requiring Idempotency-Key HTTP header.",
            "files_changed": "src/controllers/payment.ts, src/routes/checkout.ts"
        },
        {
            "id": "pr_318",
            "number": 318,
            "title": "Add STRIPE_WEBHOOK_SECRET and mandatory TLS 1.3 requirement",
            "merged_at": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "diff_summary": "Enforced TLS 1.3 on port 8443 instead of port 8080. Added required env variable STRIPE_WEBHOOK_SECRET.",
            "files_changed": "config/security.json, server.go"
        },
        {
            "id": "pr_280",
            "number": 280,
            "title": "Switch AuthService JWT algorithm to RS256 with 15m TTL",
            "merged_at": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            "diff_summary": "Upgraded token signing from HS256 to RS256 public/private key pairs. Reduced token validity from 24h to 15m for compliance.",
            "files_changed": "auth/jwt.go, auth/keys.pem"
        },
        {
            "id": "pr_295",
            "number": 295,
            "title": "NotificationWorker Kafka partition rebalance & dead-letter queue",
            "merged_at": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
            "diff_summary": "Added dead-letter queue `notifications.dlq`. Tuned batch size to 500 records.",
            "files_changed": "src/kafka/consumer.py"
        }
    ]
}


def seed_falkordb_graph() -> Dict[str, Any]:
    """
    Executes Cypher statements to seed the graph or populates the in-memory fallback.
    """
    # Clean previous graph data
    try:
        db_manager.query("MATCH (n) DETACH DELETE n")
    except Exception:
        pass

    # Populate fallback engine synchronously if in fallback mode
    if db_manager.is_fallback:
        fb = db_manager._fallback_instance
        fb.nodes.clear()
        fb.edges.clear()

        # Add developers
        for dev in SAMPLE_DATA["developers"]:
            fb.nodes[dev["id"]] = {"label": "Developer", **dev}

        # Add services
        for srv in SAMPLE_DATA["services"]:
            fb.nodes[srv["id"]] = {"label": "Service", **srv}

        # Add endpoints
        for ep in SAMPLE_DATA["endpoints"]:
            fb.nodes[ep["id"]] = {"label": "Endpoint", **ep}

        # Add doc pages
        for doc in SAMPLE_DATA["doc_pages"]:
            fb.nodes[doc["id"]] = {"label": "DocPage", **doc}

        # Add PRs
        for pr in SAMPLE_DATA["pull_requests"]:
            fb.nodes[pr["id"]] = {"label": "PullRequest", **pr}

        # Edges
        # Doc -> Service
        fb.edges.append({"type": "DOCUMENTS", "source": "doc_payment_deploy", "target": "srv_payment"})
        fb.edges.append({"type": "DOCUMENTS", "source": "doc_notification_ops", "target": "srv_notify"})
        fb.edges.append({"type": "DOCUMENTS", "source": "doc_auth_guide", "target": "srv_auth"})
        fb.edges.append({"type": "DOCUMENTS", "source": "doc_inventory_guide", "target": "srv_inventory"})

        # Doc -> Authors
        fb.edges.append({"type": "AUTHORED_BY", "source": "doc_payment_deploy", "target": "dev_alice"})
        fb.edges.append({"type": "AUTHORED_BY", "source": "doc_notification_ops", "target": "dev_bob"})  # Sole author Bob (LEFT_COMPANY)
        fb.edges.append({"type": "AUTHORED_BY", "source": "doc_auth_guide", "target": "dev_alice"})
        fb.edges.append({"type": "AUTHORED_BY", "source": "doc_inventory_guide", "target": "dev_charlie"})

        # Doc -> Endpoints
        fb.edges.append({"type": "REFERENCES", "source": "doc_payment_deploy", "target": "ep_v1_charge"})
        fb.edges.append({"type": "REFERENCES", "source": "doc_auth_guide", "target": "ep_auth_token"})
        fb.edges.append({"type": "REFERENCES", "source": "doc_inventory_guide", "target": "ep_inventory_reserve"})

        # PR -> Service
        fb.edges.append({"type": "MODIFIED", "source": "pr_310", "target": "srv_payment"})
        fb.edges.append({"type": "MODIFIED", "source": "pr_315", "target": "srv_payment"})
        fb.edges.append({"type": "MODIFIED", "source": "pr_318", "target": "srv_payment"})
        fb.edges.append({"type": "MODIFIED", "source": "pr_280", "target": "srv_auth"})
        fb.edges.append({"type": "MODIFIED", "source": "pr_295", "target": "srv_notify"})

        # PR -> Endpoints
        fb.edges.append({"type": "TOUCHED_ENDPOINT", "source": "pr_315", "target": "ep_v1_charge"})
        fb.edges.append({"type": "TOUCHED_ENDPOINT", "source": "pr_315", "target": "ep_v2_checkout"})

        # PR -> Authors
        fb.edges.append({"type": "AUTHORED_BY", "source": "pr_310", "target": "dev_charlie"})
        fb.edges.append({"type": "AUTHORED_BY", "source": "pr_315", "target": "dev_alice"})
        fb.edges.append({"type": "AUTHORED_BY", "source": "pr_318", "target": "dev_charlie"})
        fb.edges.append({"type": "AUTHORED_BY", "source": "pr_280", "target": "dev_alice"})
        fb.edges.append({"type": "AUTHORED_BY", "source": "pr_295", "target": "dev_diana"})

        # Dev left company
        fb.edges.append({"type": "LEFT_COMPANY", "source": "dev_bob", "target": "srv_notify"})

        # Add initial Alert
        alert_1 = {
            "id": "alert_drift_payment",
            "doc_id": "doc_payment_deploy",
            "reason": "PR #310 removed ./deploy.sh and PR #315 deprecated /v1/charge, but doc is 94 days old.",
            "severity": "CRITICAL",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "suggested_patch": "Update deploy guide to use Docker Compose and replace /v1/charge with /v2/checkout."
        }
        fb.nodes[alert_1["id"]] = {"label": "Alert", **alert_1}
        fb.edges.append({"type": "FLAGGED_STALE", "source": "doc_payment_deploy", "target": alert_1["id"]})

        return {
            "status": "success",
            "mode": "FalkorDB In-Memory Fallback",
            "nodes_seeded": len(fb.nodes),
            "edges_seeded": len(fb.edges)
        }

    # Cypher Seeding for Live FalkorDB Server
    cypher_statements = []

    # Developers
    for dev in SAMPLE_DATA["developers"]:
        cypher_statements.append(f"""
        MERGE (d:Developer {{id: '{dev["id"]}'}})
        SET d.name = '{dev["name"]}', d.email = '{dev["email"]}', d.role = '{dev["role"]}', d.status = '{dev["status"]}'
        """)

    # Services
    for srv in SAMPLE_DATA["services"]:
        cypher_statements.append(f"""
        MERGE (s:Service {{id: '{srv["id"]}'}})
        SET s.name = '{srv["name"]}', s.tier = '{srv["tier"]}', s.repo_url = '{srv["repo_url"]}', s.description = '{srv["description"]}'
        """)

    # Endpoints
    for ep in SAMPLE_DATA["endpoints"]:
        cypher_statements.append(f"""
        MERGE (e:Endpoint {{id: '{ep["id"]}'}})
        SET e.path = '{ep["path"]}', e.method = '{ep["method"]}', e.description = '{ep["description"]}', e.deprecated = {str(ep["deprecated"]).lower()}, e.current_status = '{ep["current_status"]}'
        """)

    # DocPages
    for doc in SAMPLE_DATA["doc_pages"]:
        escaped_content = doc["content"].replace("'", "\\'")
        cypher_statements.append(f"""
        MERGE (dp:DocPage {{id: '{doc["id"]}'}})
        SET dp.title = '{doc["title"]}', dp.url = '{doc["url"]}', dp.category = '{doc["category"]}', dp.last_updated = '{doc["last_updated"]}', dp.content = '{escaped_content}'
        """)

    # PRs
    for pr in SAMPLE_DATA["pull_requests"]:
        escaped_diff = pr["diff_summary"].replace("'", "\\'")
        cypher_statements.append(f"""
        MERGE (pr:PullRequest {{id: '{pr["id"]}'}})
        SET pr.number = {pr["number"]}, pr.title = '{pr["title"]}', pr.merged_at = '{pr["merged_at"]}', pr.diff_summary = '{escaped_diff}', pr.files_changed = '{pr["files_changed"]}'
        """)

    # Relationships
    cypher_statements.extend([
        # Doc -> Service
        "MATCH (d:DocPage {id: 'doc_payment_deploy'}), (s:Service {id: 'srv_payment'}) MERGE (d)-[:DOCUMENTS]->(s)",
        "MATCH (d:DocPage {id: 'doc_notification_ops'}), (s:Service {id: 'srv_notify'}) MERGE (d)-[:DOCUMENTS]->(s)",
        "MATCH (d:DocPage {id: 'doc_auth_guide'}), (s:Service {id: 'srv_auth'}) MERGE (d)-[:DOCUMENTS]->(s)",
        "MATCH (d:DocPage {id: 'doc_inventory_guide'}), (s:Service {id: 'srv_inventory'}) MERGE (d)-[:DOCUMENTS]->(s)",

        # Doc -> Authors
        "MATCH (d:DocPage {id: 'doc_payment_deploy'}), (dev:Developer {id: 'dev_alice'}) MERGE (d)-[:AUTHORED_BY]->(dev)",
        "MATCH (d:DocPage {id: 'doc_notification_ops'}), (dev:Developer {id: 'dev_bob'}) MERGE (d)-[:AUTHORED_BY]->(dev)",
        "MATCH (d:DocPage {id: 'doc_auth_guide'}), (dev:Developer {id: 'dev_alice'}) MERGE (d)-[:AUTHORED_BY]->(dev)",
        "MATCH (d:DocPage {id: 'doc_inventory_guide'}), (dev:Developer {id: 'dev_charlie'}) MERGE (d)-[:AUTHORED_BY]->(dev)",

        # Doc -> Endpoint
        "MATCH (d:DocPage {id: 'doc_payment_deploy'}), (ep:Endpoint {id: 'ep_v1_charge'}) MERGE (d)-[:REFERENCES]->(ep)",
        "MATCH (d:DocPage {id: 'doc_auth_guide'}), (ep:Endpoint {id: 'ep_auth_token'}) MERGE (d)-[:REFERENCES]->(ep)",
        "MATCH (d:DocPage {id: 'doc_inventory_guide'}), (ep:Endpoint {id: 'ep_inventory_reserve'}) MERGE (d)-[:REFERENCES]->(ep)",

        # PR -> Service
        "MATCH (pr:PullRequest {id: 'pr_310'}), (s:Service {id: 'srv_payment'}) MERGE (pr)-[:MODIFIED]->(s)",
        "MATCH (pr:PullRequest {id: 'pr_315'}), (s:Service {id: 'srv_payment'}) MERGE (pr)-[:MODIFIED]->(s)",
        "MATCH (pr:PullRequest {id: 'pr_318'}), (s:Service {id: 'srv_payment'}) MERGE (pr)-[:MODIFIED]->(s)",
        "MATCH (pr:PullRequest {id: 'pr_280'}), (s:Service {id: 'srv_auth'}) MERGE (pr)-[:MODIFIED]->(s)",
        "MATCH (pr:PullRequest {id: 'pr_295'}), (s:Service {id: 'srv_notify'}) MERGE (pr)-[:MODIFIED]->(s)",

        # PR -> Endpoints
        "MATCH (pr:PullRequest {id: 'pr_315'}), (ep:Endpoint {id: 'ep_v1_charge'}) MERGE (pr)-[:TOUCHED_ENDPOINT]->(ep)",
        "MATCH (pr:PullRequest {id: 'pr_315'}), (ep:Endpoint {id: 'ep_v2_checkout'}) MERGE (pr)-[:TOUCHED_ENDPOINT]->(ep)",

        # PR -> Authors
        "MATCH (pr:PullRequest {id: 'pr_310'}), (dev:Developer {id: 'dev_charlie'}) MERGE (pr)-[:AUTHORED_BY]->(dev)",
        "MATCH (pr:PullRequest {id: 'pr_315'}), (dev:Developer {id: 'dev_alice'}) MERGE (pr)-[:AUTHORED_BY]->(dev)",
        "MATCH (pr:PullRequest {id: 'pr_318'}), (dev:Developer {id: 'dev_charlie'}) MERGE (pr)-[:AUTHORED_BY]->(dev)",
        "MATCH (pr:PullRequest {id: 'pr_280'}), (dev:Developer {id: 'dev_alice'}) MERGE (pr)-[:AUTHORED_BY]->(dev)",
        "MATCH (pr:PullRequest {id: 'pr_295'}), (dev:Developer {id: 'dev_diana'}) MERGE (pr)-[:AUTHORED_BY]->(dev)",

        # Dev left company
        "MATCH (dev:Developer {id: 'dev_bob'}), (s:Service {id: 'srv_notify'}) MERGE (dev)-[:LEFT_COMPANY]->(s)",

        # Stale Alert
        """
        MERGE (a:Alert {id: 'alert_drift_payment'})
        SET a.reason = 'PR #310 removed ./deploy.sh and PR #315 deprecated /v1/charge, but doc is 94 days old.',
            a.severity = 'CRITICAL',
            a.created_at = '2026-10-14 10:00',
            a.suggested_patch = 'Update deploy guide to use Docker Compose and replace /v1/charge with /v2/checkout.'
        WITH a
        MATCH (d:DocPage {id: 'doc_payment_deploy'})
        MERGE (d)-[:FLAGGED_STALE]->(a)
        """
    ])

    for stmt in cypher_statements:
        try:
            db_manager.query(stmt)
        except Exception as e:
            print(f"Error seeding statement: {e}")

    return {
        "status": "success",
        "mode": "FalkorDB Live Server",
        "statements_executed": len(cypher_statements)
    }

# Auto-seed in fallback mode if empty so all features work immediately out-of-the-box
if db_manager.is_fallback and len(db_manager._fallback_instance.nodes) == 0:
    seed_falkordb_graph()

