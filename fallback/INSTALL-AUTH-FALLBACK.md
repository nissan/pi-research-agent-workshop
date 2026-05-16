# Install/Auth Fallback Plan

## If Pi is not installed

Use the participant zip and the fallback sample outputs. The teaching goal is the agent anatomy and specialization delta, not package-manager debugging.

## If npm install fails

1. Pair the participant with someone who has Pi running.
2. Use the fallback files:
   - `fallback/sample-research-brief-generic.md`
   - `fallback/sample-research-brief-specialized.md`
   - `fallback/sample-delta-notes.md`
3. Have them still complete the marketplace card.

## If provider login fails

Use the fallback outputs and ask the participant to specialize by editing files only. They can run it after the session.

For the VPS instructor sandbox, this is currently the only blocker to a live Pi rehearsal: the container is healthy, but Pi returns `No API key found for the selected model` until `/login` is completed interactively or a short-lived provider key is injected at runtime. See `rehearsal/PI-SANDBOX-REHEARSAL-AUTH-CHECK-2026-05-12.md`.

## If terminal comfort is low

Make them choose Path B: custom information. They only need to create or edit a markdown file.

## Facilitator rule

Do not spend more than 5 minutes debugging one participant during the live workshop. Preserve flow.
