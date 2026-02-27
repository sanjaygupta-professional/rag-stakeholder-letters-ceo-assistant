"""Load context packages and themes into Neo4j. All operations use MERGE (idempotent)."""

import json
import logging
import os

logger = logging.getLogger(__name__)


def _make_letter_id(company: str, year: int) -> str:
    return f"{company.lower().replace(' ', '_')}_{year}"


def load_companies(session, context_packages: list[dict]) -> None:
    """Create Company nodes."""
    seen = set()
    for pkg in context_packages:
        meta = pkg["meta"]
        name = meta["company"]
        if name in seen:
            continue
        seen.add(name)
        session.run("""
            MERGE (c:Company {name: $name})
            SET c.sector = $sector,
                c.geography = $geography,
                c.stock_ticker = $ticker,
                c.index_benchmark = $benchmark
        """, name=name, sector=meta["sector"], geography=meta["geography"],
            ticker=meta["company_ticker"],
            benchmark="S&P 500" if meta["geography"] == "US" else "Nifty IT")
    logger.info("Companies: %d", len(seen))


def load_letters(session, context_packages: list[dict]) -> None:
    """Create Letter nodes and PUBLISHED relationships."""
    for pkg in context_packages:
        meta = pkg["meta"]
        lid = _make_letter_id(meta["company"], meta["letter_year"])
        session.run("""
            MERGE (l:Letter {letter_id: $lid})
            SET l.company_name = $company,
                l.year = $year,
                l.fiscal_year_covered = $fy,
                l.publication_date = $pub_date,
                l.author = $author,
                l.letter_type = $ltype,
                l.word_count = $wc,
                l.overall_sentiment_score = $sentiment,
                l.forward_looking_ratio = $flr
        """, lid=lid, company=meta["company"], year=meta["letter_year"],
            fy=meta["fiscal_year_covered"], pub_date=meta["publication_date"],
            author=meta["author"], ltype=meta["letter_type"],
            wc=pkg["during"]["word_count"],
            sentiment=pkg["during"].get("overall_sentiment_score"),
            flr=pkg["during"].get("forward_looking_ratio"))

        # PUBLISHED relationship
        session.run("""
            MATCH (c:Company {name: $company})
            MATCH (l:Letter {letter_id: $lid})
            MERGE (c)-[:PUBLISHED]->(l)
        """, company=meta["company"], lid=lid)
    logger.info("Letters: %d", len(context_packages))


def load_market_contexts(session, context_packages: list[dict]) -> None:
    """Create MarketContext nodes and WRITTEN_DURING relationships."""
    for pkg in context_packages:
        meta = pkg["meta"]
        lid = _make_letter_id(meta["company"], meta["letter_year"])
        cid = f"ctx_{lid}"
        before = pkg["before"]
        session.run("""
            MERGE (m:MarketContext {context_id: $cid})
            SET m.company_name = $company,
                m.year = $year,
                m.stock_price_30d_before = $p30,
                m.stock_price_on_date = $pon,
                m.analyst_buy_count = $buy,
                m.analyst_hold_count = $hold,
                m.analyst_sell_count = $sell,
                m.pre_letter_sentiment = $sentiment,
                m.key_analyst_concerns = $concerns
        """, cid=cid, company=meta["company"], year=meta["letter_year"],
            p30=before.get("stock_price_30d_before"),
            pon=before.get("stock_price_on_publication"),
            buy=before.get("analyst_recommendations", {}).get("buy") if before.get("analyst_recommendations") else None,
            hold=before.get("analyst_recommendations", {}).get("hold") if before.get("analyst_recommendations") else None,
            sell=before.get("analyst_recommendations", {}).get("sell") if before.get("analyst_recommendations") else None,
            sentiment=before.get("pre_letter_sentiment"),
            concerns=before.get("key_analyst_concerns"))

        session.run("""
            MATCH (l:Letter {letter_id: $lid})
            MATCH (m:MarketContext {context_id: $cid})
            MERGE (l)-[:WRITTEN_DURING]->(m)
        """, lid=lid, cid=cid)
    logger.info("MarketContexts: %d", len(context_packages))


def load_market_responses(session, context_packages: list[dict]) -> None:
    """Create MarketResponse nodes and TRIGGERED relationships."""
    for pkg in context_packages:
        meta = pkg["meta"]
        lid = _make_letter_id(meta["company"], meta["letter_year"])
        rid = f"resp_{lid}"
        after = pkg["after"]
        session.run("""
            MERGE (r:MarketResponse {response_id: $rid})
            SET r.company_name = $company,
                r.year = $year,
                r.stock_change_7d_pct = $s7,
                r.stock_change_30d_pct = $s30,
                r.benchmark_change_7d_pct = $b7,
                r.benchmark_change_30d_pct = $b30,
                r.relative_return_7d = $r7,
                r.relative_return_30d = $r30,
                r.sentiment_shift = $shift
        """, rid=rid, company=meta["company"], year=meta["letter_year"],
            s7=after.get("stock_change_7d_pct"),
            s30=after.get("stock_change_30d_pct"),
            b7=after.get("benchmark_change_7d_pct"),
            b30=after.get("benchmark_change_30d_pct"),
            r7=after.get("relative_return_7d_pct"),
            r30=after.get("relative_return_30d_pct"),
            shift=after.get("sentiment_shift"))

        session.run("""
            MATCH (l:Letter {letter_id: $lid})
            MATCH (r:MarketResponse {response_id: $rid})
            MERGE (l)-[:TRIGGERED]->(r)
        """, lid=lid, rid=rid)
    logger.info("MarketResponses: %d", len(context_packages))


