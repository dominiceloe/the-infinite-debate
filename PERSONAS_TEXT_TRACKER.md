# Persona Primary Texts Tracker

**Last Updated:** 2025-10-24

Track which personas have primary texts ingested into the database and external citations validated.

## Recent Updates

### 🎊🎊🎊 RECOVERY COMPLETE: 885 Texts Ingested! 🎊🎊🎊 (2025-10-24)

**Recovery Ingestion Results (v2 with Fuzzy Matching):**
- 🚀 **576 NEW TEXTS ADDED** in recovery run (309 → 885 total!)
- 🎉 **115 total authors** now have primary texts (was 85 → +30 new authors!)
- 📚 **82,692 total sections** parsed across all texts (+193% increase!)
- 📖 **69,385,641 total words** (69+ million words of primary source material! +200% increase!)
- ✅ **196 personas processed** with fuzzy slug matching
- ⚡ **Major personas recovered** that failed in first run (Descartes, Kant, Shakespeare, Darwin, etc.)
- 🔧 **Fuzzy matching strategies:** exact → hyphenated → partial → name search
- 📊 **100% success rate** finding previously skipped personas

**Major New Additions:**
- **Aristotle:** 23 texts (was 14 → +9 texts)
- **Baruch Spinoza:** 22 texts (was 12 → +10 texts)
- **Confucius:** 21 texts (was 11 → +10 texts)
- **Bertrand Russell:** 19 texts (was 10 → +9 texts)
- **David Hume:** 13 texts (NEW!)
- **Clarence Darrow:** 14 texts (was 7 → +7 texts)
- **Charles Darwin:** 11 texts (NEW!)
- **Augustine of Hippo:** 11 texts (NEW!)
- **Dante Alighieri:** 11 texts (NEW!)
- **Adam Smith:** 11 texts (NEW!)
- **Carl Jung:** 9 texts (NEW!)
- **Albert Einstein:** 8 texts (NEW!)
- **Immanuel Kant:** 7 texts (NEW!)
- **William Shakespeare:** 10 texts (NEW!)
- **René Descartes:** 5 texts (NEW!)
- **Emma Goldman:** 10 texts (NEW!)
- **Edmund Burke:** 10 texts (NEW!)
- Plus 15+ more new authors with major works!

**Technical Details:**
- Script: `backend/ingest_all_personas_v2.py`
- Duration: ~1 hour 49 minutes
- Source: Project Gutenberg auto-discovery with fuzzy slug matching
- Rate limiting: 0.5-1s delays to respect Gutenberg servers
- Full logs: `RECOVERY_INGESTION_LOG.md`

**Quality Improvements:**
- ✅ Title cleanup: 27 texts had malformed titles fixed (removed Gutenberg metadata)
- ✅ Misattribution analysis: 41 suspicious texts flagged for review
- ✅ Fuzzy matching: Recovered ~100 personas that failed due to slug mismatch

---

### 🎉🎉🎉 TARGET 3 ACHIEVED: 309 Texts Ingested! 🎉🎉🎉 (2025-10-21)

**Overnight Batch Ingestion Results:**
- 🚀 **209 NEW TEXTS ADDED** in automated overnight run (100 → 309 total!)
- 🎊 **85 total authors** now have primary texts (was 60 → +25 new authors!)
- 📚 **28,216 total sections** parsed across all texts
- 📖 **23,111,313 total words** (23+ million words of primary source material!)
- ✅ **196 personas processed** via automated Project Gutenberg search
- ⚡ **35 personas** successfully matched and ingested
- 🔍 **Automated discovery** - script searched Gutenberg for each persona's works
- 📊 **100% ingestion success** for all discovered texts

