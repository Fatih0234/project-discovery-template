---
mode: agent
description: "Deep-analyze one selected repository's usage of the target library for junior developers"
---

You are analyzing one real-world repository to explain how it uses a target library in practice.

Target library: ${input:library:Library or framework name}
Repository slug: ${input:repo:owner/repo or local repo identifier}
Audience: junior developers

Your job:
1. Identify where the library is actually used.
2. Explain what problem the library is solving in this repository.
3. Describe the usage style:
   - wrapper abstraction
   - decorator pattern
   - middleware / plugin
   - infrastructure helper
   - scattered utility calls
   - other
4. Extract the most educational usage points:
   - imports
   - key functions/classes/decorators
   - config choices
   - error-handling or retry logic
   - surrounding context
5. Translate the code usage into plain English.

Produce the following sections:
- What this project does
- Why this library is used here
- Where it appears in the codebase
- Usage pattern
- What juniors should notice
- What not to copy blindly
- One small exercise a learner could build after reading this repo

Keep the explanation practical and beginner-friendly.
Do not just restate code; explain intent and tradeoffs.
