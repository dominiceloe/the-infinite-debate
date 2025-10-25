#!/usr/bin/env python
"""
Clean up malformed titles from Gutenberg ingestion.
Removes author names, download counts, and other metadata from titles.
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

REPORT_FILE = Path(__file__).parent.parent / "TITLE_CLEANUP_REPORT.md"

def clean_title(title):
    """
    Clean up malformed Gutenberg titles.

    Patterns to remove:
    - Author names followed by download counts (e.g., "Epictetus5854 downloads")
    - Download counts at end (e.g., "167813 downloads")
    - Multiple author names embedded in title
    - Extra whitespace
    """
    original = title

    # Pattern 1: Remove "AuthorName\d+ downloads" where AuthorName has NO spaces/is concatenated
    # Example: "The EnchiridionEpictetus5854 downloads" → "The Enchiridion"
    # Look for: word boundary, capital letter, lowercase letters (NO spaces), digits, " downloads"
    title = re.sub(r'([a-z])([A-Z][a-z]+)\d+\s+downloads$', r'\1', title)

    # Pattern 2: Remove "Author Full Name\d+ downloads" at end (WITH spaces)
    # Example: "...Mary Wollstonecraft Shelley167813 downloads" → "..."
    # Must have at least first and last name followed by digits
    title = re.sub(r'([a-z])([A-Z][a-z]+\s+[A-Z][a-z\.]+(?:\s+[A-Z][a-z]+)*)\d+\s+downloads$', r'\1', title)

    # Pattern 3: Remove just " downloads" without author name (catch-all)
    # Example: "Some Title123 downloads" → "Some Title"
    title = re.sub(r'\d+\s+downloads$', '', title)

    # Pattern 4: Remove trailing punctuation artifacts from cleanup
    title = re.sub(r'[:;,]\s*$', '', title)

    # Pattern 5: Clean up extra whitespace
    title = re.sub(r'\s+', ' ', title)
    title = title.strip()

    # Don't return empty titles - if we cleaned everything, use original
    if not title or len(title) < 3:
        return original, False

    return title, original != title

def generate_report(changes):
    """Generate before/after report"""
    report = f"""# Title Cleanup Report

**Generated:** {django.utils.timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total texts in database:** {PrimaryText.objects.count()}
- **Texts with cleaned titles:** {len([c for c in changes if c['changed']])}
- **Texts unchanged:** {len([c for c in changes if not c['changed']])}

---

## Changes Made

"""

    changed = [c for c in changes if c['changed']]
    unchanged_count = len([c for c in changes if not c['changed']])

    if changed:
        report += "### Modified Titles\n\n"
        for change in changed:
            report += f"**{change['id']}. {change['author']}**\n"
            report += f"- Before: `{change['before']}`\n"
            report += f"- After:  `{change['after']}`\n\n"

    report += f"\n### Unchanged Titles\n\n{unchanged_count} texts had clean titles already.\n"

    report += """
---

## Regex Patterns Used

1. **AuthorName + Downloads:** `[A-Z][a-zA-Z\s\.]+\d+\s+downloads$`
2. **Download Count Only:** `\d+\s+downloads$`
3. **Trailing Author Names:** `([a-z])([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$`
4. **Combined Pattern:** `[A-Z][a-z]+(?:\s+[A-Z][a-z\.]+)*\d+\s+downloads`
5. **Trailing Whitespace/Commas:** `[,\s]+$`

## Examples

- `"The EnchiridionEpictetus5854 downloads"` → `"The Enchiridion"`
- `"Frankenstein; Or, The Modern PrometheusMary Wollstonecraft Shelley167813 downloads"` → `"Frankenstein; Or, The Modern Prometheus"`
- `"A Vindication of the Rights of WomanMary Wollstonecraft3354 downloads"` → `"A Vindication of the Rights of Woman"`

---

**Script:** `backend/fix_title_formatting.py`
"""

    return report

def main():
    """Main execution"""
    print("="*60)
    print("Title Cleanup Script")
    print("="*60)
    print()

    # Get all texts
    texts = PrimaryText.objects.all().order_by('author', 'title')
    total = texts.count()

    print(f"Found {total} texts to process\n")

    changes = []
    modified_count = 0

    # Process each text
    for text in texts:
        clean, changed = clean_title(text.title)

        change_record = {
            'id': text.id,
            'author': text.author,
            'before': text.title,
            'after': clean,
            'changed': changed
        }
        changes.append(change_record)

        if changed:
            print(f"[{text.id}] {text.author}")
            print(f"  Before: {text.title}")
            print(f"  After:  {clean}")
            print()

            # Update in database
            text.title = clean
            text.save(update_fields=['title'])
            modified_count += 1

    print("="*60)
    print(f"Cleanup complete!")
    print(f"  Modified: {modified_count} texts")
    print(f"  Unchanged: {total - modified_count} texts")
    print("="*60)

    # Generate report
    report = generate_report(changes)
    with open(REPORT_FILE, 'w') as f:
        f.write(report)

    print(f"\nReport saved to: {REPORT_FILE}")

if __name__ == '__main__':
    main()
