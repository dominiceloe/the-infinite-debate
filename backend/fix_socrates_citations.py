#!/usr/bin/env python3
"""
Fix broken Socrates citation links in the database.
"""
import sqlite3
import json

# Database path
DB_PATH = '/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/db.sqlite3'

# Fixed URLs
FIXES = {
    # 1. MIT Classics Archive - Replace with Perseus Digital Library
    "https://classics.mit.edu/Plato/crito.html": {
        "title": "Plato's Crito (Perseus Digital Library)",
        "url": "https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0170"
    },

    # 2. Stanford Encyclopedia - Fix the URL (remove -historical)
    "https://plato.stanford.edu/entries/socrates-historical/": {
        "title": "The Historical Socrates - Stanford Encyclopedia",
        "url": "https://plato.stanford.edu/entries/socrates/"
    },

    # 3. Philosophy Bites - Remove (no working direct link found)
    "https://philosophybites.com/socrates/": None,

    # 4. BBC In Our Time - Fix the URL
    "https://www.bbc.co.uk/programmes/b00775bz": {
        "title": "BBC In Our Time: Socrates",
        "url": "https://www.bbc.co.uk/programmes/p003hyf6"
    },

    # 5. History of Philosophy - Fix the URL
    "https://historyofphilosophy.net/socrates": {
        "title": "History of Philosophy Without Any Gaps: Socrates without Plato",
        "url": "https://historyofphilosophy.net/socrates-without-plato"
    }
}

def fix_socrates_citations():
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get current Socrates external_links
    cursor.execute("SELECT external_links FROM personas_persona WHERE slug='socrates'")
    result = cursor.fetchone()

    if not result:
        print("ERROR: Socrates persona not found in database")
        return

    external_links = json.loads(result[0])
    print("Original external_links:")
    print(json.dumps(external_links, indent=2))
    print("\n" + "="*80 + "\n")

    changes_made = []

    # Fix primary_works
    if 'primary_works' in external_links:
        new_primary_works = []
        for work in external_links['primary_works']:
            if work['url'] in FIXES:
                fix = FIXES[work['url']]
                if fix is not None:
                    new_primary_works.append(fix)
                    changes_made.append(f"PRIMARY WORKS: Updated '{work['title']}' -> '{fix['title']}'")
                else:
                    changes_made.append(f"PRIMARY WORKS: Removed '{work['title']}'")
            else:
                new_primary_works.append(work)
        external_links['primary_works'] = new_primary_works

    # Fix academic links
    if 'academic' in external_links:
        new_academic = []
        for link in external_links['academic']:
            if link['url'] in FIXES:
                fix = FIXES[link['url']]
                if fix is not None:
                    new_academic.append(fix)
                    changes_made.append(f"ACADEMIC: Updated '{link['title']}' -> '{fix['title']}'")
                else:
                    changes_made.append(f"ACADEMIC: Removed '{link['title']}'")
            else:
                new_academic.append(link)
        external_links['academic'] = new_academic

    # Fix modern links
    if 'modern' in external_links:
        new_modern = []
        for link in external_links['modern']:
            if link['url'] in FIXES:
                fix = FIXES[link['url']]
                if fix is not None:
                    new_modern.append(fix)
                    changes_made.append(f"MODERN: Updated '{link['title']}' -> '{fix['title']}'")
                else:
                    changes_made.append(f"MODERN: Removed '{link['title']}'")
            else:
                new_modern.append(link)
        external_links['modern'] = new_modern

    print("Changes made:")
    for change in changes_made:
        print(f"  - {change}")
    print("\n" + "="*80 + "\n")

    print("Updated external_links:")
    print(json.dumps(external_links, indent=2))
    print("\n" + "="*80 + "\n")

    # Update database
    cursor.execute(
        "UPDATE personas_persona SET external_links = ? WHERE slug = 'socrates'",
        (json.dumps(external_links),)
    )

    conn.commit()
    conn.close()

    print(f"✅ Successfully updated {len(changes_made)} citations for Socrates")
    print("\nSummary of fixes:")
    print("1. MIT Classics Crito → Perseus Digital Library Crito")
    print("2. Stanford Encyclopedia (historical) → Stanford Encyclopedia (main)")
    print("3. Philosophy Bites → REMOVED (no working link)")
    print("4. BBC In Our Time → Updated to correct programme ID")
    print("5. History of Philosophy → Updated to 'Socrates without Plato' episode")

if __name__ == '__main__':
    fix_socrates_citations()
