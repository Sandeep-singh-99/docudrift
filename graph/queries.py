"""
Cypher queries powering DocuDrift's staleness detection, orphaned knowledge alerts,
blast radius queries, and auto-patch context retrieval.
"""

# Query 1: Calculate Drift Scores for all Documented Services
# Counts merged PRs touching the service/endpoints relative to doc age
QUERY_DRIFT_SCORE = """
MATCH (doc:DocPage)-[:DOCUMENTS]->(s:Service)
OPTIONAL MATCH (pr:PullRequest)-[:MODIFIED]->(s)
OPTIONAL MATCH (doc)-[:REFERENCES]->(ep:Endpoint)<-[:TOUCHED_ENDPOINT]-(pr_ep:PullRequest)
WITH doc, s,
     count(DISTINCT pr) AS service_prs,
     count(DISTINCT pr_ep) AS endpoint_prs
RETURN doc.id AS doc_id,
       doc.title AS doc_title,
       doc.last_updated AS last_updated,
       s.name AS service_name,
       s.tier AS service_tier,
       service_prs AS pr_count,
       endpoint_prs AS endpoint_pr_count,
       (service_prs * 15 + endpoint_prs * 20) AS drift_score
ORDER BY drift_score DESC
"""

# Query 2: Orphaned Knowledge Alert
# Finds DocPages and Services whose original authors have left the company
QUERY_ORPHANED_KNOWLEDGE = """
MATCH (doc:DocPage)-[:AUTHORED_BY]->(author:Developer)
WHERE author.status = 'inactive'
MATCH (doc)-[:DOCUMENTS]->(s:Service)
OPTIONAL MATCH (doc)-[:AUTHORED_BY]->(other:Developer)
WHERE other.status = 'active'
WITH doc, s, author, count(other) AS active_coauthors
WHERE active_coauthors = 0
RETURN doc.id AS doc_id,
       doc.title AS doc_title,
       doc.last_updated AS last_updated,
       s.name AS service_name,
       author.name AS departed_author,
       author.email AS departed_email
"""

# Query 3: Identify Potential New Maintainers for Orphaned Services
# Discovers active engineers who frequently contribute PRs to the orphaned service
QUERY_SUGGEST_MAINTAINERS = """
MATCH (s:Service {name: $service_name})<-[:MODIFIED]-(pr:PullRequest)-[:AUTHORED_BY]->(dev:Developer)
WHERE dev.status = 'active'
RETURN dev.name AS candidate_name,
       dev.email AS candidate_email,
       count(pr) AS recent_prs_merged
ORDER BY recent_prs_merged DESC
LIMIT 3
"""

# Query 4: Auto-Patch Retrieval Context
# Fetches doc text alongside the recent PRs and diffs that caused the drift
QUERY_AUTO_PATCH_CONTEXT = """
MATCH (doc:DocPage {id: $doc_id})-[:DOCUMENTS]->(s:Service)
OPTIONAL MATCH (pr:PullRequest)-[:MODIFIED]->(s)
OPTIONAL MATCH (doc)-[:REFERENCES]->(ep:Endpoint)
RETURN doc.id AS doc_id,
       doc.title AS doc_title,
       doc.content AS doc_content,
       doc.last_updated AS doc_last_updated,
       s.name AS service_name,
       collect(DISTINCT {
           number: pr.number,
           title: pr.title,
           merged_at: pr.merged_at,
           diff_summary: pr.diff_summary,
           files_changed: pr.files_changed
       }) AS recent_prs,
       collect(DISTINCT {
           path: ep.path,
           method: ep.method,
           deprecated: ep.deprecated,
           current_status: ep.current_status
       }) AS endpoints
"""

# Query 5: Blast Radius Analysis
# Calculates ripple effect across docs and services when an endpoint or PR changes
QUERY_BLAST_RADIUS = """
MATCH (pr:PullRequest {number: $pr_number})-[:TOUCHED_ENDPOINT]->(ep:Endpoint)
OPTIONAL MATCH (doc:DocPage)-[:REFERENCES]->(ep)
OPTIONAL MATCH (doc)-[:HAS_SECTION]->(sec:Section)
RETURN ep.path AS endpoint_path,
       ep.method AS method,
       ep.deprecated AS is_deprecated,
       collect(DISTINCT doc.title) AS affected_docs,
       collect(DISTINCT sec.title) AS affected_sections
"""

# Query 6: Full Graph Dump for Visualization
QUERY_GET_ALL_NODES = """
MATCH (n)
RETURN labels(n) AS labels, properties(n) AS props
LIMIT 300
"""

QUERY_GET_ALL_EDGES = """
MATCH (a)-[r]->(b)
RETURN id(a) AS source_id,
       labels(a)[0] AS source_label,
       a.id AS source_business_id,
       a.name AS source_name,
       a.title AS source_title,
       type(r) AS rel_type,
       properties(r) AS rel_props,
       id(b) AS target_id,
       labels(b)[0] AS target_label,
       b.id AS target_business_id,
       b.name AS target_name,
       b.title AS target_title
LIMIT 500
"""

# Query 7: List Active Alerts
QUERY_GET_ACTIVE_ALERTS = """
MATCH (doc:DocPage)-[:FLAGGED_STALE]->(a:Alert)
OPTIONAL MATCH (doc)-[:DOCUMENTS]->(s:Service)
RETURN a.id AS alert_id,
       a.reason AS reason,
       a.severity AS severity,
       a.created_at AS created_at,
       a.suggested_patch AS suggested_patch,
       doc.id AS doc_id,
       doc.title AS doc_title,
       s.name AS service_name
ORDER BY a.severity DESC, a.created_at DESC
"""
