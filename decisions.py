"""Record the person's own decision about a signal: one narrow tool, after Lecture 12.

    python decisions.py --selftest

It only appends a line to decisions.jsonl in this folder. It cannot buy or sell anything:
there is no broker connection, by design.
"""
import datetime, json, os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "decisions.jsonl")
CHOICES = ["Buy", "Hold", "Sell"]
VIEWS = ["brief", "detailed"]


def valid(call, card):
    """Shape and precondition checks. Returns (ok, reason) so the reason can be shown to the person."""
    a = call.get("arguments") or {}
    if call.get("name") != "record_decision":
        return False, "this is not a record_decision request"
    if a.get("decision") not in CHOICES:
        return False, "the decision must be Buy, Hold or Sell"
    if a.get("view") not in VIEWS:
        return False, "the view must be brief or detailed"
    if not card or a.get("card_id") != card.get("id"):
        return False, "that signal is no longer on screen, so there is nothing to decide about"
    return True, ""


def _read():
    if not os.path.exists(LOG):
        return []
    with open(LOG, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run(call, card):
    """Record one decision per signal card. A repeat returns the existing record and writes nothing."""
    a = call["arguments"]
    for r in _read():
        if r["card_id"] == a["card_id"] and not r.get("undone"):
            return dict(r, repeated=True)
    record = {"id": uuid.uuid4().hex[:8], "card_id": a["card_id"],
              "time": datetime.datetime.now().isoformat(timespec="seconds"),
              "ticker": card["ticker"], "horizon": card["horizon"], "signal": card["signal"],
              "confidence": card["confidence"], "view": a["view"], "decision": a["decision"],
              "followed_signal": a["decision"] == card["signal"]}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def undo(record_id):
    """Mark a decision as undone. The line stays in the log, so the history is honest."""
    rows, hit = _read(), None
    for r in rows:
        if r["id"] == record_id and not r.get("undone"):
            r["undone"] = True
            hit = r
    if hit:
        with open(LOG, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
    return hit


def receipt(r):
    """What the screen says, built from the returned record, not from a guess."""
    if r.get("repeated"):
        return ("Already recorded for this signal: %s. Nothing new was written. "
                "Undo it first if you want to change it." % r["decision"])
    side = "follows" if r["followed_signal"] else "goes against"
    return ("Recorded as your decision: %s %s (%s). It %s the system's %s signal. "
            "Saved to decisions.jsonl only. No trade was placed." % (
                r["decision"], r["ticker"], r["horizon"], side, r["signal"]))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        LOG = os.path.join(HERE, "selftest_decisions.jsonl")
        if os.path.exists(LOG):
            os.remove(LOG)
        card = {"id": "c1", "ticker": "XYZ", "horizon": "6 months", "signal": "Buy", "confidence": "medium"}
        call = {"name": "record_decision", "arguments": {"card_id": "c1", "decision": "Sell", "view": "brief"}}
        assert valid(call, card)[0]
        assert not valid({"name": "record_decision", "arguments": {"card_id": "c1", "decision": "Maybe", "view": "brief"}}, card)[0]
        assert not valid({"name": "record_decision", "arguments": {"card_id": "old", "decision": "Buy", "view": "brief"}}, card)[0]
        first = run(call, card)
        assert first["followed_signal"] is False
        assert run(call, card).get("repeated"), "a repeated click must not write twice"
        assert undo(first["id"])["undone"]
        assert len(_read()) == 1
        os.remove(LOG)
        print("ok: valid call accepted, 2 bad calls refused, repeat ignored, undo kept in log")
        sys.exit(0)