**Major Additions:**
- **Epictetus:** 12 texts (Enchiridion, Discourses, Golden Sayings, Teaching, etc.)
- **Plato:** 21 texts total (11 new dialogues added)
- **Aristotle:** 14 texts total (9 new works added)
- **Socrates:** 10 texts (Platonic dialogues)
- **Confucius:** 11 texts (10 new works added)
- **Friedrich Nietzsche:** 12 texts (10 new works!)
- **Baruch Spinoza:** 12 texts (10 new works!)
- **Bertrand Russell:** 10 texts (9 new works!)
- **Sam Harris:** 10 texts (all new!)
- **The Buddha:** 10 texts (all new!)
- **William O. Douglas:** 10 texts (all new!)
- **Franz Boas:** 10 texts (all new!)
- **Mary Wollstonecraft:** 9 texts (all new!)
- **Plotinus:** 9 texts (all new!)
- **José Martí:** 9 texts (all new!)
- **Mary Douglas:** 9 texts (all new!)
- **Zora Neale Hurston:** 8 texts (all new!)
- **Clarence Darrow:** 7 texts (all new!)
- Plus 18 more new authors with 1-6 texts each!

**Technical Details:**
- Script: `backend/ingest_all_personas.py`
- Duration: ~9 hours (overnight automation)
- Source: Project Gutenberg auto-discovery
- Rate limiting: 1-2s delays to respect Gutenberg servers
- Full logs: `TEST_INGESTION_OVERNIGHT_OCT20.md`

### Previous Updates (2025-10-18)

### 🎉🎉🎉 TARGET 2 ACHIEVED: 100 Texts Ingested! 🎉🎉🎉

**Citation Validation & Fixes:**
- ✅ **All 196 personas** now have validated external citations (Further Reading sections)
- ✅ **97.8% validation rate** (227/232 citations valid, 0 broken links)
- ✅ Fixed all broken Socrates citations (5 links corrected)
- ✅ Standardized Project Gutenberg URLs to clean `/ebooks/{ID}` format
- ✅ Wikipedia links added to all 196 personas
- See CITATION_VALIDATION_REPORT.md for details

**Primary Texts Ingested:**
- 🎊 **100 total texts** (Target 2 COMPLETE! was 50 → +50 new texts!)
- 🎊 **60 personas** now have primary texts (was 32 → +28 new personas!)
- ✅ **100% ingestion success rate** - all texts properly parsed
- All texts available via REST API at `/api/texts/`
- Frontend library viewer at `/texts` with continuous & sections reading modes
- Updated ingestion command to automatically handle clean Gutenberg URLs

---

## Personas with Primary Texts (60 total)

### Philosophers (14)
- [x] **Plato** - 11 texts: Apology, Crito, Euthyphro, Meno, Phaedo, Phaedrus, Parmenides, Republic, Symposium, Theaetetus, Timaeus
- [x] **Aristotle** - 5 texts: Nicomachean Ethics, Politics, Metaphysics, Poetics, On the Soul (De Anima)
- [x] **Confucius** - 1 text: The Analects
- [x] **René Descartes** - 1 text: Discourse on Method
- [x] **David Hume** - 3 texts: A Treatise of Human Nature, An Enquiry Concerning Human Understanding, Dialogues Concerning Natural Religion
- [x] **Immanuel Kant** - 3 texts: Critique of Pure Reason, Critique of Practical Reason, Groundwork of the Metaphysics of Morals
- [x] **Søren Kierkegaard** - 1 text: Fear and Trembling
- [x] **Karl Marx** - 1 text: The Communist Manifesto
- [x] **Friedrich Nietzsche** - 2 texts: Thus Spoke Zarathustra, Beyond Good and Evil
- [x] **Baruch Spinoza** - 2 texts: Tractatus Theologico-Politicus, Ethics
- [x] **Bertrand Russell** - 1 text: The Problems of Philosophy
- [x] **John Stuart Mill** - 3 texts: On Liberty, Utilitarianism, The Subjection of Women
- [x] **Voltaire** - 1 text: Candide
- [x] **Jean-Jacques Rousseau** - 1 text: The Social Contract

