# examples/ — mechanism demo, not a red-team methodology

`toy_policies.py` + `demo_run.py` wire the full pipeline end to end —
register a target → authorization gate → Crescendo loop → finding → tape →
report — using a completely abstract toy target (a LOCKED/UNLOCKED state
machine) in place of a real attacker/judge/target. There is no attack
content here to mistake for a real methodology: the "target" flips state
after a fixed number of attempts regardless of what's sent to it.

This stands in for what the roadmap calls "私有 skill + 已授权测试端点" —
things that don't belong in this repo (CLAUDE.md house rule 4). Swap
`ToyAttacker`/`ToyJudge`/`ToyTarget` for real implementations of
`AttackerPolicy`/`JudgePolicy`/`TargetClient` (see `../src/agent1_orchestrator/policies.py`)
to run this against something real.

## Run it

```bash
python3 agent1/orchestrator/examples/demo_run.py           # tape step skipped, no bub
.venv/bin/python agent1/orchestrator/examples/demo_run.py  # full loop incl. tape bridge
```

Expected output: the loop runs 3 rounds (2 `pass`, then the toy target
flips and the 3rd round comes back `fail`), one finding gets logged, and a
Markdown report prints to stdout. Under `.venv` it also reports how many
entries landed on the (in-memory) tape.
