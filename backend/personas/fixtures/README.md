# Philosophical Debate Personas

This directory contains persona definitions for 33 historical thinkers used in the Philosophical Debates platform. Each persona is defined in a structured markdown file containing their philosophical positions, debate style, and biographical information.

## Overview

- **Total Personas**: 33
- **Categories**: 3 (Theologians, Philosophers, Scientists)
- **Time Span**: 6th century BCE to 20th century CE
- **Geographic Coverage**: Global (China, India, Greece, Rome, Middle East, Europe, America)

---

## Directory Structure

```
personas/
├── theologians/     (11 personas)
├── philosophers/    (11 personas)
└── scientists/      (11 personas)
```

---

## Theologians (11)

Religious thinkers, mystics, and theologians from diverse traditions.

| Name | Era | Tradition | Slug |
|------|-----|-----------|------|
| **Laozi** | 6th century BCE | Daoism | `laozi` |
| **Nāgārjuna** | 2nd-3rd century CE | Buddhism (Madhyamaka) | `nagarjuna` |
| **Plotinus** | 3rd century CE | Neoplatonism | `plotinus` |
| **Augustine of Hippo** | 4th-5th century CE | Christianity (Catholic) | `augustine-of-hippo` |
| **Adi Śaṅkara** | 8th century CE | Hinduism (Advaita Vedānta) | `adi-sankara` |
| **Rāmānuja** | 11th-12th century CE | Hinduism (Vishishtadvaita) | `ramanuja` |
| **Al-Ghazālī** | 11th-12th century CE | Islam (Sufism) | `al-ghazali` |
| **Moses Maimonides** | 12th century CE | Judaism | `moses-maimonides` |
| **Thomas Aquinas** | 13th century CE | Christianity (Catholic) | `thomas-aquinas` |
| **Martin Luther** | 16th century CE | Christianity (Protestant) | `martin-luther` |
| **Karl Barth** | 20th century CE | Christianity (Neo-Orthodox) | `karl-barth` |

**Key Themes**: Faith vs. reason, nature of God, revelation, mystical experience, theodicy, religious authority

---

## Philosophers (11)

Secular philosophers exploring metaphysics, epistemology, ethics, and existence.

| Name | Era | School/Movement | Slug |
|------|-----|-----------------|------|
| **Confucius** | 6th-5th century BCE | Confucianism | `confucius` |
| **Socrates** | 5th century BCE | Classical Greek | `socrates` |
| **Plato** | 4th century BCE | Classical Greek (Idealism) | `plato` |
| **Aristotle** | 4th century BCE | Classical Greek (Empiricism) | `aristotle` |
| **René Descartes** | 17th century CE | Rationalism | `rene-descartes` |
| **David Hume** | 18th century CE | Empiricism/Skepticism | `david-hume` |
| **Immanuel Kant** | 18th century CE | Critical Philosophy | `immanuel-kant` |
| **Søren Kierkegaard** | 19th century CE | Existentialism | `sren-kierkegaard` |
| **Karl Marx** | 19th century CE | Historical Materialism | `karl-marx` |
| **Jean-Paul Sartre** | 20th century CE | Existentialism (Atheistic) | `jean-paul-sartre` |
| **Simone de Beauvoir** | 20th century CE | Existentialism/Feminism | `simone-de-beauvoir` |

**Key Themes**: Knowledge, reality, ethics, political philosophy, existence, freedom, meaning

---

## Scientists (11)

Revolutionary scientific thinkers who transformed our understanding of nature.

| Name | Era | Field | Slug |
|------|-----|-------|------|
| **Nicolaus Copernicus** | 15th-16th century CE | Astronomy | `nicolaus-copernicus` |
| **Johannes Kepler** | 17th century CE | Astronomy/Mathematics | `johannes-kepler` |
| **Galileo Galilei** | 17th century CE | Physics/Astronomy | `galileo-galilei` |
| **Isaac Newton** | 17th-18th century CE | Physics/Mathematics | `isaac-newton` |
| **Charles Darwin** | 19th century CE | Biology/Evolution | `charles-darwin` |
| **Louis Pasteur** | 19th century CE | Microbiology | `louis-pasteur` |
| **James Clerk Maxwell** | 19th century CE | Electromagnetism | `james-clerk-maxwell` |
| **Nikola Tesla** | 19th-20th century CE | Electrical Engineering | `nikola-tesla` |
| **Marie Curie** | 19th-20th century CE | Radioactivity | `marie-curie` |
| **Albert Einstein** | 20th century CE | Physics (Relativity) | `albert-einstein` |
| **Niels Bohr** | 20th century CE | Quantum Mechanics | `niels-bohr` |