### Theologians (6)
- [x] **Augustine of Hippo** - 2 texts: Confessions, The City of God
- [x] **Thomas Aquinas** - 1 text: Summa Theologica
- [x] **Martin Luther** - 2 texts: The Ninety-Five Theses, Table Talk
- [x] **Moses Maimonides** - 1 text: The Guide for the Perplexed
- [x] **Al-Ghazālī** - 1 text: The Alchemy of Happiness
- [x] **Laozi** - 1 text: Tao Te Ching

### Scientists (4)
- [x] **Charles Darwin** - 2 texts: On the Origin of Species, The Descent of Man
- [x] **Isaac Newton** - 1 text: Philosophiæ Naturalis Principia Mathematica
- [x] **Galileo Galilei** - 1 text: Dialogue Concerning the Two Chief World Systems
- [x] **Albert Einstein** - 1 text: Relativity: The Special and General Theory
- [x] **Nicolaus Copernicus** - 1 text: De revolutionibus orbium coelestium

### Political Theorists (3)
- [x] **Niccolò Machiavelli** - 1 text: The Prince
- [x] **Thomas Hobbes** - 1 text: Leviathan
- [x] **John Locke** - 1 text: Second Treatise of Government

### Economists (1)
- [x] **Adam Smith** - 1 text: An Inquiry into the Nature and Causes of the Wealth of Nations

### Ancient Schools (4)
- [x] **Homer** - 2 texts: The Odyssey, The Iliad
- [x] **Marcus Aurelius** - 1 text: Meditations
- [x] **Epictetus** - 1 text: Enchiridion
- [x] **Epicurus** - 1 text: Letter to Menoeceus

### Environmental Thinkers (1)
- [x] **Henry David Thoreau** - 1 text: Walden

### Psychologists (3)
- [x] **William James** - 1 text: The Principles of Psychology, Vol. 1
- [x] **Sigmund Freud** - 1 text: The Interpretation of Dreams
- [x] **Carl Jung** - 1 text: Psychology of the Unconscious

### Mystics (1)
- [x] **Rumi** - 1 text: The Masnavi

### Eastern Philosophers (3)
- [x] **Sun Tzu** - 1 text: The Art of War
- [x] **Zhuangzi** - 1 text: The Writings of Chuang Tzu
- [x] **Mencius** - 1 text: The Works of Mencius

### Literary Voices (18)
- [x] **William Shakespeare** - 5 texts: Hamlet, Macbeth, Romeo and Juliet, King Lear, Julius Caesar
- [x] **James Joyce** - 3 texts: Ulysses, Dubliners, A Portrait of the Artist as a Young Man
- [x] **Jane Austen** - 3 texts: Emma, Pride and Prejudice, Sense and Sensibility
- [x] **Charles Dickens** - 3 texts: Great Expectations, A Tale of Two Cities, A Christmas Carol
- [x] **Mark Twain** - 2 texts: Adventures of Huckleberry Finn, The Adventures of Tom Sawyer
- [x] **Fyodor Dostoevsky** - 2 texts: Crime and Punishment, The Brothers Karamazov
- [x] **Leo Tolstoy** - 2 texts: War and Peace, Anna Karenina
- [x] **Oscar Wilde** - 2 texts: The Importance of Being Earnest, The Picture of Dorian Gray
- [x] **Dante Alighieri** - 1 text: The Divine Comedy
- [x] **Virginia Woolf** - 1 text: Mrs Dalloway
- [x] **Herman Melville** - 1 text: Moby-Dick
- [x] **Franz Kafka** - 1 text: Metamorphosis
- [x] **Alexandre Dumas** - 1 text: The Count of Monte Cristo
- [x] **Mary Shelley** - 1 text: Frankenstein
- [x] **George Eliot** - 1 text: Middlemarch
- [x] **Charlotte Brontë** - 1 text: Jane Eyre
- [x] **Arthur Conan Doyle** - 1 text: The Adventures of Sherlock Holmes
- [x] **Elizabeth Gaskell** - 1 text: Cranford

### Other (1)
- [x] **Baltasar Gracián** - 1 text: The Art of Worldly Wisdom

---

