---
name: Always use --break-system-packages
description: In this devcontainer environment, always pass --break-system-packages to pip since we control the system
type: feedback
---

Always use `--break-system-packages` when running pip install.

**Why:** The project runs in a devcontainer that the user fully controls, so PEP 668 protection is unnecessary.

**How to apply:** Any time you run `pip install`, include `--break-system-packages` without hesitation.
