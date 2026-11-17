"""Run the fixed test cases against the app, with no browser and no network.

    python run_cases.py            print a pass/fail table (Markdown, ready for TEST_RECORD.md)

Each case is: what the person sends, and a phrase the reply must contain. The cases never change
between runs, so a change to the code can be judged by running the same cases again (Lecture 09).
Decisions are written to a temporary file, never to your real decisions.jsonl.
"""
import os, sys, tempfile
import app, decisions, signal_card

decisions.LOG = os.path.join(tempfile.gettempdir(), "signal_assistant_cases.jsonl")
if os.path.exists(decisions.LOG):
    os.remove(decisions.LOG)

CARD = "{card}"   # replaced by the id of the card on screen when the case runs

CASES = [
    # (id, what it tests, message sent, phrase the reply must contain)
    ("G1", "ticker and horizon understood", "Is XYZ worth buying? I would hold 6 months.", "Understood as: XYZ, holding for 6 months"),
    ("G2", "two stocks: asks which one", "Is XYZ or ABC better for 1 year?", "one stock at a time"),
    ("G3", "missing horizon: asks", ["Start over", "What about ABC?"], "How long do you plan to hold ABC"),
    ("G4", "unknown ticker: declines and offers options", "Is NAN worth buying?", "I have no data for NAN"),
    ("S1", "supported signal", ["Start over", "XYZ for 6 months", "Confirm"], "XYZ: Buy, medium confidence"),
    ("S2", "too little evidence: low confidence", ["Start over", "ABC for 1 year", "Confirm"], "ABC: Sell, low confidence"),
    ("D1", "decision against the signal is recorded", ["Start over", "XYZ for 6 months", "Confirm", "__decide__:Sell:brief:" + CARD], "goes against the system's Buy signal"),
    ("D2", "repeated click writes nothing", "__decide__:Sell:brief:" + CARD, "Nothing new was written"),
    ("D3", "malformed decision refused", "__decide__:Maybe:brief:" + CARD, "must be Buy, Hold or Sell"),
    ("D4", "decision on a card not on screen refused", "__decide__:Buy:brief:oldcard", "no longer on screen"),
]

CHECKS = [
    # (id, what it tests, check on the signal card itself)
    ("S3", "stale 2025 report reported, not used", lambda: len(signal_card.build("XYZ", "6 months")["stale"]) == 1),
    ("S4", "evidence against the signal is shown", lambda: any(e["direction"] == "negative" for e in signal_card.build("XYZ", "6 months")["top"])),
    ("S5", "no evidence gives no signal", lambda: signal_card.build("NAN", "6 months")["signal"] == "No signal"),
]


def run():
    rows, failed = [], 0
    for cid, what, sent, expect in CASES:
        reply = ""
        for msg in (sent if isinstance(sent, list) else [sent]):
            card_id = app.LAST_CARD["id"] if app.LAST_CARD else "none"
            reply = app.turn(msg.replace(CARD, card_id))["reply"]
        ok = expect in reply
        failed += not ok
        rows.append((cid, what, expect, reply, ok))
    for cid, what, check in CHECKS:
        ok = bool(check())
        failed += not ok
        rows.append((cid, what, "(checked on the card)", "", ok))
    print("| Case | What it tests | Must contain | Result |")
    print("|---|---|---|---|")
    for cid, what, expect, reply, ok in rows:
        print("| %s | %s | %s | %s |" % (cid, what, expect, "PASS" if ok else "FAIL: " + reply[:60]))
    print("\n%d of %d passed" % (len(rows) - failed, len(rows)))
    os.remove(decisions.LOG)
    return failed


if __name__ == "__main__":
    sys.exit(1 if run() else 0)