## Personas Pending Primary Texts (136 total)

### Philosophers (0 remaining - all from original tracker complete!)

### Scientists (6 remaining)
- [ ] Niels Bohr
- [ ] James Clerk Maxwell
- [ ] Louis Pasteur
- [ ] Johannes Kepler
- [ ] Nikola Tesla
- [ ] Marie Curie

### Theologians (6 remaining)
- [ ] Karl Barth
- [ ] Nāgārjuna
- [ ] Plotinus
- [ ] Rāmānuja
- [ ] Adi Śaṅkara

### Political Theorists (3 remaining)
- [ ] Edmund Burke (1729-1797)
- [ ] Hannah Arendt (1906-1975)
- [ ] Frantz Fanon (1925-1961)

### Psychologists (3 remaining)
- [ ] B.F. Skinner (1904-1990)
- [ ] Viktor Frankl (1905-1997)
- [ ] Daniel Kahneman (1934-2024)

### Mystics (5 remaining)
- [ ] Meister Eckhart (1260-1328)
- [ ] Kabir (1440-1518)
- [ ] Teresa of Ávila (1515-1582)
- [ ] Ramana Maharshi (1879-1950)
- [ ] Dogen (1200-1253)

### Social Reformers (6)
- [ ] Mahatma Gandhi (1869-1948)
- [ ] Rosa Luxemburg (1871-1919)
- [ ] Martin Luther King Jr. (1929-1968)
- [ ] Malcolm X (1925-1965)
- [ ] Nelson Mandela (1918-2013)
- [ ] Emmeline Pankhurst (1858-1928)

### Economists (5 remaining)
- [ ] John Maynard Keynes (1883-1946)
- [ ] Friedrich Hayek (1899-1992)
- [ ] Milton Friedman (1912-2006)
- [ ] Amartya Sen (1933-present)
- [ ] Joseph Schumpeter (1883-1950)

### Artists & Aestheticians (7)
- [ ] Leonardo da Vinci (1452-1519)
- [ ] Vincent van Gogh (1853-1890)
- [ ] Pablo Picasso (1881-1973)
- [ ] Wassily Kandinsky (1866-1944)
- [ ] Oscar Wilde (1854-1900)
- [ ] John Cage (1912-1992)
- [ ] Frida Kahlo (1907-1954)

### Eastern Philosophers (5 remaining)
- [ ] Xunzi (c. 310-235 BCE)
- [ ] Mozi (c. 470-391 BCE)
- [ ] Zhu Xi (1130-1200)
- [ ] Wang Yangming (1472-1529)
- [ ] Thich Nhat Hanh (1926-2022)

### Environmental Thinkers (5 remaining)
- [ ] Aldo Leopold (1887-1948)
- [ ] Rachel Carson (1907-1964)
- [ ] Arne Næss (1912-2009)
- [ ] Vandana Shiva (1952-present)
- [ ] Robin Wall Kimmerer (1953-present)

### Ancient Schools (3 remaining)
- [ ] Diogenes of Sinope (c. 412-323 BCE)
- [ ] Hypatia of Alexandria (c. 360-415 CE)
- [ ] Pyrrho of Elis (c. 360-270 BCE)

### Literary Voices (2 remaining)
- [ ] Jorge Luis Borges (1899-1986)
- [ ] Toni Morrison (1931-2019)

### Comedians & Satirists (6 remaining)
- [ ] Lenny Bruce (1925-1966)
- [ ] George Carlin (1937-2008)
- [ ] Bill Hicks (1961-1994)
- [ ] Jon Stewart (1962-present)
- [ ] Dave Chappelle (1973-present)
- [ ] Hannah Gadsby (1978-present)

### Contemporary Public Intellectuals (7)
- [ ] Noam Chomsky (1928-present)
- [ ] Camille Paglia (1947-present)
- [ ] Slavoj Žižek (1949-present)
- [ ] Nassim Nicholas Taleb (1960-present)
- [ ] Jordan Peterson (1962-present)
- [ ] Malcolm Gladwell (1963-present)
- [ ] Thomas Sowell (1930-present)

