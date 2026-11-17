# Signal assistant

**README prose word count:** 616

A prototype decision-support assistant for retail investors. You ask about a stock; it shows what it understood, gives a Buy / Hold / Sell signal with its confidence and dated evidence, and records **your** decision. MSc Intelligent Interactive Systems, Assignment 2, University of Birmingham.

Submitted version: tag `v1.0-a2` (https://github.com/CBsbisim/signal-assistant/releases/tag/v1.0-a2)

![System diagram](docs/system_diagram.png)

## Project status

| Part | Status |
|---|---|
| Understanding the question, asking when unclear, "Understood as…" + Confirm | Implemented |
| Signal card: signal, confidence, dated evidence incl. one against, stale warning, no-signal | Implemented |
| Brief view by default, detailed view on request | Implemented |
| Recording the person's decision (checked, no repeats, undo) | Implemented |
| Evidence (two fictional stocks) and each item's direction | Simulated |
| Live data, a language model, horizon weighting, outcome alerts, reliance study | Planned |
| Placing real trades | Deliberately not built |

## Development record

| Change | Why | Checked |
|---|---|---|
| [5a838e8](https://github.com/CBsbisim/signal-assistant/commit/5a838e8) Lab 4 base, unchanged | already had dated sources, a stale warning and a checked tool | Lab 4 self-tests |
| [25ede46](https://github.com/CBsbisim/signal-assistant/commit/25ede46) Dated stock evidence + superseded 2025 report | Because in finance, old evidence is wrong evidence. Dated data is needed. | NAN scored 0.00 |
| [34d3395](https://github.com/CBsbisim/signal-assistant/commit/34d3395) "Understood as…" + asking | The system shows what it understood. | 4 browser cases |
| [7da3faa](https://github.com/CBsbisim/signal-assistant/commit/7da3faa) Fix: two stocks became one silently | Found in testing | New case + earlier ones |
| [8bcb30b](https://github.com/CBsbisim/signal-assistant/commit/8bcb30b) Signal card; all evidence, not top 3 | Show the signal’s bet honestly: confidence capped with few sources, one item against, so users don’t over-rely | One source gave "high" without the rule |
| [e462389](https://github.com/CBsbisim/signal-assistant/commit/e462389) Brief / detailed view | Make user understand the detail of how the inference was made | Detail changed my judgement |
| [c5265bb](https://github.com/CBsbisim/signal-assistant/commit/c5265bb) Decision recording, no trading | The investor keeps the final decision; the tool can only log it, never trade | Bad requests refused |
| [f4b2238](https://github.com/CBsbisim/signal-assistant/commit/f4b2238) 13 fixed test cases | One demo isn’t evidence; rerun the same cases after every change | 12/13; G3 in `TEST_RECORD.md` |
| [522d08c](https://github.com/CBsbisim/signal-assistant/commit/522d08c) Removed unused Lab 4 code | Unused Lab 4 code would mislead a reader about the system | 13/13 after |

## Technology stack

- **Python 3 standard library only** (`http.server`, `json`, `re`, `datetime`, `uuid`). Nothing to install.
- **One HTML page with plain JavaScript** (`index.html`).
- **No AI model or API is called at run time.** The inference is a readable rule in `signal_card.py` to present the decisions made by the system clearly.
- **Undecided:** which language model would label evidence and phrase explanations, and which market-data source to use (yfinance was considered in Lab 3; it is unofficial).
- **No API keys are needed.** If a model is added later, a reviewer would supply their own key through an environment variable; no key is ever committed.

## Running or inspecting the work

Python 3.10 or later.

```
python app.py                    # then open http://localhost:8000
python run_cases.py              # the 13 fixed test cases; expect "13 of 13 passed"
python signal_card.py --selftest
python decisions.py --selftest
python retrieve.py --selftest
python signal_card.py XYZ        # print the signal card data for XYZ
```

Suggested walkthrough: click **Try: XYZ, 6 months** → **Confirm** → **Show how this signal was made** → **Sell** → **Undo**. Then try **ABC, 1 year** (only one source, so low confidence) and type `Is NAN worth buying?`.

| File | What it does |
|---|---|
| `app.py` | Web server and conversation: understanding, asking, confirming, routing decisions |
| `signal_card.py` | Evidence → signal, confidence, evidence shown, stale-source warnings |
| `decisions.py` | The one tool: records a decision after checks; undo |
| `retrieve.py` | Loads the evidence files with their source, date and direction |
| `index.html` | The page: chat, signal card, detailed view, decision buttons |
| `corpus/` | Simulated evidence, one file per source |
| `run_cases.py`, `TEST_RECORD.md` | Fixed test cases and the record of what they found |

## AI assistance

**Tool**: Claude.

**Asked for**: A building guide based on A1 and Lab 4; explanations of lecture concepts, reference codes.

**What I decided or changed**: I wrote the evidence texts, chose all six direction labels, chose to remember past horizon for G3 with my own reasons, picked which lab to start from with its guidance, judged the brief vs detailed views, write codes to fit.

**How I checked**: Ran every self-test and the 13 cases; clicked through each step in the browser; the tests caught real bugs, the two-stock bug and G3.

## Additional files

- `TEST_RECORD.md`: test results, failures found and what changed.
- `screenshots/`: the screens used in the report's storyboards.
- `docs/`: the system diagram and storyboards used in the report.
- No ZIP file; everything is in this repository.