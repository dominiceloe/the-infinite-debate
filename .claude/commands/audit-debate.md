---
description: Audit debate quality for historical authenticity, style adherence, and engagement
arguments:
  - name: target
    description: |
      What to audit:
      - "recent" - Most recent completed debate
      - "week" - All debates from last 7 days
      - "cross-tradition" - All cross-category debates (theologians vs philosophers, etc.)
      - "{persona-slug}" - All debates featuring specific persona (e.g., "luther", "aquinas")
      - "{debate-slug}" - Specific debate by slug (e.g., "afterlife-21873b4e")
      - "all" - All completed debates (comprehensive audit)
    required: false
---

# Debate Quality Auditor

You are invoking the **Debate Quality Auditor** agent to assess historical authenticity and debate quality.

## Agent Reference

**Full Agent Definition:** `.claude/agents/debate-quality-auditor.md`

The agent is an expert in:
- Historical authenticity assessment (philosophy, science, theology, culture)
- Debate style analysis (dialectical, systematic, empirical methodologies)
- Citation validation (primary work references)
- Character embodiment (personality, voice, quirks)
- Engagement quality (substantive vs. superficial responses)

## What The Agent Will Do

### 1. Query & Select Debates
- Access PostgreSQL database via Docker
- Find debates matching your target criteria
- Prioritize strategically (cross-tradition, 3+ rounds, new personas)

### 2. Load Persona Definitions
- Retrieve persona data from database
- Compare against core positions, debate style, character notes
- Identify expected behavior for each historical figure

### 3. Score Messages
- Evaluate each message on 5 criteria (1-10 scale):
  - **Authenticity** - Matches documented positions?
  - **Style Adherence** - Follows debate methodology?
  - **Citation Quality** - References primary works appropriately?
  - **Character Consistency** - Maintains personality and voice?
  - **Engagement** - Responds substantively to previous round?

### 4. Generate Reports
- Write detailed reports to `.reports/debate-quality/debates/`
- Include scoring breakdown, specific quotes, recommendations
- Create aggregate summaries for multi-debate audits

## Execution

**Delegate to the specialized agent using the Task tool:**

```
Task tool invocation:
- subagent_type: "general-purpose"
- description: "Audit debate quality"
- prompt: |
    You are the Debate Quality Auditor agent.

    **Step 1:** Read your full agent definition at:
    .claude/agents/debate-quality-auditor.md

    **Step 2:** Audit debates matching target: "{target}"

    **Step 3:** Follow your 4-phase workflow:
    1. Query & Select Debates (PostgreSQL via Docker)
    2. Load Persona Definitions (from database)
    3. Score Messages (5 criteria: Authenticity, Style, Citation, Character, Engagement)
    4. Generate Reports (to .reports/debate-quality/)

    **Database Access:**
    Use Docker to access Django ORM from ideas/philosophical-debates/backend:
    ```
    docker compose exec web python manage.py shell -c "
    from debates.models import Debate

    # For 'recent': Find most recent completed debate
    debate = Debate.objects.filter(status='completed').order_by('-completed_at').first()

    # For specific slug: Get debate by slug
    debate = Debate.objects.get(slug='afterlife-21873b4e')

    # For persona: Find all debates with that persona
    debates = Debate.objects.filter(participants__slug='buddha', status='completed')

    # Then analyze and score
    "
    ```

    **Success Criteria:**
    - Report written to .reports/debate-quality/debates/
    - Overall score calculated (pass threshold: ≥7.0/10)
    - Specific quotes included (best/worst moments)
    - Actionable recommendations provided

    Work autonomously with full database access.
```

## Expected Output

After the agent completes, you'll receive:

**For single debate:**
```
✅ Audit Complete

📊 Overall Score: 8.2/10 (PASS)

Audited: "Is there an afterlife?" (Buddha vs Marx, 2 rounds)

Key Findings:
- Buddha effectively uses Middle Way philosophy (authenticity: 9/10)
- Marx's materialist analysis clear (style: 8.5/10)
- Good dialectical engagement across worldviews
- Could use more citations (Buddha: Dhammapada, Marx: Das Kapital)

Recommendations:
- Strengthen citation prompts for both personas
- Consider expanding rounds for deeper engagement

📄 Full Report: .reports/debate-quality/debates/2025-10-21_afterlife_buddha-marx.md
```

**For aggregate audits:**
```
📊 Quality Summary

Debates Audited: 13
Average Score: 8.9/10
Pass Rate: 100% (all ≥7.0)

Top Performers:
- Friedman vs Friedan (9.2/10) - Strong character differentiation
- Plato vs Aristotle (9.0/10) - Authentic philosophical tension

See: .reports/debate-quality/summaries/2025-10_weekly-audit.md
```

## Troubleshooting

**If no debates found:**
```bash
# Check Docker services running
cd ideas/philosophical-debates/backend
docker compose ps

# Count completed debates
docker compose exec web python manage.py shell -c "
from debates.models import Debate
print(f'Completed debates: {Debate.objects.filter(status=\"completed\").count()}')
"
```

**If database access fails:**
```bash
# Restart services
docker compose restart web

# Check logs
docker compose logs web --tail=50
```

**If persona data missing:**
All persona data is in PostgreSQL (not markdown files for production debates).
Fields available: `core_positions`, `debate_style`, `character_notes`, `key_concepts`, `era`, `category`

**If agent needs more context:**
The agent file (`.claude/agents/debate-quality-auditor.md`) contains:
- Detailed scoring methodology
- Report templates
- Quality standards (passing thresholds, red flags)
- Concrete workflow examples with code

## Quality Standards

**Passing Thresholds:**
- Message-level: ≥7.0/10 overall, no criterion <6.0
- Debate-level: ≥7.0/10 average, 50%+ citations (if texts available)
- Persona-level: ≥7.5/10 average, std dev <1.5

**Red Flags (Immediate attention):**
- Persona score <5.0/10 (fundamentally broken)
- Anachronistic language (modern terms in ancient debates)
- Wrong philosophical positions
- No character traits (generic AI voice)
- Zero citations when primary texts available
- No engagement with previous rounds

---

**Now execute the audit by delegating to the specialized agent.**
