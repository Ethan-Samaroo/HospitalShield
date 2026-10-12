import re
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()



from urllib.parse import urlparse


OFFICIAL_DOMAINS = {
    "mta.info",
    "njtransit.com",
    "weather.gov",
    "panynj.gov",
    "nyc.gov",
}



from datetime import datetime, timezone
from urllib.parse import urlparse


OFFICIAL_DOMAINS = {
    "mta.info",
    "njtransit.com",
    "weather.gov",
    "panynj.gov",
    "nyc.gov",
}

MANUAL_CORROBORATIONS = [
    {
        "event_key": "portal bridge",
        "event_title": "Portal Bridge Cutover",
        "source_title": "NJ TRANSIT Portal Bridge Cutover",
        "source_url": "https://www.njtransit.com/portalcut",
        "status": "Confirmed planned service changes",
        "date_range": "October 11-November 14, 2026",
        "notes": (
            "NJ TRANSIT reports temporary rail schedule changes "
            "during cutover work. Regular schedules are expected "
            "to resume November 15, subject to safety testing."
        ),
    }
]


GENERIC_PAGE_TERMS = [
    "new-york-city-transit",
    "/guides/",
    "skywarn",
    "weekly-traffic-advisory",
    "/agency/",
    "destinations/beaches",
    "first-alert-weather",
    "weather-forecast",
]

DISRUPTION_TERMS = [
    "service disruption",
    "service suspended",
    "service changes",
    "service delay",
    "rail schedule",
    "road closure",
    "power outage",
    "flooding",
    "weather warning",
    "weather alert",
    "planned work",
    "skipping stops",
    "service changes",
    "track maintenance",
    "service suspended",
    "service disruption",
    "delays",
    "cancellations",
    "reduced service",
]



def assess_evidence(finding: dict) -> dict:
    """Check source quality, relevance, and dates in a search result."""

    url = finding.get("url", "")
    host = (urlparse(url).hostname or "").lower()
    host = host.removeprefix("www.")

    title = finding.get("title", "")
    content = finding.get("content", "")
    title_text = title.lower()
    content_text = content.lower()

    is_official = any(
        host == domain or host.endswith("." + domain)
        for domain in OFFICIAL_DOMAINS
    )

    is_generic = any(
        term in url.lower() for term in GENERIC_PAGE_TERMS
    )

    
    disruption_phrases = (
        "service disruption",
        "service disruptions",
        "service suspended",
        "service suspension",
        "service changes",
        "delays",
        "cancellations",
        "cancelled",
        "canceled",
        "skipping stops",
        "track maintenance",
        "severe weather alert",
        "weather warning",
        "emergency alert issued",
        "evacuation order",
        "service suspended",
        "service disruptions",
        "road closed",
        "roads closed",
        "power outage reported",
        "transit strike",
        "road closures",
        "road closure",
        "power outage",
        "transit strike",
        "service interruption",
        "service interruptions",
        "planned service changes",
        "track work",
        "bridge work",
        "delays expected",
        "mass delays",
    )

    has_disruption_terms = any(
        phrase in title_text
        for phrase in disruption_phrases
    )


    today = datetime.now(timezone.utc).date()
    published = finding.get("published_date")

    recent_publication = False
    current_event_date = False
    date_status = "Publication and event dates unknown"

    # First, check the publication date supplied by the search API.
    if published:
        try:
            try:
                parsed = datetime.fromisoformat(
                    published.replace("Z", "+00:00")
                )
            except ValueError:
                from email.utils import parsedate_to_datetime
                parsed = parsedate_to_datetime(published)

            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)

            age_days = (datetime.now(timezone.utc) - parsed).total_seconds() / 86400

            if 0 <= age_days <= 7:
                recent_publication = True
                date_status = "Published within the last 7 days"
            elif age_days < 0:
                date_status = "Publication date is in the future; check it"
            else:
                date_status = "Older than 7 days"
        except (ValueError, TypeError, AttributeError):
            date_status = "Publication date could not be parsed"

    # If publication metadata is missing, look for an explicit
    # month/day/year date or date range in the title and snippet.
    if not published or not recent_publication:
        date_text = f"{title} {content[:1000]}"

        months = (
            "January February March April May June July "
            "August September October November December"
        )
        month_pattern = (
            r"\b(" + months.replace(" ", "|") + r")\s+"
            r"(\d{1,2})"
            r"(?:\s*[–—-]\s*(\d{1,2}))?"
            r",?\s+(\d{4})\b"
        )

        match = re.search(month_pattern, date_text, re.IGNORECASE)

        if match:
            month_name, first_day, last_day, year = match.groups()

            try:
                start_date = datetime.strptime(
                    f"{month_name} {first_day} {year}",
                    "%B %d %Y",
                ).date()

                end_date = start_date

                if last_day:
                    end_date = start_date.replace(day=int(last_day))

                if start_date <= today <= end_date:
                    current_event_date = True
                    date_status = (
                        "Event dates include today; "
                        "publication date unknown"
                    )
                elif end_date < today:
                    date_status = (
                        "Event dates have passed; "
                        "current status unconfirmed"
                    )
                else:
                    date_status = (
                        "Future event dates; "
                        "check whether they are relevant"
                    )

            except ValueError:
                date_status = "Date mentioned but could not be parsed"

    # Classify relevance separately from date status.
    if is_generic:
        relevance = "Generic page — not a specific disruption report"
    elif not has_disruption_terms:
        relevance = "No clear disruption identified in the text"
    else:
        relevance = "Possible disruption — details need verification"

    source_status = (
        "Official domain"
        if is_official
        else "Secondary source — corroboration needed"
    )

    # Only retain specific, potentially relevant reports with a
    # recent publication date or event dates that include today.
    if is_generic:
        disposition = "Exclude from disruption candidates"
    elif not has_disruption_terms:
        disposition = "Low relevance"
    elif recent_publication or current_event_date:
        disposition = "Candidate for further verification"
    else:
        disposition = "Needs date verification"
   
    return {
        "source_status": source_status,
        "date_status": date_status,
        "relevance": relevance,
        "disposition": disposition,
        "verified": False,
        "verification_note": (
            "Official source; specific claim still needs review."
            if source_status == "Official domain"
            else "Secondary source; seek official corroboration."
        ),
    }


