# Changelog

All notable changes to **CommitPilot** are documented here.

---

## [Unreleased]

---

## [0.1.0] — 2026-10-30

### ✨ Added
- `pilot commit`: Conventional Commits message from the staged diff, with accept, edit, regenerate, split and cancel
- Split mode (`--split` or `s`): model-planned groups, validated to cover every staged file once, with a folder-based fallback; commits exact staged patches and restages the rest if a commit fails
- Mixed-diff warning when changes span separate areas
- `pilot message` for scripts, `--yes`, `--dry-run`, and `--style emoji`
- Groq (default), OpenAI and Ollama through one OpenAI-compatible client; config from env, `~/.config/commitpilot/config.env` or `./.env`

### 🧪 Tests
- Diff parsing and split commits against real temporary repos, with a fake chat model for the CLI flows

---

[Unreleased]: https://github.com/akshatgcodes/CommitPilot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/akshatgcodes/CommitPilot/releases/tag/v0.1.0

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
