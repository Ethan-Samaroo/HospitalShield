
from research import consolidate_events

corroboration = {
    "event_key": "portal bridge",
    "status": "Confirmed planned service changes",
    "source_url": "https://www.njtransit.com/portalcut",
}

findings = [
    {
        "title": "CBS report",
        "url": "https://example.com/cbs",
        "event_corroboration": corroboration,
    },
    {
        "title": "NorthJersey report",
        "url": "https://example.com/nj",
        "event_corroboration": corroboration,
    },
    {
        "title": "PIX11 report",
        "url": "https://example.com/pix",
        "event_corroboration": corroboration,
    },
]

results = consolidate_events(findings)

# All three reports should be consolidated into one event.
assert len(results) == 1, "Expected one consolidated event"

# All three distinct article URLs should be retained.
sources = results[0]["supporting_sources"]
assert len(sources) == 3, "Expected three supporting articles"

source_urls = {source["url"] for source in sources}
assert source_urls == {
    "https://example.com/cbs",
    "https://example.com/nj",
    "https://example.com/pix",
}, "One or more supporting URLs are missing"

# The event's corroboration details should be preserved.
assert (
    results[0]["event_corroboration"]["status"]
    == "Confirmed planned service changes"
), "Event corroboration status was not preserved"

print("PASS: Three reports consolidated into one event.")
print("PASS: All three supporting URLs were retained.")
print("PASS: Event corroboration details were preserved.")
