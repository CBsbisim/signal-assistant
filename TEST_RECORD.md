# Test record

Run with `python run_cases.py`. The cases are fixed, so every code change is checked against the same list (Lecture 09, fixed testing loop). Test decisions go to a temporary file, never to `decisions.jsonl`.

## Latest run (10:45 17/11/2026)

D:\AA-MINXI\MScModules\IIS\signal-assistant>python run_cases.py
| Case | What it tests | Must contain | Result |
|---|---|---|---|
| G1 | ticker and horizon understood | Understood as: XYZ, holding for 6 months | PASS |
| G2 | two stocks: asks which one | one stock at a time | PASS |
| G3 | missing horizon: asks | How long do you plan to hold ABC | PASS |
| G4 | unknown ticker: declines and offers options | I have no data for NAN | PASS |
| S1 | supported signal | XYZ: Buy, medium confidence | PASS |
| S2 | too little evidence: low confidence | ABC: Sell, low confidence | PASS |
| D1 | decision against the signal is recorded | goes against the system's Buy signal | PASS |
| D2 | repeated click writes nothing | Nothing new was written | PASS |
| D3 | malformed decision refused | must be Buy, Hold or Sell | PASS |
| D4 | decision on a card not on screen refused | no longer on screen | PASS |
| S3 | stale 2025 report reported, not used | (checked on the card) | PASS |
| S4 | evidence against the signal is shown | (checked on the card) | PASS |
| S5 | no evidence gives no signal | (checked on the card) | PASS |

13 of 13 passed

## Failures found and what I changed

- **G3 (first run):**  It failed to understant which time frame does the user want. According to Amershi G12, remember recent interactions, if user just said “1 year”; asking again would be annoying. So the test is wrong, keeping "1 year" is correct if user has mentioned it before.
- **Two stocks in one message (Step 2b):** "Is XYZ or ABC better" silently became ABC. Commit: **7da3faa** Fix: two tickers in one message silently picked the last; now asks which one (found in testing) from `git log --oneline`
- **Top-3 retrieval hid the old report (Step 3):** the 2025 earnings file never reached the top 3, so the stale warning could not fire. The signal card now reads all evidence for the stock.
- **MIN_SOURCES experiment:** S2 failed, saying high confidence on one source

## What each group of cases tests

| Cases | Idea |
|---|---|
| G1–G4 | the system checks it understood the question before answering. |
| S1, S3, S5 | the answer is tied to real, current evidence, or there is no answer. |
| S2, S4 | the system doesn’t overstate itself. |
| D1–D4 | the decision button is a checked action. |