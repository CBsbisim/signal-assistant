# 02_TEST_RECORD.md

What the screen actually showed, run in the browser at http://localhost:8000 on 27 Oct 2026.
Screenshots are in `screenshots/`.

- **Grounded** — the current documents contain the answer.
- **Stale** — an old document contains an answer, but a newer document replaces it.
- **Unanswerable** — the documents do not contain the answer.

| question | type | what the screen showed | supported? | what I would change |
|---|---|---|---|---|
| "when is coursework 1 due" | grounded | Answer: "Coursework 1 is due on 14 November at 12:00 and is worth 40%…". Evidence card quoted that passage: Module Handbook 2026–27, §3 Assessment, updated 2026-09-12, score 1.056. Two lower hits (0.949 feedback, 0.761 CW2) also listed. (`01_grounded.png`) | yes | Nothing for the answer. The two extra passages are relevant but not needed; could show only hits used for the answer and collapse the rest. |
| "What is the late-submission penalty?" | stale | Orange warning: "The top retrieval result is superseded…". Answer used the 2026 rule (five marks per working day, max five days). Evidence listed the 2024 passage first marked `[SUPERSEDED]`, updated 2024-10-03, score 0.821, then the current 2026 passage, updated 2026-09-12, score 0.489. (`02_stale.png`) | partly | The page is right only because of the superseded flag; the **ranking** is still wrong (old rule outscores the current one 0.82 vs 0.49). Filter or down-rank superseded passages *before* ranking, and break ties by `updated` date. |
| "Can I resubmit coursework 1 after I get feedback?" | unanswerable | The corpus says nothing about resubmission, but the page answered "Feedback on coursework 1 is returned within fifteen working days of the deadline." with that passage as evidence, score 0.936 — well above the 0.25 threshold. No warning. (`03_unanswerable_resubmit.png`) | **no** | Word overlap ("coursework", "1", "feedback") is not the same as answering the question; the high score made an irrelevant passage look like an answer. Require the passage to contain the question's key term (here "resubmit/resubmission"), or add an answerability check (on a live route: ask the model whether the quoted passage answers the question, and refuse if not). The 0.25 threshold alone cannot catch this. |

Extra check (not one of the three required rows): "Can I use an AI assistant for the project?" — every
score was 0.00, the page said "The supplied corpus does not give a reliable answer. Ask the module lead…"
and showed no evidence (`04_unanswerable_ai.png`). Correct, but only because no words overlapped at all.

## Tool and image checks (same session)

| check | what the screen showed | result |
|---|---|---|
| invalid call, 900 minutes | "Tool refused: minutes must be between 15 and 180. Nothing ran." Nothing written to `tool_log.jsonl`. (`05_tool_refused.png`) | pass |
| valid call, 90 minutes | "Add a 90-minute revision slot on Sat 14 Nov 2026?" with Confirm / Cancel (`06_tool_confirm.png`) | pass |
| after Confirm | "Tool result: {"status":"ok","id":"slot_1","total_slots":1}" (`07_tool_result.png`). Last line of `tool_log.jsonl`: `{"tool": "book_slot", "args": {"date": "2026-11-14", "minutes": 90}, "confirmed_by": "user", "result": {"status": "ok", "id": "slot_1", "total_slots": 1}}` | pass |
| poster image | "14 November, 12:00 (confidence 0.86 — the sheet reads 'Due: 14 November, 12:00')" (`08_poster.png`) | pass |
| noticeboard image | "I cannot answer that from this image: no deadline is visible in this image, and it shows a named person's mark, which I will not read out" (`09_noticeboard.png`) | pass |

Note: in mock mode `vlm.py` decides by **file name**, not by looking at the image, and 0.86 is a fixed
number. The page shows the confidence correctly, but it is not a measured confidence.
