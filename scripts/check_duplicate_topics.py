#!/usr/bin/env python3
"""Detect likely duplicate blog topics from front matter and article briefs.

This is intentionally conservative: it reports candidates for editorial review.
A non-zero exit prevents a new post from being merged until the overlap is resolved
or the post scopes are made clearly distinct.
"""
from pathlib import Path
import re, sys
from itertools import combinations

POSTS=Path("_posts")
FIELDS=("対象読者","この記事で伝えること","Reader","Question","Scope","Primary sources")
STOP={"する","について","記事","実装","仕様","処理","確認","どの","よう","the","and","for","with","from","into"}

def norm(s):
    s=s.lower().replace("／","/").replace("：",":")
    return set(x for x in re.findall(r"[a-z0-9_.:/§-]+|[\u3040-\u30ff\u3400-\u9fff]{2,}",s) if x not in STOP)

def extract(path):
    text=path.read_text(encoding="utf-8")
    title=re.search(r'^title:\s*["\']?(.*?)["\']?\s*$',text,re.M)
    vals=[title.group(1) if title else ""]
    for key in FIELDS:
        vals += re.findall(rf'(?:\*\*)?{re.escape(key)}(?:\*\*)?\s*:\s*(.+)',text,re.I)
    # Standards/section and protocol nouns are strong duplicate signals.
    vals += re.findall(r'RFC\s*\d+|§\s*[\d.]+|OpenID Connect|WebAuthn|SCIM|PAR|PATCH|ID Token|conditional mediation|related origin\w*|Group membership',text,re.I)[:30]
    return text, norm(" ".join(vals))

def score(a,b):
    if not a or not b: return 0
    return len(a&b)/min(len(a),len(b))

docs={p:extract(p) for p in sorted(POSTS.glob("*.md"))}
hits=[]
for (pa,(ta,a)),(pb,(tb,b)) in combinations(docs.items(),2):
    s=score(a,b)
    # High overlap is a review blocker. Same explicit feature phrases lower the threshold.
    phrases=("scim patch","group membership","conditional mediation","related origin","pushed authorization","id token")
    same_feature=any(q in ta.lower() and q in tb.lower() for q in phrases)
    if s>=0.58 or (same_feature and s>=0.38):
        hits.append((s,pa,pb))
if hits:
    print("Potential duplicate article topics detected:",file=sys.stderr)
    for s,a,b in sorted(hits,reverse=True):
        print(f"  {s:.2f}  {a}  <->  {b}",file=sys.stderr)
    print("Review Reader / Question / Scope. Update or merge the canonical article instead of creating a near-duplicate.",file=sys.stderr)
    sys.exit(1)
print("No likely duplicate article topics detected.")
