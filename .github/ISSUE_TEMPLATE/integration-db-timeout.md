---
name: Integration DB statement timeout
about: Enforce DB statement timeouts and log timed-out SQL during tests
title: Integration DB statement timeout
labels: testing, db
assignees: ''
---

Enforce `SET statement_timeout` equivalent via SQLite progress handler during tests. Default 2000ms in CI. Log timed-out SQL or failing paths.