### Counterculture Icons (7)
- [ ] Emma Goldman (1869-1940)
- [ ] Timothy Leary (1920-1996)
- [ ] Howard Zinn (1922-2010)
- [ ] Allen Ginsberg (1926-1997)
- [ ] Abbie Hoffman (1936-1989)
- [ ] Hunter S. Thompson (1937-2005)
- [ ] Angela Davis (1944-present)

### Media Critics (7)
- [ ] Walter Lippmann (1889-1974)
- [ ] Marshall McLuhan (1911-1980)
- [ ] Neil Postman (1931-2003)
- [ ] Susan Sontag (1933-2004)
- [ ] Sherry Turkle (1948-present)
- [ ] Douglas Rushkoff (1961-present)
- [ ] Naomi Klein (1970-present)

### African Thinkers (7)
- [ ] Kwame Nkrumah (1909-1972)
- [ ] Julius Nyerere (1922-1999)
- [ ] Cheikh Anta Diop (1923-1986)
- [ ] Wangari Maathai (1940-2011)
- [ ] Steve Biko (1946-1977)
- [ ] Chinua Achebe (1930-2013)
- [ ] Thomas Sankara (1949-1987)

### Latin American Voices (7)
- [ ] José Martí (1853-1895)
- [ ] Octavio Paz (1914-1998)
- [ ] Paulo Freire (1921-1997)
- [ ] Eduardo Galeano (1940-2015)
- [ ] Subcomandante Marcos (1957-present)
- [ ] Gustavo Gutiérrez (1928-present)
- [ ] Silvia Rivera Cusicanqui (1949-present)

### Legal Minds (7)
- [ ] Clarence Darrow (1857-1938)
- [ ] Louis Brandeis (1856-1941)
- [ ] Thurgood Marshall (1908-1993)
- [ ] Ruth Bader Ginsburg (1933-2020)
- [ ] William O. Douglas (1898-1980)
- [ ] Oliver Wendell Holmes Jr. (1841-1935)
- [ ] Derrick Bell (1930-2011)

### Journalists & Truth-Seekers (7)
- [ ] Ida B. Wells (1862-1931)
- [ ] H.L. Mencken (1880-1956)
- [ ] I.F. Stone (1907-1989)
- [ ] Martha Gellhorn (1908-1998)
- [ ] Edward R. Murrow (1908-1965)
- [ ] Seymour Hersh (1937-present)
- [ ] Glenn Greenwald (1967-present)

### Anthropologists & Cultural Observers (7)
- [ ] Franz Boas (1858-1942)
- [ ] Margaret Mead (1901-1978)
- [ ] Claude Lévi-Strauss (1908-2009)
- [ ] Zora Neale Hurston (1891-1960)
- [ ] Clifford Geertz (1926-2006)
- [ ] Mary Douglas (1921-2007)
- [ ] David Graeber (1961-2020)

### Feminist & Gender Theorists (7)
- [ ] Mary Wollstonecraft (1759-1797)
- [ ] Betty Friedan (1921-2006)
- [ ] bell hooks (1952-2021)
- [ ] Judith Butler (1956-present)
- [ ] Audre Lorde (1934-1992)
- [ ] Gloria Steinem (1934-present)
- [ ] Chimamanda Ngozi Adichie (1977-present)

### Queer Theorists (6)
- [ ] Michel Foucault (1926-1984)
- [ ] Eve Kosofsky Sedgwick (1950-2009)
- [ ] José Esteban Muñoz (1967-2013)
- [ ] Jack Halberstam (1961-present)
- [ ] Gayle Rubin (1949-present)
- [ ] Adrienne Rich (1929-2012)

### Islamic Scholars (8)
- [ ] Al-Kindi (801-873)
- [ ] Al-Farabi (872-950)
- [ ] Avicenna / Ibn Sina (980-1037)
- [ ] Averroes / Ibn Rushd (1126-1198)
- [ ] Suhrawardi (1154-1191)
- [ ] Ibn Arabi (1165-1240)
- [ ] Ibn Khaldun (1332-1406)
- [ ] Mulla Sadra (1571-1640)

