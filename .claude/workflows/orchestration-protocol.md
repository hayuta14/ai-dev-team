# Orchestration Protocol

#### Sequential Chaining
Chain subagents when a step needs the previous step's output (e.g. plan → implement → test → review): each finishes before the next starts, and its output is passed on.

#### Staged Spawn (every parallel batch, incl. ad-hoc)
Spawn the first agent, wait for its **first token** (~2s), then spawn the rest. N parallel requests sharing a prefix all pay cache-write **2,0×** — none can read a cache another is still writing; the first write turns the rest into cache-read. Wait for the first token, never for completion.

#### Parallel Execution
Run independent subagents in parallel only when they touch no shared file or resource; decide the integration points before starting.