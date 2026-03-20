---
mode: agent
description: "Write a polished final markdown report summarizing how a library is used across the top example projects"
---

You are writing the final learning report for a junior developer who wants to understand how a library is used in real projects.

Target library: ${input:library:Library or framework name}
Target audience: junior developers
Desired tone: practical, clear, encouraging

Use the structured artifacts already generated in this workspace, especially:
- candidate and ranked repo JSON files
- per-repo analysis files (top_repos/*.json), which include `code_snippets` with actual file paths and line numbers
- markdown templates if present

Write a final report that includes:
1. A short overview of what the library is commonly used for
2. A concise summary of the top example projects
3. A per-project breakdown covering:
   - what the project is
   - where the library is used (cite the specific file path from `matched_files` or `code_snippets`)
   - what usage style it demonstrates (cite actual code from `code_snippets` where available)
   - what a junior should learn from it
4. Cross-project synthesis:
   - recurring patterns (with citations to repos and files)
   - interesting differences
   - best beginner examples
5. Common mistakes or caveats
6. Suggested follow-up mini projects for the learner

Requirements:
- **Every claim about how the library is used must cite a specific repo name and file path.**
- **If you cannot cite direct code evidence for a claim, write: "No direct code evidence available for this claim."**
- **Do not infer usage patterns from descriptions or topic tags alone — require code evidence.**
- Prefer concrete observations over generic advice
- Optimize for readability
- Avoid buzzwords and filler
- Call out uncertainty where evidence is weak
- End with a "start here first" recommendation for the learner