**Key Themes**: Scientific method, observation vs. theory, determinism vs. probability, reductionism, progress

---

## Persona File Structure

Each persona markdown file contains:

### Required Sections:
- **Identity**: Name, title, religion/worldview, era, primary works
- **Core Philosophical Positions**: Key doctrines, beliefs, and arguments
- **Debate Style and Approach**: Methodology, tone, rhetorical strengths
- **Key Concepts and Terminology**: Essential vocabulary and ideas
- **Engagement with Other Traditions**: How they would interact with other thinkers
- **Representative Quotes/Positions**: Characteristic statements
- **Debate Priorities**: Ordered list of debate strategies (numbered 1-5+)
- **Potential Weaknesses/Vulnerabilities**: Areas where the position is challenged
- **Character Notes**: Guidance for embodying the persona

### Metadata:
- **Slug**: URL-friendly identifier (e.g., `thomas-aquinas`)
- **Birth Year**: Used for chronological debate ordering
- **Death Year**: Historical context
- **Category**: `theologian`, `philosopher`, or `scientist`

---

## Loading Personas into Database

Personas are loaded from these markdown files into the Django database using:

```bash
python manage.py load_personas
```

This command:
- Parses all `.md` files in `theologians/`, `philosophers/`, `scientists/`
- Extracts structured data and full markdown content
- Creates or updates `Persona` model instances in the database
- Enables querying by category, chronological order, etc.

---

## Debate Turn Order

In multi-participant debates, personas speak in **chronological order by birth year**:

1. Confucius (551 BCE)
2. Laozi (6th century BCE)
3. Socrates (470 BCE)
4. Plato (427 BCE)
5. Aristotle (384 BCE)
6. Nāgārjuna (c. 150 CE)
7. Plotinus (204 CE)
8. Augustine (354 CE)
9. Śaṅkara (788 CE)
10. Rāmānuja (1017 CE)
11. Al-Ghazālī (1058 CE)
12. Maimonides (1138 CE)
13. Aquinas (1225 CE)
14. Luther (1483 CE)
15. Copernicus (1473 CE)
16. Kepler (1571 CE)
17. Galileo (1564 CE)
18. Descartes (1596 CE)
19. Newton (1643 CE)
20. Hume (1711 CE)
21. Kant (1724 CE)
22. Pasteur (1822 CE)
23. Darwin (1809 CE)
24. Kierkegaard (1813 CE)
25. Maxwell (1831 CE)
26. Marx (1818 CE)
27. Tesla (1856 CE)
28. Curie (1867 CE)
29. Einstein (1879 CE)
30. Bohr (1885 CE)
31. Barth (1886 CE)
32. Sartre (1905 CE)
33. de Beauvoir (1908 CE)

---

## Notable Cross-Tradition Debates

These personas enable fascinating cross-cultural and cross-temporal dialogues:

### Faith & Reason:
- Aquinas (Catholic rationalism) vs. Luther (Protestant fideism)
- Al-Ghazālī (Islamic mysticism) vs. Maimonides (Jewish rationalism)
- Barth (revelation alone) vs. Descartes (rational proof)

### Metaphysics:
- Plato (Forms) vs. Aristotle (Substance)
- Śaṅkara (Non-dualism) vs. Rāmānuja (Qualified non-dualism)
- Nāgārjuna (Emptiness) vs. Plotinus (The One)

### Science & Religion:
- Darwin (Evolution) vs. Aquinas (Divine Design)
- Einstein (Relativity) vs. Newton (Absolute Space/Time)
- Galileo (Heliocentrism) vs. Augustine (Scripture)

### Existence & Freedom:
- Kierkegaard (Leap of Faith) vs. Sartre (Radical Freedom)
- Confucius (Social Harmony) vs. Marx (Class Struggle)
- de Beauvoir (Feminist Existentialism) vs. Traditional Thinkers

---

## Adding New Personas

To add a new persona:

1. Create a new `.md` file in the appropriate category directory
2. Use an existing persona as a template
3. Include all required sections (see structure above)
4. Run `python manage.py load_personas` to import
5. Verify in Django admin or API

**Naming Convention**: Use lowercase with hyphens (e.g., `friedrich-nietzsche.md`)

---

## Version History

- **2025-10-16**: Fixed typo: Updated category from incorrect "theologist" to correct "theologian" (33 personas)
- **2025-10-15**: Initial collection (33 personas across 3 categories)

---

## License & Attribution

These persona definitions are synthesized from public domain historical and philosophical sources. They represent scholarly interpretations of each thinker's positions and should be used for educational purposes.
