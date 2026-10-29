# Architecture

```
  pilot / python pilot.py  ──▶  cli.py (argparse, prompts, colours)
                                   │
          ┌────────────────────────┼─────────────────────────┐
          ▼                        ▼                         ▼
     git.py                     llm.py                   grouping.py
     staged_patch · commit      suggest · plan_split     area · heuristic_groups
     split_commit · backup      chat_model (ChatOpenAI)  looks_mixed · check_plan
          │                        │
          ▼                        ▼
     diff.py (pure)             messages.py (pure)
     parse → FileDiff[]         clean · problems · to_emoji
     condensed (for the model)
```

## Modules

| Module | Role |
|---|---|
| `diff.py` | Splits `git diff --staged --binary -M` into one `FileDiff` per file (path, old path, status, binary flag, +/− counts, and that file's exact patch text). `condensed()` builds the model's view: lockfiles and binaries summarised, 2,500 characters per file, 20,000 in total, stats only after that. |
| `messages.py` | `clean()` turns a raw reply into a message: strips code fences, labels and wrapping quotes, swaps typographic dashes and quotes for ASCII, and makes the second line blank. `problems()` lists rule breaks. `to_emoji()` converts to the emoji style. |
| `grouping.py` | Model-free grouping by area (`deps`, `docs`, `ci`, `root`, top folder, or `src/<pkg>`); tests follow the source file with the same stem, lockfiles go with deps. `check_plan()` validates a split plan. |
| `git.py` | Thin wrappers over the git CLI (`core.quotePath=false` so non-ASCII paths come back as-is). `split_commit()` makes the commits. |
| `llm.py` | Settings, provider presets, the prompts, `suggest()` and `plan_split()`. |
| `cli.py` | `commit` and `message` commands, the interactive menu, opening the git editor. |

## Suggest flow

1. `git diff --staged` → `parse()`; nothing staged → error
2. Last 10 commit subjects (so the model reuses existing scopes)
3. System prompt with the rules and five few-shot examples; user message with the subjects and `condensed()` diff
4. `clean()` the reply; if `problems()` finds anything, ask once more with the problems listed
5. If `looks_mixed()` (2+ areas and 80+ changed lines), show a split hint

## Split flow

1. `heuristic_groups()` is passed to the model as a starting point, with a prompt that keeps fixes, features, refactors, docs and CI apart, but keeps a change's own tests, docs and dependencies with it
2. Reply must be JSON `{"commits": [{"files": [...], "message": "..."}]}`; `check_plan()` rejects unknown, missing or duplicate files; one retry with the errors
3. Still invalid → one commit per heuristic group, each with its own `suggest()`
4. On confirm, `split_commit()`:
   - writes the staged patch to `.git/commitpilot-backup.patch`
   - empties the index (`git reset -q`, or `git read-tree --empty` before the first commit)
   - for each group: `git apply --cached` that group's patches, then `git commit -F -` (hooks run)
   - on failure: re-applies the groups not yet committed and stops; if even that fails, prints the `git apply --cached` command for the backup
   - on success: deletes the backup

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
