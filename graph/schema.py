"""
Graph Schema definitions, indices, and node/relationship specifications for FalkorDB.
"""

# Schema indices for high-performance Cypher execution in FalkorDB
CREATE_INDEX_STATEMENTS = [
    "CREATE INDEX FOR (d:DocPage) ON (d.id)",
    "CREATE INDEX FOR (s:Service) ON (s.id)",
    "CREATE INDEX FOR (s:Service) ON (s.name)",
    "CREATE INDEX FOR (dev:Developer) ON (dev.id)",
    "CREATE INDEX FOR (dev:Developer) ON (dev.email)",
    "CREATE INDEX FOR (pr:PullRequest) ON (pr.id)",
    "CREATE INDEX FOR (pr:PullRequest) ON (pr.number)",
    "CREATE INDEX FOR (ep:Endpoint) ON (ep.path)",
    "CREATE INDEX FOR (a:Alert) ON (a.id)",
]

# Track 01 & Track 03 Model Definitions
NODE_LABELS = {
    "DocPage": "Company documentation articles, wikis, Notion/Confluence pages, and READMEs",
    "Section": "Specific headings or sub-sections within a documentation page",
    "Service": "Microservices, background workers, or backend applications in production",
    "CodeRepo": "Version control repositories hosting the codebases",
    "Endpoint": "REST/gRPC API routes, parameters, and contracts",
    "Developer": "Engineers, team leads, and former team members",
    "PullRequest": "Merged pull requests and code modifications that trigger drift",
    "Alert": "Staleness, orphaned maintainer, or deprecated endpoint warnings"
}

RELATIONSHIPS = {
    "DOCUMENTS": "(DocPage)-[:DOCUMENTS]->(Service)",
    "AUTHORED_BY": "(DocPage)-[:AUTHORED_BY]->(Developer) and (PullRequest)-[:AUTHORED_BY]->(Developer)",
    "HAS_SECTION": "(DocPage)-[:HAS_SECTION]->(Section)",
    "REFERENCES": "(DocPage)-[:REFERENCES]->(Endpoint)",
    "MODIFIED": "(PullRequest)-[:MODIFIED]->(Service)",
    "TOUCHED_ENDPOINT": "(PullRequest)-[:TOUCHED_ENDPOINT]->(Endpoint)",
    "LEFT_COMPANY": "(Developer)-[:LEFT_COMPANY]->(Service)",
    "FLAGGED_STALE": "(DocPage)-[:FLAGGED_STALE]->(Alert)"
}