### Buddhist Masters (8)
- [ ] The Buddha / Siddhartha Gautama (c. 563-483 BCE)
- [ ] Vasubandhu (4th-5th c. CE)
- [ ] Buddhaghosa (5th c. CE)
- [ ] Shantideva (8th c. CE)
- [ ] Bodhidharma (5th-6th c. CE)
- [ ] Padmasambhava (8th c. CE)
- [ ] Tsongkhapa (1357-1419)
- [ ] 14th Dalai Lama / Tenzin Gyatso (1935-present)

### Modern Atheists & Skeptics (8)
- [ ] Baruch Spinoza (1632-1677)
- [ ] Friedrich Nietzsche (1844-1900)
- [ ] Bertrand Russell (1872-1970)
- [ ] Albert Camus (1913-1960)
- [ ] Richard Dawkins (1941-present)
- [ ] Christopher Hitchens (1949-2011)
- [ ] Daniel Dennett (1942-2024)
- [ ] Sam Harris (1967-present)

---

## Primary Text Addition Instructions

When adding primary texts to a persona:

1. Research the persona's most important and representative works
2. Select 3-5 key primary texts that best represent their thought
3. For each text, include:
   - Full title
   - Publication date (if applicable)
   - Brief description of the work's significance
   - Key themes or concepts covered
4. Add the primary texts to the persona's database record
5. Check off `[x]` in this tracker

## Selection Criteria

- **Philosophers**: Major treatises, dialogues, and foundational works
- **Scientists**: Groundbreaking papers, books, and research publications
- **Theologians**: Key theological works, commentaries, and spiritual writings
- **Political Theorists**: Influential political writings and manifestos
- **Psychologists**: Seminal research papers and theoretical works
- **Others**: Most influential and representative works in their field

## Notes

- Prioritize works that are widely considered essential to understanding the thinker
- Include works that demonstrate their unique contributions to their field
- Consider including both early/foundational works and mature/representative works
- For historical figures, include works that had the greatest impact on their legacy

---

## Next Phase: Expand Primary Text Library

### Phase 1 Goals (Target: 50-100 texts total)

**Priority 1: Complete Top-Tier Personas (Free/Starter)**
Focus on adding 1-3 key texts for the most recognizable figures:

1. **Philosophers (High Priority)**
   - [ ] Socrates - Add more Platonic dialogues (Crito, Euthyphro, Phaedrus)
   - [ ] Jean-Paul Sartre - Being and Nothingness, Existentialism is a Humanism
   - [ ] Simone de Beauvoir - The Second Sex
   - [ ] Friedrich Nietzsche - Thus Spoke Zarathustra, Beyond Good and Evil

2. **Scientists (High Priority)**
   - [ ] Albert Einstein - Relativity: The Special and General Theory
   - [ ] Nicolaus Copernicus - On the Revolutions of the Heavenly Spheres
   - [ ] Marie Curie - Scientific papers (check public domain status)

3. **Theologians (High Priority)**
   - [ ] Karl Barth - Church Dogmatics excerpts (check copyright)
   - [ ] Nāgārjuna - Mūlamadhyamakakārikā (Fundamental Verses on the Middle Way)
   - [ ] Plotinus - The Enneads
   - [ ] Rāmānuja - Vedārtha Saṅgraha (check translations)
   - [ ] Adi Śaṅkara - Vivekacūḍāmaṇi (Crest-Jewel of Discrimination)

4. **Additional Key Works for Existing Personas**
   - [ ] Plato - Add Timaeus, Parmenides, Theaetetus
   - [ ] Aristotle - Add On the Soul (De Anima), Posterior Analytics
   - [ ] Kant - Add Critique of Practical Reason, Critique of Judgment

