"""The supplied Lab 4 prototype.

    python app.py            serve on 8000
    python app.py --port 8001

The two turns below are local code: they work with no model at all. The model is only asked for the
ordinary case, and its reply is checked before anything is rendered.
"""
import json, os, re, sys, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import model  # noqa: E402
import retrieve  # noqa: E402  
import tools  # noqa: E402     
import vlm  # noqa: E402   
import signal_card  # noqa: E402  Step 3: evidence -> signal, confidence, dated evidence
import decisions  # noqa: E402    Step 5: record the person's own decision
HERE = os.path.dirname(os.path.abspath(__file__))
PENDING_TOOL = None          # a validated call waiting for the user's Confirm
MIN_SCORE = 0.25           # below this, a retrieval hit is not treated as evidence
SCHEMA = {"reply": str, "options": list, "action": (dict, type(None)), "unsupported_claims": list}
APPOINTMENTS = [{"id": "derm-14nov", "clinic": "Dermatology", "date": "14 Nov", "time": "10:20"},
                {"id": "physio-20nov", "clinic": "Physiotherapy", "date": "20 Nov", "time": "09:00"}]
TICKERS = ["XYZ", "ABC"]                      # stocks the simulated corpus covers
HORIZONS = ["1 month", "6 months", "1 year"]  # offered when the person gives no horizon
QUERY = {"ticker": None, "horizon": None}     # what the system has understood so far
LAST_CARD = None                              # the signal currently on screen

def valid(data):
    return isinstance(data, dict) and all(k in data and isinstance(data[k], t) for k, t in SCHEMA.items())

def fallback_turn():
    """A malformed reply is a caught error, never a blank page."""
    return {"reply": "I could not read the reply, so I have not changed anything. Try again or ask the module lead.",
            "options": [], "action": None, "unsupported_claims": []}

def clarification_turn(candidates):
    names = " or ".join("%s on %s" % (a["clinic"], a["date"]) for a in candidates)
    return {"reply": "Which appointment: %s?" % names,
            "options": [a["id"] for a in candidates], "action": None, "unsupported_claims": []}

def decline_turn():
    return {"reply": "Dr Achebe has no clinic next week, and I cannot see your dialysis days, so I cannot "
                     "avoid them. Here are the open slots; you choose.",
            "options": ["Thu 09:40", "Fri 14:10"], "action": None, "unsupported_claims": ["clinic availability beyond next week"]}

def understand(message):
    """Fill in the ticker and horizon the message mentions. Return a problem to ask about, if any."""
    found = [t for t in TICKERS if re.search(r"\b%s\b" % t, message, re.I)]
    m = re.search(r"(\d+)\s*(week|month|year)", message, re.I)
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        QUERY["horizon"] = "%d %s%s" % (n, unit, "" if n == 1 else "s")
    if len(found) > 1:
        QUERY["ticker"] = None
        return {"several": found}
    if found:
        QUERY["ticker"] = found[0]
        return None
    unknown = [w for w in re.findall(r"\b[A-Z]{2,5}\b", message) if w not in TICKERS]
    if unknown:
        QUERY["ticker"] = None
        return {"unknown": unknown[0]}
    return None

def grounding_turn(problem=None):
    """Ask for whatever is missing, or show what was understood and wait for Confirm."""
    if problem and "several" in problem:
        text = "I look at one stock at a time. Which one first: %s?" % " or ".join(problem["several"])
        options = problem["several"]
    elif problem and "unknown" in problem:
        text, options = "I have no data for %s. Which stock did you mean?" % problem["unknown"], TICKERS
    elif not QUERY["ticker"]:
        text, options = "Which stock are you asking about?", TICKERS
    elif not QUERY["horizon"]:
        text, options = "How long do you plan to hold %s?" % QUERY["ticker"], HORIZONS
    else:
        text = "Understood as: %s, holding for %s. Is that right?" % (QUERY["ticker"], QUERY["horizon"])
        options = ["Confirm", "Start over"]
    return {"reply": text, "options": list(options), "action": None, "unsupported_claims": []}

def log_context(parts):
    """Step 1: print exactly what is sent to the model, one line per part."""
    for part in parts:
        print("CONTEXT:", part)

def image_turn(filename):
    image = vlm.ask(os.path.join(HERE, "sample_images", filename), "what deadline is shown?")
    return {"reply": vlm.render(image), "options": [], "action": None,
            "unsupported_claims": [], "image": image}
def decision_turn(message):
    """The button sends __decide__:<choice>:<view>:<card id>. Treat it as a proposal and check it."""
    parts = message.split(":")
    if len(parts) != 4:
        return {"reply": "Not recorded: I could not read that request.", "options": [], "action": None,
                "unsupported_claims": []}
    _, choice, view, card_id = parts
    call = {"name": "record_decision", "arguments": {"card_id": card_id, "decision": choice, "view": view}}
    ok, reason = decisions.valid(call, LAST_CARD)
    if not ok:
        return {"reply": "Not recorded: %s." % reason, "options": [], "action": None, "unsupported_claims": []}
    record = decisions.run(call, LAST_CARD)
    return {"reply": decisions.receipt(record), "options": [], "action": None, "unsupported_claims": [],
            "receipt": dict(record, text=decisions.receipt(record))}


def undo_turn(record_id):
    record = decisions.undo(record_id)
    if not record:
        return {"reply": "Nothing to undo.", "options": [], "action": None, "unsupported_claims": []}
    text = "Undone: your %s decision on %s is marked as undone in the log. You can choose again." % (
        record["decision"], record["ticker"])
    return {"reply": text, "options": [], "action": None, "unsupported_claims": [], "undone": text}
def turn(message):
    global PENDING_TOOL, LAST_CARD
    m = (message or "").lower()

    # --- Agree on what was asked before fetching anything ---
    if message.startswith("__decide__"):
        return decision_turn(message)
    if message.startswith("__undo__:"):
        return undo_turn(message.split(":", 1)[1])
    if message == "Start over":
        QUERY["ticker"] = QUERY["horizon"] = None
        return grounding_turn()
    if message != "Confirm":
        return grounding_turn(understand(message))
    if not (QUERY["ticker"] and QUERY["horizon"]):
        return grounding_turn()
    
    # --- Confirmed, so build the signal card from the evidence ---
    c = signal_card.build(QUERY["ticker"], QUERY["horizon"])
    c["id"] = uuid.uuid4().hex[:8]
    LAST_CARD = c
    return {"reply": "%s: %s, %s confidence. The decision is yours." % (c["ticker"], c["signal"], c["confidence"]),
            "options": ["Start over"], "action": None, "unsupported_claims": [], "card": c}

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        with open(os.path.join(HERE, "index.html"), "rb") as f:
            self._send(200, f.read(), "text/html; charset=utf-8")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        msg = json.loads(self.rfile.read(n).decode("utf-8")).get("message", "")
        self._send(200, json.dumps(turn(msg)).encode("utf-8"))

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    port = 8000
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    print("serving on http://localhost:%d" % port)
    HTTPServer(("localhost", port), Handler).serve_forever()
