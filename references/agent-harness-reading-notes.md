# Agent Harness Reading Notes

These notes summarize the reference articles behind the opening presentation and harness lab. They are facilitator context, not instructions to the workshop agent.

## Sources

- Anthropic, Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- Augment Code, Harness Engineering for AI Coding Agents: https://www.augmentcode.com/guides/harness-engineering-ai-coding-agents
- Mitchell Hashimoto, My AI Adoption Journey: https://mitchellh.com/writing/my-ai-adoption-journey
- OpenAI, Harness engineering: https://openai.com/index/harness-engineering/
- LangChain, The Anatomy of an Agent Harness: https://www.langchain.com/blog/the-anatomy-of-an-agent-harness

## Synthesis for This Workshop

1. Start simple, then add agency only where the task needs it.
   Anthropic's framing is useful for the first 20 minutes: workflows follow predefined paths, while agents dynamically choose tool use and process.

2. An agent is the model plus its harness.
   LangChain's definition is the clean teaching line: if it is not the model, it is part of the harness.

3. Harness engineering is the reliability layer.
   Augment and OpenAI both emphasize that prompts alone rely on probabilistic compliance.

4. Humans steer; agents execute.
   OpenAI reframes engineering work as designing environments, specifying intent, and building feedback loops.

5. The ratchet matters.
   Mitchell Hashimoto's adoption story is pragmatic: every repeated agent failure should become a harness improvement.

6. Measurement needs baseline and evidence.
   Show generic output first, then specialized output, then harnessed output. The scorecard makes the delta legible.

## Prompt Examples to Keep Visible

Baseline: use only the basic source notes and produce the first generic brief.

Specialized: add domain pack, arXiv/PDF tools, evidence labels, and delta notes.

Harnessed: run the same task under harness policy, require evidence boundaries, write a harness report, and compare against the loose run.