**Priority 2: Literary Voices (High Priority - Many on Gutenberg!)**
   - [ ] Mark Twain - Adventures of Huckleberry Finn, Tom Sawyer, Connecticut Yankee
   - [ ] Dante Alighieri - Divine Comedy (Inferno, Purgatorio, Paradiso)
   - [ ] William Shakespeare - Hamlet, Macbeth, Romeo and Juliet, King Lear
   - [ ] Fyodor Dostoevsky - Crime and Punishment, Brothers Karamazov, Notes from Underground
   - [ ] James Joyce - Ulysses, Dubliners, A Portrait of the Artist
   - [ ] Virginia Woolf - Mrs Dalloway, To the Lighthouse, A Room of One's Own
   - [ ] Jorge Luis Borges - Check Gutenberg availability

**Priority 3: Expand to Other Categories**
   - [ ] Ancient Schools - Epicurus, Epictetus, Marcus Aurelius (Meditations), Diogenes
   - [ ] Eastern Philosophers - More Zhuangzi, Mencius, Xunzi if available
   - [ ] Political Theorists - Machiavelli (The Prince), Hobbes (Leviathan), Locke
   - [ ] Environmental Thinkers - Thoreau (Walden), Aldo Leopold

**Priority 4: Other Public Domain Sources**
- MIT Classics Archive (Greek/Roman philosophy)
- Internet Archive (medieval/modern philosophy)
- Sacred Texts (religious/theological works)
- Wikisource (various public domain works)

**Copyright Strategy: Trust Project Gutenberg**
- ✅ **If it's on Project Gutenberg, it's public domain** - they verify copyright status
- Works can be PD for many reasons (pre-1928, no renewal, author donation, non-US rules)
- For living/recent authors: Only link externally (no ingestion)

### Text Ingestion Workflow

**Step 1: Search Project Gutenberg by Author**

Visit: `https://www.gutenberg.org/ebooks/search/?query=AUTHOR_NAME`

Example searches:
- Mark Twain: https://www.gutenberg.org/ebooks/search/?query=mark+twain
- Nietzsche: https://www.gutenberg.org/ebooks/search/?query=nietzsche
- Virginia Woolf: https://www.gutenberg.org/ebooks/search/?query=virginia+woolf

**Step 2: Identify Works and Extract Ebook IDs**

From search results, click on a work to get its ebook page.
URL format: `https://www.gutenberg.org/ebooks/{ID}`

Examples:
- Huckleberry Finn: https://www.gutenberg.org/ebooks/76 → **ID: 76**
- Thus Spoke Zarathustra: https://www.gutenberg.org/ebooks/1998 → **ID: 1998**
- Mrs Dalloway: https://www.gutenberg.org/ebooks/30220 → **ID: 30220**

**Step 3: Construct URLs and Ingest**

Use the clean `/ebooks/{ID}` format (NOT the .txt files):
```bash
cd backend

# Single text ingestion
venv/bin/python manage.py ingest_text \
  --url "https://www.gutenberg.org/ebooks/76" \
  --title "Adventures of Huckleberry Finn" \
  --author "Mark Twain" \
  --category philosophy \
  --era modern \
  --translator "" \
  --source-type gutenberg

# For translations, include translator name
venv/bin/python manage.py ingest_text \
  --url "https://www.gutenberg.org/ebooks/1998" \
  --title "Thus Spoke Zarathustra" \
  --author "Friedrich Nietzsche" \
  --category philosophy \
  --era modern \
  --translator "Thomas Common" \
  --source-type gutenberg
```

**Step 4: Batch Ingestion Strategy**

For authors with multiple works, create a batch script:
```bash
# Example: Ingest all Plato dialogues
venv/bin/python manage.py ingest_text --url "https://www.gutenberg.org/ebooks/1656" --title "Apology" --author "Plato" --category philosophy --era ancient --translator "Benjamin Jowett" --source-type gutenberg
venv/bin/python manage.py ingest_text --url "https://www.gutenberg.org/ebooks/1750" --title "Crito" --author "Plato" --category philosophy --era ancient --translator "Benjamin Jowett" --source-type gutenberg
venv/bin/python manage.py ingest_text --url "https://www.gutenberg.org/ebooks/1572" --title "Euthyphro" --author "Plato" --category philosophy --era ancient --translator "Benjamin Jowett" --source-type gutenberg
```

