"""The supplied Lab 4 prototype.

    python app.py            serve on 8000
    python app.py --port 8001

The two turns below are local code: they work with no model at all. The model is only asked for the
ordinary case, and its reply is checked before anything is rendered.
"""
import json, os, re, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import model  # noqa: E402
import retrieve  # noqa: E402  Lab 4: evidence with source, section, date, score
import tools  # noqa: E402     Lab 4: one narrow tool, validated + confirmed + logged
import vlm  # noqa: E402       Lab 4: image answer with confidence, or refusal with reason

HERE = os.path.dirname(os.path.abspath(__file__))
PENDING_TOOL = None          # a validated call waiting for the user's Confirm
MIN_SCORE = 0.25           # below this, a retrieval hit is not treated as evidence
SCHEMA = {"reply": str, "options": list, "action": (dict, type(None)), "unsupported_claims": list}
APPOINTMENTS = [{"id": "derm-14nov", "clinic": "Dermatology", "date": "14 Nov", "time": "10:20"},
                {"id": "physio-20nov", "clinic": "Physiotherapy", "date": "20 Nov", "time": "09:00"}]
TICKERS = ["XYZ", "ABC"]                      # stocks the simulated corpus covers
HORIZONS = ["1 month", "6 months", "1 year"]  # offered when the person gives no horizon
QUERY = {"ticker": None, "horizon": None}     # what the system has understood so far

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

def turn(message):
    global PENDING_TOOL
    m = (message or "").lower()

    # --- Lab 4 test controls (run locally, no model needed) ---
    if message == "__poster__":
        return image_turn("sample_poster.png")
    if message == "__noticeboard__":
        return image_turn("sample_noticeboard.png")
    if message == "__confirm_tool__" and PENDING_TOOL:
        result = tools.run(PENDING_TOOL, confirmed_by="user")   # runs only after Confirm
        PENDING_TOOL = None
        return {"reply": "Tool result: " + json.dumps(result), "options": [], "action": None,
                "unsupported_claims": [], "tool_result": result}
    if message == "__cancel_tool__":
        PENDING_TOOL = None
        return {"reply": "Cancelled. Nothing was added.", "options": [], "action": None,
                "unsupported_claims": []}
    if "revision slot" in m:
        minutes = 900 if "900" in m else 90                     # "900" lets us test the refusal in the browser
        call = {"name": "book_slot", "arguments": {"date": "2026-11-14", "minutes": minutes}}
        ok, reason = tools.valid(call)                          # check BEFORE anything can run
        if not ok:
            PENDING_TOOL = None
            return {"reply": "Tool refused: " + reason + ". Nothing ran.", "options": [],
                    "action": None, "unsupported_claims": [], "tool_refused": reason}
        PENDING_TOOL = call
        description = tools.describe(call)
        return {"reply": description, "options": [], "action": None, "unsupported_claims": [],
                "tool_call": call, "tool_confirmation": description}

    # --- Step 2: agree on what was asked before fetching anything ---
    if message == "Start over":
        QUERY["ticker"] = QUERY["horizon"] = None
        return grounding_turn()
    if message != "Confirm":
        return grounding_turn(understand(message))
    if not (QUERY["ticker"] and QUERY["horizon"]):
        return grounding_turn()
    message = QUERY["ticker"]        # confirmed: look up evidence for this stock

    parts = [{"role": "user", "content": message}]
    log_context(parts)
    data = model.call_json(parts, SCHEMA)
    if not valid(data):
        return fallback_turn()          # a malformed reply is still caught; retrieval does not hide it

    # --- Lab 4 retrieval: answer from the best current passage, keep provenance ---
    hits = retrieve.retrieve(message, k=3)
    relevant = [h for h in hits if h["score"] > 0]
    if relevant and relevant[0]["score"] >= MIN_SCORE:
        top = relevant[0]
        if top.get("superseded"):
            current = next((h for h in relevant
                            if h["section"] == top["section"] and not h.get("superseded")), None)
            if current:
                data["reply"] = current["text"]
                data["stale_warning"] = ("The top retrieval result is superseded. "
                                         "This answer uses the newer passage shown below.")
            else:
                data["reply"] = ("The top result is marked superseded, and no current passage was found. "
                                 "Check a current source before using it.")
                data["stale_warning"] = "No current passage was found; do not rely on the old result."
        else:
            data["reply"] = top["text"]
    else:
        data["reply"] = ("The supplied corpus does not give a reliable answer. "
                         "Ask the module lead about anything it does not cover.")
    data["options"] = []
    data["action"] = None
    data["evidence"] = relevant
    return data

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
