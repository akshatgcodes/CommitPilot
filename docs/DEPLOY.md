# Deploy

## Website

The product page at **https://commitpilot.akshatgcodes.in** is `landing/` (a Next.js static export) on Vercel, connected to this repo. CommitPilot itself is a CLI and runs on your machine; the rest of this page is about that.

CommitPilot is a local CLI; there's no server to host. "Deploying" it means installing it as a command you can run in any repo.

## Install as a command

```bash
git clone https://github.com/akshatgcodes/CommitPilot
cd CommitPilot
uv tool install .        # or: pipx install .
pilot --help
```

Upgrade after pulling changes with `uv tool install --reinstall .` (or `pipx reinstall commitpilot`).

## Key

Put the key in the user-wide config file so it works in every repo and stays out of project `.env` files:

```bash
mkdir -p ~/.config/commitpilot
echo 'GROQ_API_KEY=gsk_...' > ~/.config/commitpilot/config.env
chmod 600 ~/.config/commitpilot/config.env
```

## Make it a habit

A git alias, so `git pc` runs it:

```bash
git config --global alias.pc '!pilot commit'
```

## What leaves your machine

Each run sends the provider a condensed copy of your **staged diff** and your last 10 commit subjects. Don't use it on code you're not allowed to send to a third party; use `LLM_PROVIDER=ollama` with a local model instead.

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
