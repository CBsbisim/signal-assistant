# AI use declaration — Lab 4

- **Tool:** Claude (Anthropic), used through the Claude app.
- **What it did:** explained the lab. and give me a to do list. correcting the grammer of my code, reorganizing the code, refining the code
- **Changes from the handout code:** added a "Propose invalid 900-minute slot" button so the validation
  refusal can be seen in the browser (not only in `tools.py`); did not add the handout's second
  `stale_warning` block because the supplied `index.html` already renders it; chose my own unanswerable
  question ("Can I resubmit coursework 1…?"), which exposed a real retrieval failure.
- **What I checked / changed myself:** ran the three self-tests (`retrieve.py`, `tools.py`, `vlm.py` with `--selftest`) and `python app.py` on my own machine on 28 Oct 2026; asked "when is coursework 1 due" in the browser and confirmed the terminal printed the single `CONTEXT:` line recorded in `01_CONTEXT_MAP.md`. I did not change the code.
- **Data:** only the supplied course documents and sample images; no API keys, no personal data. 
