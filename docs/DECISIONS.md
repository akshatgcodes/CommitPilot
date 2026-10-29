# Decisions

### 1. Shell out to the git CLI
**Decision:** `subprocess` running `git`, not GitPython or libgit2.
**Why:** The diff, `apply --cached` and commit hooks behave exactly as they do for the user. No extra dependency, and the commands are easy to reproduce by hand when something looks wrong.

### 2. Commit exact patches in split mode
**Decision:** Save the staged patch, reset the index, then `git apply --cached` each group's slice and commit.
**Why:** `git add <path>` would also stage unstaged edits in those files. Applying the staged patch keeps "what you staged is what gets committed", and works for renames, deletions and binaries (`--binary`).
**Trade-off:** Splitting is per file. Two unrelated changes in one file go into the same commit.

### 3. Validate the plan, fall back to a heuristic
**Decision:** A model plan is only used if every staged file appears exactly once. One retry with the errors, then group by area.
**Why:** The model is good at seeing which changes belong together, but a plan that drops a file would silently leave changes uncommitted. The heuristic is dull but always correct.

### 4. Folder grouping is a hint, not the answer
**Decision:** The model gets the heuristic groups as a starting point, plus a rule that a fix, a feature, a refactor, docs and CI are separate commits even in one folder, while a change's own tests, docs and dependencies stay with it.
**Why:** In testing with Groq, four unrelated changes (a CI workflow, a README tweak, a new query parameter, a new module with its test) were first grouped into three commits because two sat in the same folder; with this rule they became four. A single feature with its test and README section stays together.
**Trade-off:** A dependency bump the diff doesn't clearly tie to the feature may still get its own `chore(deps)` commit.

### 5. Check and retry the message, don't just trust it
**Decision:** `clean()` then `problems()`; one retry with the problems listed.
**Why:** Models sometimes add a trailing period, a capital letter, code fences, or typographic dashes and quotes. Cleaning fixes formatting noise; the retry fixes rule breaks.

### 6. Send a condensed diff
**Decision:** Summarise lockfiles and binaries, cap each file at 2,500 characters and the total at 20,000.
**Why:** A lockfile can be thousands of lines and says nothing about intent. Capping keeps requests fast and inside free-tier limits.
**Trade-off:** For a huge diff the model sees only stats for later files, so their part of the message is a guess from file names.

### 7. Any OpenAI-compatible API, Groq by default
**Decision:** `ChatOpenAI` with a configurable `base_url`; presets for Groq, OpenAI and Ollama.
**Why:** Groq is fast and has a free tier, which matters for a tool you run on every commit. One client covers all three.

### 8. The human confirms every commit
**Decision:** Nothing is committed without `y`, unless `--yes` is passed. `--dry-run` never commits. Without a terminal and without `--yes`, `pilot commit` refuses.
**Why:** It's the user's history. A wrong suggestion should cost a keypress, not a `git reset`.

### 9. Tests against real repos with a fake model
**Decision:** Fixtures create temporary repos with an isolated git config; `chat_model()` is replaced with a scripted fake.
**Why:** Diff parsing and split commits are tested on real git behaviour (renames, deletions, binaries, paths with spaces, partial staging, a repo with no commits, a hook that rejects a commit) without network calls or API keys.

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
