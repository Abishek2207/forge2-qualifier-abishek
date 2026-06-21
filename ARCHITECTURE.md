# Architecture

Here is how the components communicate:

## Agents
* **Hermes**: The brain / orchestrator agent. It receives tasks, formulates plans, and delegates work.
* **OpenClaw**: The hands / coding agent. It takes instructions and executes them to accomplish tasks.

## Slack Workflow Channels
Communication happens over specific Slack channels:
* `#sprint-main` or `#commands`: The user posts tasks here.
* `#agent-coder` or `#agent-orchestrator`: Hermes formulates and posts plans, delegating to OpenClaw.
* `#agent-log`: OpenClaw posts a structured status report here.
* `#human-review`: Hermes validates the result and posts the final output here for human review.

## Model Routing
* **Hermes**: `owl-alpha` (Planning, memory, orchestration, task decomposition)
* **OpenClaw**: `qwen2.5-coder` via Ollama (Code generation, execution, file operations)
* **Fallback Models**: OpenRouter Free Models, Gemini 2.5 Flash
