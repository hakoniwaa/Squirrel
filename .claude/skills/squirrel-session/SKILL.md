---
name: squirrel-session
description: Load behavioral corrections from Squirrel memory at session start. Use when starting a new coding session.
user-invocable: false
---

At the start of this session, load corrections from Squirrel:

1. Call `squirrel_get_memory` to get all behavioral corrections.
2. Apply these corrections throughout the session.
