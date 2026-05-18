# Chat Lab Round 2 - 10-Loop Retrospective Review

Date: 2026-05-18
Issue: https://github.com/nissan/pi-research-agent-workshop/issues/6

## Loop 1 - Review Round 1 Fit
- Observation: Round 1 answered the core UI request, but comparison still required three manual sends.
- Change: added a single action to run all three modes from the same prompt.
- Review: this better matches the workshop question: what changes when we add agency and harnessing?

## Loop 2 - Facilitation Artifact
- Observation: participants and facilitators need a way to preserve the conversation outcome.
- Change: added markdown transcript export at /chat-transcript.
- Review: transcript export gives collateral without screenshots or manual copy/paste.

## Loop 3 - Reset Control
- Observation: repeated participant exercises need a clean state.
- Change: added /chat-clear and a Clear conversation button.
- Review: reset is scoped to Chat Lab history/transcript and does not delete unrelated workshop outputs.

## Loop 4 - Comparison Framing
- Observation: users should understand the three modes before clicking.
- Change: added a compact Plain / Agent / Harnessed summary panel.
- Review: the UI now teaches the distinction at the point of action.

## Loop 5 - Prompt Ergonomics
- Observation: an empty prompt made the first action feel under-specified.
- Change: prefilled a reusable research-comparison prompt.
- Review: participants can still edit it, but the demo works immediately.

## Loop 6 - Regression Expansion
- Observation: export and clear paths are easy to break.
- Change: extended chat_lab.py to cover run-all, transcript generation, and clear.
- Review: source test now covers the full Chat Lab lifecycle.

## Loop 7 - Docker Smoke Expansion
- Observation: Docker smoke should match participant interactions, not only source tests.
- Change: extended smoke to run all modes, fetch transcript, clear state, and verify files.
- Review: release gate now checks the interaction in the container layout.

## Loop 8 - Guide Update
- Observation: participant docs mentioned the mode comparison but not export/reset.
- Change: updated the guide with transcript/history/report artifact expectations.
- Review: the guide now explains what participants should see and where outputs live.

## Loop 9 - Recording Update
- Observation: the Chat Lab recording needed to match button labels and new export affordance.
- Change: updated the recording script to use Send selected mode and show transcript export.
- Review: the video remains aligned with the live UI.

## Loop 10 - Release Gate
- Observation: Round 2 needs the same release discipline as Round 1.
- Change: rerun py_compile, focused tests, media generation, Docker smoke, public image publish, here.now publish, PR/issue comments, and status/memory updates.
- Review: final status must include any failed or skipped gate.
