#!/usr/bin/env python
"""Verify PERSONAS_TEXT_TRACKER.md is accurate against database."""

import django
import os
import re
from pathlib import Path
from collections import defaultdict

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from texts.models import PrimaryText

# Get all texts from database
db_texts = defaultdict(list)
for text in PrimaryText.objects.all().order_by('author', 'title'):
    db_texts[text.author].append(text.title)

# Read tracker file (in Docker: /app is backend/, so ../ is project root)
tracker_path = Path('/app/../PERSONAS_TEXT_TRACKER.md')
if not tracker_path.exists():
    print(f'❌ Tracker not found at {tracker_path}')
    exit(1)

content = tracker_path.read_text()

# Extract author entries from tracker
# Pattern: - [x] **AuthorName** - N texts: title1, title2
pattern = r'- \[x\] \*\*([^*]+)\*\* - \d+ texts?: ([^\n]+)'
tracker_authors = {}

for match in re.finditer(pattern, content):
    author = match.group(1)
    texts_str = match.group(2)
    texts = [t.strip() for t in texts_str.split(',')]
    tracker_authors[author] = texts

print(f'📊 Comparison Report:')
print(f'  Database: {len(db_texts)} authors, {sum(len(t) for t in db_texts.values())} texts')
print(f'  Tracker:  {len(tracker_authors)} authors, {sum(len(t) for t in tracker_authors.values())} texts')
print()

# Find discrepancies
all_authors = set(db_texts.keys()) | set(tracker_authors.keys())
discrepancies = []

for author in sorted(all_authors):
    db_count = len(db_texts.get(author, []))
    tracker_count = len(tracker_authors.get(author, []))

    if db_count != tracker_count:
        discrepancies.append({
            'author': author,
            'db_count': db_count,
            'tracker_count': tracker_count,
            'db_texts': db_texts.get(author, []),
            'tracker_texts': tracker_authors.get(author, [])
        })

if discrepancies:
    print('❌ DISCREPANCIES FOUND:\n')
    for d in discrepancies:
        print(f'  {d["author"]}:')
        print(f'    Database:  {d["db_count"]} texts')
        print(f'    Tracker:   {d["tracker_count"]} texts')
        if d['db_count'] > 0:
            print(f'    DB Texts:  {", ".join(d["db_texts"][:3])}...')
        if d['tracker_count'] > 0:
            print(f'    Tracker:   {", ".join(d["tracker_texts"][:3])}...')
        print()
else:
    print('✅ TRACKER IS ACCURATE!')
    print('   All authors and text counts match the database.')
