# Chat Lab 10-Loop Retrospective Review

Date: 2026-05-18
Issue: https://github.com/nissan/pi-research-agent-workshop/issues/6

## Loop 1 - Interpret Feedback
- Observation: the workshop had task buttons and harness pages, but not a conversational surface.
- Change: scoped Chat Lab as a same-prompt comparison across plain chat, agent chat, and harnessed agent chat.
- Review: this directly answers the participant mental model gap without changing the core workshop sequence.

## Loop 2 - Build Skeleton
- Observation: participants need the first screen to feel familiar.
- Change: added /chat with a textarea, mode controls, conversation history, and artifact links.
- Review: the route is additive and does not disturb existing /, /harness, or /compare routes.

## Loop 3 - Plain Mode
- Observation: a no-agent baseline should be explicit.
- Change: plain mode returns a model-only answer and records that no tools or harness were used.
- Review: this makes the difference between chat and agents visible without requiring credentials.

## Loop 4 - Agent Mode
- Observation: agent behavior needs visible output surfaces even in a clean-room/no-key run.
- Change: agent mode copies fallback artifacts and writes a trace explaining the live credentialed path.
- Review: no secrets or external calls are needed, and participants can inspect artifacts immediately.

## Loop 5 - Harnessed Mode
- Observation: harness value is clearest when it changes the contract, not just the wording.
- Change: harnessed mode writes chat-harness-report.json with enforced checks and blocked action classes.
- Review: the report gives facilitators a concrete object to compare against the un-harnessed agent mode.

## Loop 6 - Persistence
- Observation: prior tester feedback asked that outputs survive route changes.
- Change: chat turns persist to starter/outputs/chat-lab-history.json.
- Review: the UI can move between Chat Lab, Harness Lab, and Compare without losing context.

## Loop 7 - Regression Coverage
- Observation: route regressions are easy to miss in this small Python server.
- Change: added docker-workshop/tests/chat_lab.py with temp-root GET/POST checks across all modes.
- Review: source-level regression now catches missing routes, missing history, and missing harness reports.

## Loop 8 - Docker Smoke
- Observation: source tests are not enough for participant confidence.
- Change: extended docker-workshop/tests/smoke.sh to exercise /chat in the running container.
- Review: Docker smoke now verifies the UI route and generated chat artifacts in the real image layout.

## Loop 9 - Participant Collateral
- Observation: the guide needs a visible explanation and a recording, not just a new button.
- Change: added the Chat Lab recording flow to scripts/record-participant-walkthroughs.mjs; guide update embeds 06-chat-lab.webm.
- Review: participants can see the expected state transitions before class.

## Loop 10 - Release Gate
- Observation: this should ship only if the participant path still works.
- Change: run py_compile, Chat Lab regression, integrity/rate-limit tests, Docker build/smoke, recording generation, here.now publish, and PR/issue updates before completion.
- Review: final status must list any failed gate rather than claiming readiness.
