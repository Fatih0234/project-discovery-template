---
mode: agent
description: "Discover and shortlist strong real-world GitHub projects using a target library"
---

You are helping build a beginner-friendly learning map for a programming library or framework.

Target library: ${input:library:Name of the library or framework}
Target language: ${input:language:Primary language, e.g. python, typescript, go}
Goal: ${input:goal:What is the learner trying to understand?}
Top K repos: ${input:top_k:Number of repos to shortlist}

Your task:
1. Search the workspace and project outputs to understand what discovery tooling already exists.
2. If discovery outputs do not exist yet, inspect the CLI and discovery modules and explain which command should be run.
3. If candidate outputs exist, review them and shortlist the best repositories for a junior developer.
4. Favor repos that:
   - clearly use the library in real code
   - are active enough to be trustworthy
   - are understandable for learners
   - illustrate distinct use cases
5. Avoid repos that:
   - only mention the library in docs or lockfiles
   - are huge monorepos with poor learning value
   - are stale or obscure unless they are exceptionally educational

Return:
- a ranked shortlist
- one sentence on why each repo deserves inclusion
- one sentence on what a junior developer would learn from each
- any gaps in the candidate set

Be concrete and cite workspace files when possible.