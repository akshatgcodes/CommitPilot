# PRD: CommitPilot

## Problem

Commit messages are written last, in a hurry: `git commit -m "fix stuff"`. Worse, one commit often bundles a bug fix, a new feature and a README tweak, which makes history hard to read, review and revert.

## Goal

A drop-in for `git commit -m` that writes a good Conventional Commits message from the staged diff and catches mixed commits before they happen, while leaving the human in charge of what gets committed.

## Users

- A developer who commits from the terminal and wants consistent messages without thinking about the format
- A developer who tends to stage everything at once and wants help untangling it
- A script or hook that needs a suggested message on stdout

## User stories

| As a… | I want to… | So that… |
|---|---|---|
| developer | get a suggested message from what I staged | I don't write "wip" again |
| developer | accept, edit, regenerate or cancel before committing | nothing is committed I didn't approve |
| developer | be told when my diff mixes unrelated work | I keep commits focused |
| developer | have it split the staged changes into several commits | I fix bad hygiene in one step |
| developer | keep my repo's existing scopes and style | new messages match the history |
| developer | use a free or local model | it costs nothing to run |
| script | print a message without committing | I can use it in hooks |

## Requirements

- Read only staged changes; never touch the working tree
- Conventional Commits header (`type(scope): subject`, ≤72 characters), optional short body
- Validate model output; retry once with the problems listed
- Split plan must cover every staged file exactly once; fall back to folder grouping
- Split mode must commit exactly the staged content, and recover the index if a commit fails
- Provider, model and key from env vars or a config file; clear error and exit code 2 without a key
- Works in a repo with no commits yet

## Non-goals

- Splitting one file's hunks across commits (v1 splits by file)
- Pushing, amending, or rewriting existing history
- A GUI or editor plugin

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
