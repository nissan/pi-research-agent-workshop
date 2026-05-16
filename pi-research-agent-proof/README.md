# Pi Research Agent Proof

This is the participant starter project for the **Build Your First Specialist Agent** roadshow workshop.

## Goal

Start with a generic local research agent, then specialize it with exactly one layer:

1. a better prompt,
2. a small local tool,
3. a reusable skill,
4. custom domain information, or
5. a harness/settings customization.

Then compare the generic output with the specialized output and decide whether the specialized version could become a paid Reddi Agent Protocol specialist.

## Setup

```bash
npm install -g @earendil-works/pi-coding-agent
cd pi-research-agent-proof
pi
```

Inside Pi, run:

```text
/login
```

Then use the baseline prompt:

```text
Read the project instructions and generate the research brief requested in inputs/generic-brief-request.md. Use sources/source-notes.md. Write the result to outputs/research-brief-generic.md.
```

## Specialization challenge

Open `inputs/specialization-challenge.md`, choose one path, add your specialization, then rerun:

```text
Rerun the same research task, but include my specialization layer. Write the improved result to outputs/research-brief-specialized.md and write comparison notes to outputs/delta-notes.md.
```

## Safety note

Do not paste confidential client data, credentials, private keys, or personal information into this exercise. Use synthetic or redacted examples.

## Docker workshop mode

If your facilitator provides the public Docker image, you do not need to install Pi manually. Use:

```bash
docker run --rm -it --name pi-research-agent-workshop -p 8787:8787 nissan/pi-research-agent-workshop:latest
```

Then open `http://localhost:8787`.


## Hugging Face model swap

After the OpenAI baseline works, use `HUGGINGFACE-MODEL-SWAP.md` to rerun the same specialist agent with `--provider huggingface --model Qwen/Qwen2.5-7B-Instruct`.

Use one of the sample domain packs in `sources/domain-packs/`:

- Artificial Intelligence
- Blockchain Development
- Cloud Computing
- Database Development

The harness changes for this run: the final brief must name the provider/model and the domain pack used, and must label arXiv evidence, domain-pack context, and assumptions separately.
