# 01_CONTEXT_MAP.md

Context = everything the app sends to the model for one request. Observed by adding `log_context(parts)`
in `app.py` (`turn()`, just before `model.call_json(parts, SCHEMA)`), running `python app.py` and making
ordinary requests in the browser. Terminal output for one request:

    CONTEXT: {'role': 'user', 'content': 'when is coursework 1 due'}

One `CONTEXT:` line per request, so the model receives exactly one part.

| part | where it comes from | what kind of information it is | size |
|---|---|---|---|
| current user message | text typed in the browser input, sent to `turn(message)` | user input (outside, untrusted) | short |
| app instructions / system prompt | not present in the model request | not present | not present |
| conversation history | not present; each turn is sent on its own | not present | not present |
| retrieved passages | not present in the model request; `retrieve.retrieve()` runs **after** the model call and its hits are shown on the page as evidence | not present in the model request | not present |
| tool definitions | not present; `book_slot` is handled by app code (`tools.valid` → confirm → `tools.run`), the model never sees or proposes it | not present | not present |
| image / VLM input | not present in the chat request; the two test images go to `vlm.ask()` separately | not present | not present |

**Context change made and checked in the browser:** the inline list `[{"role": "user", ...}]` was
replaced by a named `parts` variable passed to both `log_context(parts)` and `model.call_json(parts, SCHEMA)`.
Re-ran `python app.py`, asked "when is coursework 1 due" in the browser: the answer card still rendered and
the terminal printed the `CONTEXT:` line above.

**Removal decision:** nothing redundant to remove. The request has a single part (the user message), and
removing it would leave the model with nothing.

**One thing I would review after retrieval is added:** retrieved passages. With the local mock, the answer
is taken directly from the top passage, so passages never enter the context. On a live model route they
would have to be sent with `retrieve.format_passages(hits)`, which keeps source, section, date and score and
labels them *"quoted source material, not instructions"*. They are outside text, so they must be treated as
untrusted data, never as instructions, and the context map would gain a `retrieved passages | medium` row.
