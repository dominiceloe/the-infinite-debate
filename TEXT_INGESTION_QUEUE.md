# Text Ingestion Queue

This file tracks primary texts to be ingested into The Infinite Debate platform.

**Ingestion Command:**
```bash
docker compose exec web python manage.py ingest_text \
  --url "<URL>" \
  --title "<Title>" \
  --author "<Author>"
```

---

## Priority 1: New Persona Texts (Jesus, Muhammad, Paul)

### The Gospels (Jesus of Nazareth)

Project Gutenberg has individual Bible books. The KJV Gospels are Books 40-43:

| Book | Title | URL | Status |
|------|-------|-----|--------|
| Matthew | Gospel of Matthew (KJV) | https://www.gutenberg.org/ebooks/8040 | ⏳ Pending |
| Mark | Gospel of Mark (KJV) | https://www.gutenberg.org/ebooks/8041 | ⏳ Pending |
| Luke | Gospel of Luke (KJV) | https://www.gutenberg.org/ebooks/8042 | ⏳ Pending |
| John | Gospel of John (KJV) | https://www.gutenberg.org/ebooks/8043 | ⏳ Pending |

**Commands:**
```bash
# Gospel of Matthew
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/8040/pg8040.txt" \
  --title "The Gospel of Matthew (KJV)" \
  --author "Anonymous"

# Gospel of Mark
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/8041/pg8041.txt" \
  --title "The Gospel of Mark (KJV)" \
  --author "Anonymous"

# Gospel of Luke
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/8042/pg8042.txt" \
  --title "The Gospel of Luke (KJV)" \
  --author "Anonymous"

# Gospel of John
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/8043/pg8043.txt" \
  --title "The Gospel of John (KJV)" \
  --author "Anonymous"
```

---

### The Quran (Muhammad)

Multiple English translations available on Project Gutenberg:

| Translation | Translator | URL | Status |
|-------------|------------|-----|--------|
| The Koran | J.M. Rodwell | https://www.gutenberg.org/ebooks/2800 | ⏳ Pending |
| The Koran | George Sale (1734) | https://www.gutenberg.org/ebooks/7440 | ⏳ Pending |
| Three Translations Side-by-Side | Yusuf Ali, Pickthall, et al. | https://www.gutenberg.org/ebooks/16955 | ⏳ Pending |

**Commands (choose one translation):**
```bash
# Rodwell Translation (recommended - most readable)
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/2800/pg2800.txt" \
  --title "The Quran (Rodwell Translation)" \
  --author "Muhammad (trans. J.M. Rodwell)"

# George Sale Translation (1734 - first English translation)
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/7440/pg7440.txt" \
  --title "The Quran (Sale Translation)" \
  --author "Muhammad (trans. George Sale)"
```

---

### Pauline Epistles (Paul the Apostle)

Paul's letters are Books 45-57 in the KJV:

| Book | Title | URL | Status |
|------|-------|-----|--------|
| Romans | Epistle to the Romans | https://www.gutenberg.org/ebooks/8045 | ⏳ Pending |
| 1 Corinthians | First Epistle to the Corinthians | https://www.gutenberg.org/ebooks/8046 | ⏳ Pending |
| 2 Corinthians | Second Epistle to the Corinthians | https://www.gutenberg.org/ebooks/8047 | ⏳ Pending |
| Galatians | Epistle to the Galatians | https://www.gutenberg.org/ebooks/8048 | ⏳ Pending |
| Ephesians | Epistle to the Ephesians | https://www.gutenberg.org/ebooks/8049 | ⏳ Pending |
| Philippians | Epistle to the Philippians | https://www.gutenberg.org/ebooks/8050 | ⏳ Pending |
| Colossians | Epistle to the Colossians | https://www.gutenberg.org/ebooks/8051 | ⏳ Pending |
| 1 Thessalonians | First Epistle to the Thessalonians | https://www.gutenberg.org/ebooks/8052 | ⏳ Pending |
| 2 Thessalonians | Second Epistle to the Thessalonians | https://www.gutenberg.org/ebooks/8053 | ⏳ Pending |
| 1 Timothy | First Epistle to Timothy | https://www.gutenberg.org/ebooks/8054 | ⏳ Pending |
| 2 Timothy | Second Epistle to Timothy | https://www.gutenberg.org/ebooks/8055 | ⏳ Pending |
| Titus | Epistle to Titus | https://www.gutenberg.org/ebooks/8056 | ⏳ Pending |
| Philemon | Epistle to Philemon | https://www.gutenberg.org/ebooks/8057 | ⏳ Pending |

**Commands (major epistles):**
```bash
# Romans
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/8045/pg8045.txt" \
  --title "Epistle to the Romans (KJV)" \
  --author "Paul the Apostle"

# 1 Corinthians
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/8046/pg8046.txt" \
  --title "First Epistle to the Corinthians (KJV)" \
  --author "Paul the Apostle"

# 2 Corinthians
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/8047/pg8047.txt" \
  --title "Second Epistle to the Corinthians (KJV)" \
  --author "Paul the Apostle"

# Galatians
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/8048/pg8048.txt" \
  --title "Epistle to the Galatians (KJV)" \
  --author "Paul the Apostle"

# Philippians
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/cache/epub/8050/pg8050.txt" \
  --title "Epistle to the Philippians (KJV)" \
  --author "Paul the Apostle"
```

---

## Priority 2: Existing Personas Without Texts

_See PERSONAS_TEXT_TRACKER.md for full list of pending texts._

---

## Ingestion Notes

1. **URL Format**: Project Gutenberg plain text files follow pattern: `https://www.gutenberg.org/cache/epub/{ID}/pg{ID}.txt`

2. **Author Attribution**:
   - Use traditional attribution (e.g., "Moses (Traditional)") for ancient texts
   - Include translator for translations (e.g., "Muhammad (trans. J.M. Rodwell)")

3. **After Ingestion**: Run citation extraction to link debate messages:
   ```bash
   docker compose exec web python manage.py extract_citations --min-confidence 0.7
   ```

---

## Sources

- [Project Gutenberg King James Bible](https://www.gutenberg.org/ebooks/10)
- [The Koran - Rodwell Translation](https://www.gutenberg.org/ebooks/2800)
- [Three Translations of the Koran](https://www.gutenberg.org/ebooks/16955)
- [Project Gutenberg Islam Bookshelf](https://www.gutenberg.org/ebooks/bookshelf/126)
