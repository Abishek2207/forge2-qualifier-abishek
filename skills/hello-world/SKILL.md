---
name: hello-world
description: >
  A basic introductory skill to demonstrate skill firing.
  Triggers when the user says hello or asks for an introduction.
triggers:
  - hello
  - greet
  - introduce
---

# Hello World Skill

## Purpose
This skill proves that Hermes can detect keywords and trigger predefined workflows autonomously.

## Execution Steps
1. Detect "hello", "greet", or "introduce" in the user prompt.
2. Greet the user in Slack.
3. Save a greeting evidence file to `outputs/greetings.md`.
4. Report completion.