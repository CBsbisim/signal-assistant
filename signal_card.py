"""Turn all the evidence for one stock into a signal card.

    python signal_card.py XYZ          print the card for XYZ
    python signal_card.py --selftest   check the XYZ and ABC cases

SIMULATED: each evidence file carries a hand-written direction (positive / negative / neutral).
A real system would infer it from the text [planned]. Everything after that step is real code.
"""
import datetime, json, re, sys
import retrieve

VOTE = {"positive": 1, "negative": -1, "neutral": 0}
MIN_SOURCES = 3   # with fewer independent sources than this, confidence is never above "low"
SHOW = 3          # evidence items shown on the card; the rest sit behind "Show all"
RULE = ("Each source gets one vote: up, down or neutral. If the net agreement is under 40%%, the signal is Hold. "
        "Otherwise it follows the majority. Confidence is high at 75%% agreement or more, medium at 40%% or more, "
        "and always low with fewer than %d sources." % MIN_SOURCES)

def evidence_for(ticker, passages=None):
    """Every passage that names the ticker, split into evidence to use and evidence replaced by a newer source."""
    passages = passages if passages is not None else retrieve.load()
    mine = [p for p in passages if re.search(r"\b%s\b" % ticker, p["text"])]
    current, replaced = [], []
    for p in mine:
        newer = [q for q in mine if q["section"] == p["section"] and not q["superseded"]]
        if p["superseded"] and newer:
            replaced.append(p)
        else:
            current.append(p)
    return current, replaced


def item(p, today):
    return {"text": p["text"], "source": p["source"], "date": p["date"], "direction": p["direction"],
            "days_old": (today - datetime.date.fromisoformat(p["date"])).days}


def build(ticker, horizon, today=None):
    today = today or datetime.date.today()
    current, replaced = evidence_for(ticker)
    if not current:
        return {"ticker": ticker, "horizon": horizon, "signal": "No signal", "confidence": "none",
        "reason": "I have no current evidence for %s, so I give no signal." % ticker,
        "top": [], "all": [], "stale": [], "simulated": __doc__.split("SIMULATED: ")[1].split("\n\n")[0]}

    newest = sorted(current, key=lambda p: p["date"], reverse=True)
    sources = {}
    for p in newest:
        sources.setdefault(p["section"], p)            # one vote per source, not per paragraph
    votes = [VOTE.get(p["direction"], 0) for p in sources.values()]
    total, n = sum(votes), len(votes)
    agreement = abs(total) / n

    if total == 0 or agreement < 0.4:
        signal = "Hold"
    else:
        signal = "Buy" if total > 0 else "Sell"
    if n < MIN_SOURCES:
        confidence = "low"
    elif agreement >= 0.75:
        confidence = "high"
    elif agreement >= 0.4:
        confidence = "medium"
    else:
        confidence = "low"

    up, down = votes.count(1), votes.count(-1)
    reason = "Sources: %d up, %d down, %d neutral." % (up, down, n - up - down)
    if n < MIN_SOURCES:
        reason += " With only %d source%s, confidence stays low." % (n, "" if n == 1 else "s")

    top = list(sources.values())[:SHOW]
    sign = {"Buy": 1, "Sell": -1}.get(signal, 0)
    against = [p for p in sources.values() if sign and VOTE.get(p["direction"], 0) == -sign]
    if against and not any(p in top for p in against):
        top[-1] = against[0]                           # always show the strongest evidence against the signal

    stale = ["Not used: %s, dated %s, has been replaced by a newer source in the same section."
             % (p["source"], p["date"]) for p in replaced]
    stale += ["Out of date: %s, dated %s, is marked superseded and has no newer replacement. Check a current source."
              % (p["source"], p["date"]) for p in current if p["superseded"]]

    breakdown = [{"section": p["section"], "source": p["source"], "date": p["date"], "direction": p["direction"],
                  "vote": VOTE.get(p["direction"], 0)} for p in sources.values()]
    not_used = ["%s, dated %s: replaced by a newer source." % (p["source"], p["date"]) for p in replaced]
    not_used.append("Your holding period (%s): shown, but not yet used to weight the evidence [planned]." % horizon)
    not_used.append("Anything after the newest date above: this simulated feed has no live data [planned].")

    return {"ticker": ticker, "horizon": horizon, "signal": signal, "confidence": confidence, "reason": reason,
            "top": [item(p, today) for p in top], "all": [item(p, today) for p in newest], "stale": stale,
            "breakdown": breakdown, "not_used": not_used, "rule": RULE,
            "simulated": __doc__.split("SIMULATED: ")[1].split("\n\n")[0]}


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        xyz, abc = build("XYZ", "6 months"), build("ABC", "6 months")
        assert (xyz["signal"], xyz["confidence"]) == ("Buy", "medium"), xyz
        assert any(e["direction"] == "negative" for e in xyz["top"]), "evidence against is missing"
        assert len(xyz["stale"]) == 1, "the 2025 earnings report should be reported as replaced"
        assert (abc["signal"], abc["confidence"]) == ("Sell", "low"), abc
        assert len(xyz["breakdown"]) == 4 and len(xyz["not_used"]) == 3, "detailed view is incomplete"
        print("ok: XYZ Buy/medium with 1 replaced source, ABC Sell/low")
        sys.exit(0)
    print(json.dumps(build(sys.argv[1] if len(sys.argv) > 1 else "XYZ", "6 months"), indent=2))