**Step 5: Quality Check**
- ✅ Verify sections parsed correctly in Django admin
- ✅ Check word count is reasonable (typically 10k-200k words)
- ✅ Test reading view in frontend: http://localhost:3001/texts/[slug]
- ✅ Validate citation extraction automatically ran
- ✅ Check for any parsing errors in console output

**Common Issues & Solutions:**
- **Empty content:** URL might be landing page instead of text file - Gutenberg will auto-redirect
- **Poor parsing:** Try different source-type or manually adjust parser
- **Missing translator:** Check Gutenberg page for translator info in metadata

### Success Metrics

- **Target 1:** 50 total texts - **✅ ACHIEVED! (50/50)**
- **Target 2:** 100 total texts - **✅ ACHIEVED! (100/100)**
- **Coverage:** At least 1 text for each Free tier persona (30 total) - **✅ EXCEEDED: 60/30 (200%!)**
- **Quality:** All texts properly parsed with correct metadata - **✅ 100% success rate**
- **Usability:** All texts readable in frontend library viewer - **✅ Working**

### Current Status
- 🎊 **100 texts ingested** (60 personas with primary texts)
- ✅ Citation extraction working (automatic on message save)
- ✅ REST API functional (`/api/texts/`)
- ✅ Frontend library viewer operational with dual reading modes
- ✅ Citation validation (97.8% valid, 0 broken links)
- ✅ Ingestion command updated to handle clean Gutenberg URLs
- 🎯 **Next:** Target 3 (optional) - Expand to 150-200 texts, or focus on quality improvements

### Quick Reference: Project Gutenberg Search Links

**Philosophers:**
- [Socrates/Plato works](https://www.gutenberg.org/ebooks/search/?query=plato)
- [Aristotle](https://www.gutenberg.org/ebooks/search/?query=aristotle)
- [Nietzsche](https://www.gutenberg.org/ebooks/search/?query=nietzsche)
- [Kant](https://www.gutenberg.org/ebooks/search/?query=kant)
- [Descartes](https://www.gutenberg.org/ebooks/search/?query=descartes)
- [Spinoza](https://www.gutenberg.org/ebooks/search/?query=spinoza)

**Literary Voices:**
- [Mark Twain](https://www.gutenberg.org/ebooks/search/?query=mark+twain)
- [Shakespeare](https://www.gutenberg.org/ebooks/search/?query=shakespeare)
- [Dante](https://www.gutenberg.org/ebooks/search/?query=dante)
- [Dostoevsky](https://www.gutenberg.org/ebooks/search/?query=dostoevsky)
- [Virginia Woolf](https://www.gutenberg.org/ebooks/search/?query=virginia+woolf)
- [James Joyce](https://www.gutenberg.org/ebooks/search/?query=james+joyce)

**Political/Social:**
- [Machiavelli](https://www.gutenberg.org/ebooks/search/?query=machiavelli)
- [Thomas Hobbes](https://www.gutenberg.org/ebooks/search/?query=hobbes)
- [John Locke](https://www.gutenberg.org/ebooks/search/?query=john+locke)
- [Thoreau](https://www.gutenberg.org/ebooks/search/?query=thoreau)
- [Mary Wollstonecraft](https://www.gutenberg.org/ebooks/search/?query=wollstonecraft)

**Ancient/Classical:**
- [Marcus Aurelius](https://www.gutenberg.org/ebooks/search/?query=marcus+aurelius)
- [Epictetus](https://www.gutenberg.org/ebooks/search/?query=epictetus)
- [Epicurus](https://www.gutenberg.org/ebooks/search/?query=epicurus)
- [Confucius](https://www.gutenberg.org/ebooks/search/?query=confucius)