def find_event_corroboration(finding: dict) -> dict | None:
    """Match research results to a manually recorded official event."""

    text = " ".join([
        finding.get("title", ""),
        finding.get("content", ""),
        finding.get("url", ""),
    ]).lower()

    for event in MANUAL_CORROBORATIONS:
        if event["event_key"].lower() in text:
            return event

        # Recognize alternate wording for the same recorded event.
        portal_terms = (
            "portal north bridge",
            "portal bridge north",
            "portal cutover",
        )
        transit_terms = (
            "nj transit",
            "rail service",
            "rail disruptions",
        )

        if (
            any(term in text for term in portal_terms)
            and any(term in text for term in transit_terms)
        ):
            return event

    return None



def clean_research_content(title: str, content: str) -> str:
    """Remove unrelated headlines from noisy search snippets."""

    if not content:
        return "No summary was provided by the search source."

    cleaned = content.replace(title, "").strip()

    # Remove common page-navigation text.
    cleaned = re.sub(r"(?im)^\s*watch CBS News\s*$", "", cleaned)

    # Stop when the snippet appears to switch to another headline.
    unrelated_headlines = [
        "First Alert Weather:",
        "Starfish smoked seafood",
    ]

    for phrase in unrelated_headlines:
        position = cleaned.lower().find(phrase.lower())
        if position >= 0:
            cleaned = cleaned[:position].strip()

    cleaned = re.sub(r"\n{2,}", "\n", cleaned).strip()

    return cleaned[:600] or (
        "Search result matched the title, but no clean summary was available."
    )

