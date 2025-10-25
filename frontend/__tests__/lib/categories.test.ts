import { describe, it, expect } from 'vitest'
import {
  CATEGORY_INFO,
  getCategoryInfo,
  sortPersonasByTime,
  ERA_INFO,
  getPersonaEra,
  type Era,
} from '@/lib/categories'

describe('categories utilities', () => {
  describe('CATEGORY_INFO', () => {
    it('contains all expected categories', () => {
      expect(CATEGORY_INFO).toHaveProperty('theologians')
      expect(CATEGORY_INFO).toHaveProperty('philosophers')
      expect(CATEGORY_INFO).toHaveProperty('scientists')
      expect(CATEGORY_INFO).toHaveProperty('ancient_schools')
      expect(CATEGORY_INFO).toHaveProperty('eastern_philosophers')
      expect(CATEGORY_INFO).toHaveProperty('mystics')
      expect(CATEGORY_INFO).toHaveProperty('artists')
      expect(CATEGORY_INFO).toHaveProperty('political_theorists')
      expect(CATEGORY_INFO).toHaveProperty('social_reformers')
      expect(CATEGORY_INFO).toHaveProperty('economists')
      expect(CATEGORY_INFO).toHaveProperty('psychologists')
      expect(CATEGORY_INFO).toHaveProperty('environmental_thinkers')
    })

    it('has correct structure for each category', () => {
      Object.values(CATEGORY_INFO).forEach((category) => {
        expect(category).toHaveProperty('title')
        expect(category).toHaveProperty('description')
        expect(category).toHaveProperty('color')
        expect(typeof category.title).toBe('string')
        expect(typeof category.description).toBe('string')
        expect(typeof category.color).toBe('string')
      })
    })

    it('has gradient colors for all categories', () => {
      Object.values(CATEGORY_INFO).forEach((category) => {
        expect(category.color).toMatch(/linear-gradient/)
      })
    })
  })

  describe('getCategoryInfo', () => {
    it('returns existing category info', () => {
      const info = getCategoryInfo('philosophers')
      expect(info.title).toBe('Philosophers')
      expect(info.description).toBe('Secular philosophers and thinkers')
      expect(info.color).toMatch(/linear-gradient/)
    })

    it('returns theologians info correctly', () => {
      const info = getCategoryInfo('theologians')
      expect(info.title).toBe('Theologians')
      expect(info.description).toBe('Religious thinkers and theologians')
    })

    it('returns scientists info correctly', () => {
      const info = getCategoryInfo('scientists')
      expect(info.title).toBe('Scientists')
      expect(info.description).toBe('Scientific figures and researchers')
    })

    it('generates fallback for unknown category with underscores', () => {
      const info = getCategoryInfo('unknown_category')
      expect(info.title).toBe('Unknown category')
      expect(info.description).toBe('Thinkers in unknown category')
      expect(info.color).toMatch(/linear-gradient/)
    })

    it('generates fallback for unknown category without underscores', () => {
      const info = getCategoryInfo('mystery')
      expect(info.title).toBe('Mystery')
      expect(info.description).toBe('Thinkers in mystery')
    })

    it('capitalizes first letter in fallback title', () => {
      const info = getCategoryInfo('test')
      expect(info.title).toBe('Test')
    })

    it('replaces underscores with spaces in fallback', () => {
      const info = getCategoryInfo('some_long_category_name')
      expect(info.title).toBe('Some long category name')
      expect(info.description).toBe('Thinkers in some long category name')
    })
  })

  describe('sortPersonasByTime', () => {
    it('sorts by birth year ascending (earliest first)', () => {
      const personas = [
        { name: 'Modern', birth_year: 1900 },
        { name: 'Ancient', birth_year: -400 },
        { name: 'Medieval', birth_year: 1200 },
      ]

      const sorted = sortPersonasByTime(personas)

      expect(sorted[0].name).toBe('Ancient')
      expect(sorted[1].name).toBe('Medieval')
      expect(sorted[2].name).toBe('Modern')
    })

    it('handles negative birth years correctly', () => {
      const personas = [
        { name: 'Plato', birth_year: -427 },
        { name: 'Socrates', birth_year: -470 },
        { name: 'Aristotle', birth_year: -384 },
      ]

      const sorted = sortPersonasByTime(personas)

      expect(sorted[0].name).toBe('Socrates') // -470
      expect(sorted[1].name).toBe('Plato') // -427
      expect(sorted[2].name).toBe('Aristotle') // -384
    })

    it('sorts alphabetically when birth years are equal', () => {
      const personas = [
        { name: 'Zeno', birth_year: 1900 },
        { name: 'Alice', birth_year: 1900 },
        { name: 'Bob', birth_year: 1900 },
      ]

      const sorted = sortPersonasByTime(personas)

      expect(sorted[0].name).toBe('Alice')
      expect(sorted[1].name).toBe('Bob')
      expect(sorted[2].name).toBe('Zeno')
    })

    it('places personas with birth years before those without', () => {
      const personas = [
        { name: 'Unknown', birth_year: null },
        { name: 'Ancient', birth_year: -400 },
        { name: 'Mystery', birth_year: undefined },
      ]

      const sorted = sortPersonasByTime(personas)

      expect(sorted[0].name).toBe('Ancient')
      // Unknown and Mystery should be after Ancient
      expect(['Unknown', 'Mystery']).toContain(sorted[1].name)
      expect(['Unknown', 'Mystery']).toContain(sorted[2].name)
    })

    it('sorts personas without birth years alphabetically', () => {
      const personas = [
        { name: 'Zara', birth_year: null },
        { name: 'Alice', birth_year: null },
        { name: 'Bob', birth_year: null },
      ]

      const sorted = sortPersonasByTime(personas)

      expect(sorted[0].name).toBe('Alice')
      expect(sorted[1].name).toBe('Bob')
      expect(sorted[2].name).toBe('Zara')
    })

    it('does not mutate original array', () => {
      const personas = [
        { name: 'B', birth_year: 1900 },
        { name: 'A', birth_year: 1800 },
      ]
      const original = [...personas]

      sortPersonasByTime(personas)

      expect(personas).toEqual(original)
    })

    it('handles empty array', () => {
      const sorted = sortPersonasByTime([])
      expect(sorted).toEqual([])
    })

    it('handles single persona', () => {
      const personas = [{ name: 'Solo', birth_year: 1900 }]
      const sorted = sortPersonasByTime(personas)
      expect(sorted).toEqual(personas)
    })
  })

  describe('ERA_INFO', () => {
    it('contains all expected eras', () => {
      const expectedEras: Era[] = ['ancient', 'medieval', 'early_modern', 'modern', 'contemporary']

      expectedEras.forEach((era) => {
        expect(ERA_INFO).toHaveProperty(era)
      })
    })

    it('has correct structure for each era', () => {
      Object.values(ERA_INFO).forEach((era) => {
        expect(era).toHaveProperty('label')
        expect(era).toHaveProperty('description')
        expect(era).toHaveProperty('range')
        expect(typeof era.label).toBe('string')
        expect(typeof era.description).toBe('string')
        expect(typeof era.range).toBe('string')
      })
    })

    it('has correct labels', () => {
      expect(ERA_INFO.ancient.label).toBe('Ancient')
      expect(ERA_INFO.medieval.label).toBe('Medieval')
      expect(ERA_INFO.early_modern.label).toBe('Early Modern')
      expect(ERA_INFO.modern.label).toBe('Modern')
      expect(ERA_INFO.contemporary.label).toBe('Contemporary')
    })
  })

  describe('getPersonaEra', () => {
    it('classifies ancient era (before 500)', () => {
      expect(getPersonaEra(-470)).toBe('ancient') // Socrates
      expect(getPersonaEra(100)).toBe('ancient')
      expect(getPersonaEra(499)).toBe('ancient')
    })

    it('classifies medieval era (500-1499)', () => {
      expect(getPersonaEra(500)).toBe('medieval')
      expect(getPersonaEra(1200)).toBe('medieval') // Aquinas
      expect(getPersonaEra(1499)).toBe('medieval')
    })

    it('classifies early modern era (1500-1799)', () => {
      expect(getPersonaEra(1500)).toBe('early_modern')
      expect(getPersonaEra(1650)).toBe('early_modern') // Descartes
      expect(getPersonaEra(1799)).toBe('early_modern')
    })

    it('classifies modern era (1800-1949)', () => {
      expect(getPersonaEra(1800)).toBe('modern')
      expect(getPersonaEra(1850)).toBe('modern') // Nietzsche
      expect(getPersonaEra(1949)).toBe('modern')
    })

    it('classifies contemporary era (1950+)', () => {
      expect(getPersonaEra(1950)).toBe('contemporary')
      expect(getPersonaEra(2000)).toBe('contemporary')
      expect(getPersonaEra(2024)).toBe('contemporary')
    })

    it('returns null for null birth year', () => {
      expect(getPersonaEra(null)).toBeNull()
    })

    it('returns null for undefined birth year', () => {
      expect(getPersonaEra(undefined)).toBeNull()
    })

    it('handles boundary years correctly', () => {
      expect(getPersonaEra(499)).toBe('ancient')
      expect(getPersonaEra(500)).toBe('medieval')
      expect(getPersonaEra(1499)).toBe('medieval')
      expect(getPersonaEra(1500)).toBe('early_modern')
      expect(getPersonaEra(1799)).toBe('early_modern')
      expect(getPersonaEra(1800)).toBe('modern')
      expect(getPersonaEra(1949)).toBe('modern')
      expect(getPersonaEra(1950)).toBe('contemporary')
    })
  })
})
