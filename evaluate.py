"""Small original diagnostic set, not a benchmark of outdoor usefulness."""
import json
import statistics
import time
from pathlib import Path
from urllib.request import Request, urlopen

CASES = [
    ("I want to hear rustling and chirping without moving", 5, "sound-map"),
    ("I'd like to doodle what I see from a bench", 20, "tiny-sketch"),
    ("I want a stroll and conversation with a companion", 20, "friend-stroll"),
    ("I want to watch the shapes drifting above me", 10, "cloud-story"),
    ("I'd like to compare changes in my potted plants", 10, "garden-check"),
    ("I want to study the veins and edges of a leaf", 5, "leaf-lines"),
    ("I'd like to write a short poem using a sound and a color", 10, "pattern-poem"),
    ("I want a little walk to look at brick and stone patterns", 10, "texture-walk"),
]
rows = []
for query, minutes, expected in CASES:
    start = time.perf_counter()
    req = Request("http://127.0.0.1:8797/api/select", data=json.dumps(dict(query=query, minutes=minutes)).encode(),
                  headers={"Content-Type":"application/json"})
    with urlopen(req) as r:
        matches = json.load(r)["matches"]
    rows.append(dict(query=query, expected=expected, top1=matches[0]["id"] if matches else None,
                     top3=[c["id"] for c in matches], milliseconds=round((time.perf_counter()-start)*1000,2)))
report = dict(description="Eight author-written English diagnostic queries. No independent users or field test.",
              model="sentence-transformers/all-MiniLM-L6-v2", revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
              top1=sum(r["top1"]==r["expected"] for r in rows),
              top3=sum(r["expected"] in r["top3"] for r in rows), total=len(rows),
              median_ms=round(statistics.median(r["milliseconds"] for r in rows),2), cases=rows)
Path("docs/evaluation.json").write_text(json.dumps(report, indent=2)+"\n")
print(json.dumps(report, indent=2))