def load_macro_conditions(session, context_packages: list[dict]) -> None:
    """Create MacroCondition nodes + SHAPED_BY and AFFECTED relationships."""
    seen = set()
    for pkg in context_packages:
        meta = pkg["meta"]
        lid = _make_letter_id(meta["company"], meta["letter_year"])
        cid = f"ctx_{lid}"
        macro = pkg["before"].get("macro_context", {})
        year = meta["letter_year"]

        # Create region-specific macro nodes for each year
        for region, context_key in [("US", "us_context"), ("India", "india_context"),
                                     ("Global", "global_context")]:
            mid = f"macro_{year}_{region.lower()}"
            context_text = macro.get(context_key, "")
            if not context_text and mid in seen:
                continue

            rate_key = "us_fed_rate" if region == "US" else ("india_rbi_repo_rate" if region == "India" else None)
            rate = macro.get(rate_key, "") if rate_key else ""

            if mid not in seen:
                session.run("""
                    MERGE (mc:MacroCondition {macro_id: $mid})
                    SET mc.year = $year,
                        mc.region = $region,
                        mc.interest_rate = $rate,
                        mc.key_factors = $factors,
                        mc.market_sentiment = $sentiment
                """, mid=mid, year=year, region=region, rate=rate,
                    factors=context_text,
                    sentiment="cautious")  # Simplified default
                seen.add(mid)

            # SHAPED_BY: MarketContext -> MacroCondition
            session.run("""
                MATCH (m:MarketContext {context_id: $cid})
                MATCH (mc:MacroCondition {macro_id: $mid})
                MERGE (m)-[:SHAPED_BY]->(mc)
            """, cid=cid, mid=mid)

            # AFFECTED: MacroCondition -> Company
            session.run("""
                MATCH (mc:MacroCondition {macro_id: $mid})
                MATCH (c:Company {name: $company})
                MERGE (mc)-[:AFFECTED]->(c)
            """, mid=mid, company=meta["company"])

    logger.info("MacroConditions: %d", len(seen))


def load_themes(session, context_packages: list[dict]) -> None:
    """Create Theme nodes and ADDRESSES_THEME relationships."""
    count = 0
    for pkg in context_packages:
        meta = pkg["meta"]
        lid = _make_letter_id(meta["company"], meta["letter_year"])
        themes = pkg["during"].get("themes", [])

        for i, theme in enumerate(themes):
            tid = f"{lid}_t{i+1}"
            session.run("""
                MERGE (t:Theme {theme_id: $tid})
                SET t.label = $label,
                    t.description = $desc,
                    t.sentiment_polarity = $sentiment,
                    t.temporal_orientation = $temporal,
                    t.confidence_level = $confidence,
                    t.key_quote = $quote,
                    t.cross_cultural_relevance = $ccr,
                    t.company = $company,
                    t.year = $year
            """, tid=tid, label=theme.get("label", ""),
                desc=theme.get("description", ""),
                sentiment=theme.get("sentiment_polarity", ""),
                temporal=theme.get("temporal_orientation", ""),
                confidence=theme.get("confidence_level", ""),
                quote=theme.get("key_quote", ""),
                ccr=theme.get("cross_cultural_relevance", 3),
                company=meta["company"], year=meta["letter_year"])

            session.run("""
                MATCH (l:Letter {letter_id: $lid})
                MATCH (t:Theme {theme_id: $tid})
                MERGE (l)-[:ADDRESSES_THEME]->(t)
            """, lid=lid, tid=tid)
            count += 1
    logger.info("Themes: %d", count)


