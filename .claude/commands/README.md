# Slash Commands for The Infinite Debate

Custom slash commands for the The Infinite Debate project. These commands invoke specialized agents and workflows.

## Available Commands

### `/audit-debate [target]`

**Purpose:** Audit debate quality for historical authenticity, style adherence, and engagement

**Invokes:** Debate Quality Auditor agent (`.claude/agents/debate-quality-auditor.md`)

**Usage:**

```bash
# Audit most recent debate
/audit-debate recent
/audit-debate

# Audit all debates from last week
/audit-debate week

# Audit all cross-tradition debates (theologians vs philosophers, etc.)
/audit-debate cross-tradition

# Audit all debates featuring a specific persona
/audit-debate luther
/audit-debate aquinas
/audit-debate sartre

# Audit specific debate by ID
/audit-debate 42

# Comprehensive audit of all debates
/audit-debate all
```

**What it does:**
1. Queries database for debate(s) matching target
2. Loads persona definitions for comparison
3. Scores each message on 5 criteria (Authenticity, Style, Citation, Character, Engagement)
4. Generates detailed reports with specific quotes and recommendations
5. Writes reports to `.reports/debate-quality/` or `.reports/persona-quality/scorecards/`

**Output:**
- Per-debate reports: `.reports/debate-quality/debates/{timestamp}_{topic}_{participants}.md`
- Aggregate summaries: `.reports/debate-quality/summaries/{date}_{description}.md`
- Persona scorecards: `.reports/persona-quality/scorecards/{persona-slug}.md`

**Example:**
```bash
/audit-debate aquinas

# Finds all debates with Aquinas, scores each message,
# writes scorecard to .reports/persona-quality/scorecards/aquinas.md
```

---

## Creating New Slash Commands

To create a new slash command for this project:

1. **Create file:** `.claude/commands/{command-name}.md`

2. **Add YAML frontmatter:**
```yaml
---
description: Short description of what this command does
arguments:
  - name: arg1
    description: What this argument does
    required: false
---
```

3. **Write instructions:** The markdown body contains the prompt that Claude Code will execute when the command is invoked.

4. **Reference agents:** If your command uses an agent, tell it to read the agent file:
```markdown
Read your full agent definition: `.claude/agents/{agent-name}.md`
```

5. **Test:** Run the command with `/command-name [args]`

---

## Command Guidelines

**Good slash commands:**
- Have clear, single purposes
- Reference agent files for detailed instructions
- Provide concrete examples of expected output
- Include quality standards and success criteria
- Write results to `.reports/` for tracking

**Avoid:**
- Hardcoding data that goes stale
- Overly generic commands that try to do too much
- Commands that duplicate existing functionality

---

**Last Updated:** 2025-10-19
