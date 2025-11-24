Assistant Technical Response Preferences
=====================================

This repository includes machine-assistant response preferences and a lightweight validator that the developer/assistant should follow.

Core rules
- Keep responses focused, technically precise, and verifiable.
- Provide copy-pasteable system commands targeted at the environment: Windows PowerShell (use `;` to join commands on one line).
- When changing code: prefer minimal, correct changes; run and report tests when possible.
- State assumptions only when required for correctness.
- When producing diffs or editing files: use `apply_patch`/git workflow and reference file paths.

Validator
- A small script lives at `scripts/validate_powershell_commands.py`. Run it to scan the repo for likely bash-style constructs that are not PowerShell-friendly (for example `&&` and obvious `bash` snippets). It flags matches so the assistant/developer can review and correct them.

How to use
- Run the validator in PowerShell:

```powershell
python .\scripts\validate_powershell_commands.py
```

Expectations for the assistant
- Use PowerShell-compatible commands in examples.
- Keep messages concise and actionable.
- When modifying code, run quick validations and report results.

Notes
- This document is guidance for the assistant and contributors; it does not change runtime behaviour of the application.