def load_parallels(session, parallels: list[dict], context_packages: list[dict]) -> None:
    """Create PARALLELS relationships between cross-company themes."""
    # Build a lookup: (company_lower, year, theme_label_lower) -> theme_id
    theme_lookup = {}
    for pkg in context_packages:
        meta = pkg["meta"]
        lid = _make_letter_id(meta["company"], meta["letter_year"])
        for i, theme in enumerate(pkg["during"].get("themes", [])):
            key = (meta["company"].lower(), meta["letter_year"],
                   theme.get("label", "").lower().strip())
            theme_lookup[key] = f"{lid}_t{i+1}"

    count = 0
    for p in parallels:
        year = p.get("year")
        brk_label = p.get("berkshire_theme_label", "").lower().strip()
        infy_label = p.get("infosys_theme_label", "").lower().strip()
        score = p.get("similarity_score", 0.5)

        brk_id = theme_lookup.get(("berkshire hathaway", year, brk_label))
        infy_id = theme_lookup.get(("infosys", year, infy_label))

        if not brk_id or not infy_id:
            # Try fuzzy match — find closest label
            for key, tid in theme_lookup.items():
                if key[0] == "berkshire hathaway" and key[1] == year and not brk_id:
                    if brk_label in key[2] or key[2] in brk_label:
                        brk_id = tid
                if key[0] == "infosys" and key[1] == year and not infy_id:
                    if infy_label in key[2] or key[2] in infy_label:
                        infy_id = tid

        if brk_id and infy_id:
            session.run("""
                MATCH (t1:Theme {theme_id: $brk_id})
                MATCH (t2:Theme {theme_id: $infy_id})
                MERGE (t1)-[r:PARALLELS]->(t2)
                SET r.similarity_score = $score,
                    r.same_year = true,
                    r.parallel_description = $desc,
                    r.cultural_difference = $diff,
                    r.shared_driver = $driver
            """, brk_id=brk_id, infy_id=infy_id, score=score,
                desc=p.get("parallel_description", ""),
                diff=p.get("cultural_difference", ""),
                driver=p.get("shared_driver", ""))
            count += 1
    logger.info("PARALLELS relationships: %d", count)


def load_temporal_evolution(session, evolutions: list[dict],
                            context_packages: list[dict]) -> None:
    """Create EVOLVED_TO relationships for temporal theme evolution."""
    theme_lookup = {}
    for pkg in context_packages:
        meta = pkg["meta"]
        lid = _make_letter_id(meta["company"], meta["letter_year"])
        for i, theme in enumerate(pkg["during"].get("themes", [])):
            key = (meta["company"].lower(), meta["letter_year"],
                   theme.get("label", "").lower().strip())
            theme_lookup[key] = f"{lid}_t{i+1}"

    count = 0
    for evo in evolutions:
        company = evo.get("company", "").lower()
        from_year = evo.get("from_year")
        to_year = evo.get("to_year")
        from_label = evo.get("from_theme_label", "").lower().strip()
        to_label = evo.get("to_theme_label", "").lower().strip()

        from_id = theme_lookup.get((company, from_year, from_label))
        to_id = theme_lookup.get((company, to_year, to_label))

        # Fuzzy match fallback
        if not from_id:
            for key, tid in theme_lookup.items():
                if key[0] == company and key[1] == from_year:
                    if from_label in key[2] or key[2] in from_label:
                        from_id = tid
                        break
        if not to_id:
            for key, tid in theme_lookup.items():
                if key[0] == company and key[1] == to_year:
                    if to_label in key[2] or key[2] in to_label:
                        to_id = tid
                        break

        if from_id and to_id:
            session.run("""
                MATCH (t1:Theme {theme_id: $from_id})
                MATCH (t2:Theme {theme_id: $to_id})
                MERGE (t1)-[r:EVOLVED_TO]->(t2)
                SET r.years_gap = $gap,
                    r.evolution_description = $desc,
                    r.driver = $driver
            """, from_id=from_id, to_id=to_id,
                gap=evo.get("years_gap", 1),
                desc=evo.get("evolution_description", ""),
                driver=evo.get("driver", ""))
            count += 1
    logger.info("EVOLVED_TO relationships: %d", count)


def load_all(driver, context_packages_dir: str = "data/processed/context_packages",
             themes_dir: str = "data/themes") -> None:
    """Load everything into Neo4j from processed data files."""
    # Load context packages
    packages = []
    for fname in sorted(os.listdir(context_packages_dir)):
        if fname.endswith("_context.json"):
            with open(os.path.join(context_packages_dir, fname)) as f:
                packages.append(json.load(f))
    logger.info("Loaded %d context packages", len(packages))

    # Load parallel and evolution data
    parallels_path = os.path.join(themes_dir, "cross_company_parallels.json")
    parallels = []
    if os.path.exists(parallels_path):
        with open(parallels_path) as f:
            parallels = json.load(f)

    evolution_path = os.path.join(themes_dir, "temporal_evolution.json")
    evolutions = []
    if os.path.exists(evolution_path):
        with open(evolution_path) as f:
            evolutions = json.load(f)

    with driver.session() as session:
        load_companies(session, packages)
        load_letters(session, packages)
        load_market_contexts(session, packages)
        load_market_responses(session, packages)
        load_macro_conditions(session, packages)
        load_themes(session, packages)
        load_parallels(session, parallels, packages)
        load_temporal_evolution(session, evolutions, packages)

    logger.info("Graph loading complete.")