def consolidate_events(findings: list[dict]) -> list[dict]:
    """Show each corroborated event once, retaining supporting reports."""

    events = {}

    for finding in findings:
        corroboration = finding.get("event_corroboration")

        if corroboration:
            # Articles matched to the same recorded event share one key.
            key = f"event:{corroboration['event_key']}"
        else:
            # Keep unrelated or uncorroborated reports separate.
            key = f"url:{finding.get('url', finding.get('title', 'unknown'))}"

        if key not in events:
            event = finding.copy()
            event["supporting_sources"] = [{
                "title": finding.get("title", "Untitled"),
                "url": finding.get("url", ""),
                "source_status": finding.get("source_status", ""),
                "published_date": finding.get("published_date"),
            }]
            events[key] = event

        else:
            existing = events[key]

            # Retain each distinct article as a supporting source.
            source_url = finding.get("url", "")
            known_urls = {
                source.get("url")
                for source in existing["supporting_sources"]
            }

            if source_url and source_url not in known_urls:
                existing["supporting_sources"].append({
                    "title": finding.get("title", "Untitled"),
                    "url": source_url,
                    "source_status": finding.get("source_status", ""),
                    "published_date": finding.get("published_date"),
                })

    return list(events.values())

def research_disruptions(query: str) -> list[dict]:
    """Search official sources and broader news for possible disruptions."""

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise ValueError("TAVILY_API_KEY is missing from .env")

    tavily = TavilyClient(api_key=api_key)

    
    searches = [
        {
            "label": "Official transit sources",
            "query": (
                "site:njtransit.com service disruptions "
                "OR site:mta.info service alerts "
                "New York October 2026"
            ),
        },
        {
            "label": "Official weather alerts",
            "query": (
                "site:weather.gov New York active weather warnings "
                "October 11 2026"
            ),
        },
        {
            "label": "Broader transit news",
            "query": (
                "NJ Transit MTA confirmed service disruption "
                "schedule changes New York October 2026"
            ),
        },
    ]


    results = []
    seen_urls = set()

    for search in searches:
        try:
            response = tavily.search(
                query=search["query"],
                search_depth="advanced",
                topic="news",
                days=7,
                max_results=5,
                include_answer=False,
            )
        except Exception as error:
            print(f"{search['label']} search failed: {error}")
            continue

        for item in response.get("results", []):
            url = item.get("url", "")

            if url in seen_urls:
                continue

            seen_urls.add(url)

            
            title = item.get("title", "Untitled")
            content = clean_research_content(
                title,
                item.get("content", ""),
            )

            finding = {
                "title": title,
                "url": url,
                "content": content,
                "score": item.get("score"),
                "published_date": item.get("published_date"),
                "search_type": search["label"],
            }

            finding.update(assess_evidence(finding))
            results.append(finding)

            results[-1].update(assess_evidence(results[-1]))
    

    
    print(f"\nTotal search results before filtering: {len(results)}")

    for finding in results:
        print(
            f"Title: {finding['title']}\n"
            f"Relevance: {finding['relevance']}\n"
            f"Date: {finding['date_status']}\n"
            f"Disposition: {finding['disposition']}\n"
        )

    
    filtered_results = [
        finding for finding in results
        if finding.get("disposition") in (
            "Candidate for further verification",
            "Needs date verification",
        )
    ]

    for finding in filtered_results:
        corroboration = find_event_corroboration(finding)
        if corroboration:
            finding["event_corroboration"] = corroboration

    return consolidate_events(filtered_results)



if __name__ == "__main__":
    findings = research_disruptions(
        "official active weather alerts and public transit disruptions "
        "Long Island New York"
    )

    if not findings:
        print("No results returned. This does not prove no disruptions exist.")

    
    
    for finding in findings:
        finding.update(assess_evidence(finding))

        corroboration = find_event_corroboration(finding)

        if corroboration:
            finding["event_corroboration"] = corroboration
        else:
            finding["event_corroboration"] = None


        print(f"\nTitle: {finding['title']}")
        print(f"Published: {finding.get('published_date') or 'Unknown'}")
        print(f"URL: {finding['url']}")
        print(f"Source status: {finding['source_status']}")
        print(f"Date status: {finding['date_status']}")
        print(f"Relevance: {finding['relevance']}")
        print(f"Disposition: {finding['disposition']}")
        print(f"Verified: {finding['verified']}")
        print("Verification note:", finding["verification_note"])
        
        corroboration = finding.get("event_corroboration")

        if corroboration:
            print("Event corroboration:", corroboration["status"])
            print("Official source:", corroboration["source_url"])
        else:
            print("Event corroboration: None")

        print(f"Evidence: {finding['content'][:250]}")
