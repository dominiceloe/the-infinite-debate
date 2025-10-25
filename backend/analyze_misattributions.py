#!/usr/bin/env python
"""
Analyze potential misattributions in ingested texts.
Identifies texts where the Gutenberg author doesn't match the persona attribution.
"""
import os
import sys
import re
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from texts.models import PrimaryText
from personas.models import Persona

REPORT_FILE = Path(__file__).parent.parent / "MISATTRIBUTION_REVIEW.md"

def analyze_text(text):
    """
    Analyze a single text for potential misattribution.
    Returns dict with analysis results.
    """
    issues = []
    confidence = "low"  # low, medium, high

    title_lower = text.title.lower()
    author_lower = text.author.lower()

    # Check 1: "about" or "biography" in title
    if any(word in title_lower for word in ['about', 'biography', 'life of', 'story of', 'memoirs']):
        issues.append("Title suggests biography/commentary")
        confidence = "high"

    # Check 2: Different author name embedded in title
    # Look for patterns like "by AuthorName" or "AuthorName" at start
    if re.search(r'\bby\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', text.title, re.IGNORECASE):
        match = re.search(r'\bby\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', text.title, re.IGNORECASE)
        embedded_author = match.group(1)
        if embedded_author.lower() != author_lower:
            issues.append(f"Different author in title: '{embedded_author}'")
            confidence = "high"

    # Check 3: Author name remnants in cleaned title
    # After cleanup, if title still contains what looks like an author name at end
    author_parts = author_lower.split()
    for part in author_parts:
        if len(part) > 3 and part in title_lower.split():
            # Check if it's at the end
            if title_lower.endswith(part):
                issues.append(f"Author name '{part}' found at end of title")
                confidence = "medium"

    # Check 4: Known misattribution patterns
    misattribution_patterns = [
        ('Frankenstein', 'Mary Wollstonecraft', 'Should be Mary Shelley'),
        ('Seekers after God', 'Epictetus', 'About Epictetus, by F.W. Farrar'),
        ('Ancient and Modern Celebrated Freethinkers', 'Epicurus', 'Anthology about multiple thinkers'),
    ]

    for pattern_title, pattern_author, explanation in misattribution_patterns:
        if pattern_title.lower() in title_lower and pattern_author.lower() in author_lower:
            issues.append(f"KNOWN MISATTRIBUTION: {explanation}")
            confidence = "high"

    # Check 5: Persona mismatch
    try:
        persona = Persona.objects.filter(name__iexact=text.author).first()
        if not persona:
            issues.append(f"No persona found for author '{text.author}'")
            confidence = "medium"
    except:
        pass

    return {
        'id': text.id,
        'title': text.title,
        'author': text.author,
        'source_url': text.source_url,
        'word_count': text.word_count,
        'issues': issues,
        'confidence': confidence,
        'suspicious': len(issues) > 0
    }

def generate_report(analyses):
    """Generate misattribution report"""
    suspicious = [a for a in analyses if a['suspicious']]
    high_confidence = [a for a in suspicious if a['confidence'] == 'high']
    medium_confidence = [a for a in suspicious if a['confidence'] == 'medium']
    low_confidence = [a for a in suspicious if a['confidence'] == 'low']

    report = f"""# Misattribution Review Report

**Generated:** {django.utils.timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total texts analyzed:** {len(analyses)}
- **Suspicious texts:** {len(suspicious)}
  - High confidence misattributions: {len(high_confidence)}
  - Medium confidence misattributions: {len(medium_confidence)}
  - Low confidence misattributions: {len(low_confidence)}
- **Clean attributions:** {len(analyses) - len(suspicious)}

---

## HIGH CONFIDENCE MISATTRIBUTIONS

These texts are very likely misattributed and should be reviewed immediately:

"""

    if high_confidence:
        for analysis in high_confidence:
            report += f"""
### [{analysis['id']}] {analysis['title']}

**Currently attributed to:** {analysis['author']}
**Word count:** {analysis['word_count']:,}
**Source:** {analysis['source_url']}

**Issues identified:**
"""
            for issue in analysis['issues']:
                report += f"- {issue}\n"

            report += f"""
**Recommendation:** Review and correct attribution or delete if not relevant.

---
"""
    else:
        report += "\n*None found*\n"

    report += """
---

## MEDIUM CONFIDENCE MISATTRIBUTIONS

These texts may have attribution issues and should be spot-checked:

"""

    if medium_confidence:
        for analysis in medium_confidence:
            report += f"""
### [{analysis['id']}] {analysis['title']}

**Currently attributed to:** {analysis['author']}
**Source:** {analysis['source_url']}

**Issues:**
"""
            for issue in analysis['issues']:
                report += f"- {issue}\n"
            report += "\n"
    else:
        report += "\n*None found*\n"

    report += """
---

## LOW CONFIDENCE ISSUES

These may have minor issues but are likely correct:

"""

    if low_confidence:
        for analysis in low_confidence:
            report += f"- [{analysis['id']}] {analysis['author']} - {analysis['title']}\n"
    else:
        report += "\n*None found*\n"

    report += f"""
---

## Recommended Actions

### For HIGH confidence misattributions ({len(high_confidence)} texts):

1. **Review each text** in the Django admin or database
2. **Options:**
   - Delete if completely wrong (e.g., Frankenstein under Mary Wollstonecraft)
   - Correct attribution if it's just a name issue
   - Add metadata flag "related_work" instead of "primary_work" if keeping

### For MEDIUM confidence misattributions ({len(medium_confidence)} texts):

1. **Spot check** 2-3 examples
2. **Decide policy:** Keep as "related works" or remove?

### For LOW confidence ({len(low_confidence)} texts):

- Generally safe to ignore unless you notice specific issues

---

## SQL Quick Fixes

To delete known misattributions:

```sql
-- Example: Delete Frankenstein from Mary Wollstonecraft
DELETE FROM texts_primarytext
WHERE title LIKE 'Frankenstein%' AND author = 'Mary Wollstonecraft';

-- Or use Django:
-- PrimaryText.objects.filter(title__icontains='Frankenstein', author='Mary Wollstonecraft').delete()
```

---

**Script:** `backend/analyze_misattributions.py`
"""

    return report

def main():
    """Main execution"""
    print("="*60)
    print("Misattribution Analysis")
    print("="*60)
    print()

    # Get all texts
    texts = PrimaryText.objects.all().order_by('author', 'title')
    total = texts.count()

    print(f"Analyzing {total} texts...\n")

    analyses = []
    suspicious_count = 0

    # Analyze each text
    for text in texts:
        analysis = analyze_text(text)
        analyses.append(analysis)

        if analysis['suspicious']:
            suspicious_count += 1
            if analysis['confidence'] == 'high':
                print(f"🚨 HIGH: [{text.id}] {text.author} - {text.title}")
                for issue in analysis['issues']:
                    print(f"   └─ {issue}")
            elif analysis['confidence'] == 'medium':
                print(f"⚠️  MEDIUM: [{text.id}] {text.author} - {text.title}")

    print("\n" + "="*60)
    print(f"Analysis complete!")
    print(f"  Suspicious: {suspicious_count} texts")
    print(f"  Clean: {total - suspicious_count} texts")
    print("="*60)

    # Generate report
    report = generate_report(analyses)
    with open(REPORT_FILE, 'w') as f:
        f.write(report)

    print(f"\nReport saved to: {REPORT_FILE}")

if __name__ == '__main__':
    main()
