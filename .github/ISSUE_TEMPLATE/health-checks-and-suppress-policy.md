---
name: Health checks + suppress policy
about: Add health endpoints and forbid suppress outside startup
title: Health checks + suppress policy
labels: dashboard, ops
assignees: ''
---

Add `/healthz/live` and `/healthz/startup`. Move all `contextlib.suppress` to `dashboard/startup.py`. Add CI guard script forbidding suppress elsewhere.

