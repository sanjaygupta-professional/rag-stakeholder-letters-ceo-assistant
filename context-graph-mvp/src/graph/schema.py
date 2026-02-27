"""Neo4j schema creation — constraints and indexes for the Context Graph."""

import logging

logger = logging.getLogger(__name__)

# Constraints ensure uniqueness and create implicit indexes.
CONSTRAINTS = [
    "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT letter_id IF NOT EXISTS FOR (l:Letter) REQUIRE l.letter_id IS UNIQUE",
    "CREATE CONSTRAINT theme_id IF NOT EXISTS FOR (t:Theme) REQUIRE t.theme_id IS UNIQUE",
    "CREATE CONSTRAINT market_ctx_id IF NOT EXISTS FOR (m:MarketContext) REQUIRE m.context_id IS UNIQUE",
    "CREATE CONSTRAINT market_resp_id IF NOT EXISTS FOR (r:MarketResponse) REQUIRE r.response_id IS UNIQUE",
    "CREATE CONSTRAINT macro_id IF NOT EXISTS FOR (mc:MacroCondition) REQUIRE mc.macro_id IS UNIQUE",
]


def create_schema(driver) -> None:
    """Create all constraints. Safe to run multiple times."""
    with driver.session() as session:
        for cypher in CONSTRAINTS:
            try:
                session.run(cypher)
                logger.info("OK: %s", cypher.split("FOR")[0].strip())
            except Exception as e:
                # Constraint may already exist
                if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                    logger.info("SKIP (exists): %s", cypher.split("FOR")[0].strip())
                else:
                    logger.warning("Constraint failed: %s — %s", cypher[:60], e)


def get_node_counts(driver) -> dict[str, int]:
    """Return count of each node label in the graph."""
    labels = ["Company", "Letter", "Theme", "MarketContext", "MarketResponse", "MacroCondition"]
    counts = {}
    with driver.session() as session:
        for label in labels:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
            counts[label] = result.single()["cnt"]
    return counts


def get_relationship_counts(driver) -> dict[str, int]:
    """Return count of each relationship type."""
    rel_types = ["PUBLISHED", "WRITTEN_DURING", "ADDRESSES_THEME", "TRIGGERED",
                 "SHAPED_BY", "PARALLELS", "EVOLVED_TO", "AFFECTED"]
    counts = {}
    with driver.session() as session:
        for rt in rel_types:
            result = session.run(f"MATCH ()-[r:{rt}]->() RETURN count(r) AS cnt")
            counts[rt] = result.single()["cnt"]
    return counts
