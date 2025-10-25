import { describe, it, expect } from 'vitest'
import { theme } from '@/lib/theme'

describe('theme configuration', () => {
  it('exports a valid MUI theme object', () => {
    expect(theme).toBeDefined()
    expect(theme).toHaveProperty('palette')
    expect(theme).toHaveProperty('typography')
    expect(theme).toHaveProperty('shape')
    expect(theme).toHaveProperty('components')
  })

  describe('palette', () => {
    it('has light mode configured', () => {
      expect(theme.palette.mode).toBe('light')
    })

    it('has primary colors defined', () => {
      expect(theme.palette.primary).toBeDefined()
      expect(theme.palette.primary.main).toBe('#4f46e5') // indigo-600
      expect(theme.palette.primary.light).toBe('#6366f1')
      expect(theme.palette.primary.dark).toBe('#4338ca')
    })

    it('has secondary colors defined', () => {
      expect(theme.palette.secondary).toBeDefined()
      expect(theme.palette.secondary.main).toBe('#9333ea') // purple-600
      expect(theme.palette.secondary.light).toBe('#a855f7')
      expect(theme.palette.secondary.dark).toBe('#7e22ce')
    })

    it('has error color defined', () => {
      expect(theme.palette.error?.main).toBe('#dc2626')
    })

    it('has success color defined', () => {
      expect(theme.palette.success?.main).toBe('#16a34a')
    })

    it('has background colors defined', () => {
      expect(theme.palette.background).toBeDefined()
      expect(theme.palette.background.default).toBe('#f9fafb')
      expect(theme.palette.background.paper).toBe('#ffffff')
    })

    it('has text colors defined', () => {
      expect(theme.palette.text).toBeDefined()
      expect(theme.palette.text.primary).toBe('#111827')
      expect(theme.palette.text.secondary).toBe('#6b7280')
    })
  })

  describe('typography', () => {
    it('has font family configured', () => {
      expect(theme.typography.fontFamily).toContain('var(--font-geist-sans)')
    })

    it('has heading styles defined', () => {
      expect(theme.typography.h1).toBeDefined()
      expect(theme.typography.h1?.fontWeight).toBe(700)
      expect(theme.typography.h1?.fontSize).toBe('2.25rem')

      expect(theme.typography.h2).toBeDefined()
      expect(theme.typography.h2?.fontWeight).toBe(700)

      expect(theme.typography.h3).toBeDefined()
      expect(theme.typography.h3?.fontWeight).toBe(600)
    })

    it('has body styles defined', () => {
      expect(theme.typography.body1).toBeDefined()
      expect(theme.typography.body1?.fontSize).toBe('1rem')

      expect(theme.typography.body2).toBeDefined()
      expect(theme.typography.body2?.fontSize).toBe('0.875rem')
    })
  })

  describe('shape', () => {
    it('has border radius configured', () => {
      expect(theme.shape.borderRadius).toBe(8)
    })
  })

  describe('component overrides', () => {
    it('has Button overrides', () => {
      expect(theme.components?.MuiButton).toBeDefined()
      expect(theme.components?.MuiButton?.styleOverrides).toBeDefined()
    })

    it('configures buttons with no text transform', () => {
      const buttonRoot = theme.components?.MuiButton?.styleOverrides?.root
      expect(buttonRoot).toHaveProperty('textTransform', 'none')
    })

    it('has Card overrides', () => {
      expect(theme.components?.MuiCard).toBeDefined()
      expect(theme.components?.MuiCard?.styleOverrides).toBeDefined()
    })

    it('has TextField overrides', () => {
      expect(theme.components?.MuiTextField).toBeDefined()
      expect(theme.components?.MuiTextField?.styleOverrides).toBeDefined()
    })

    it('has Chip overrides', () => {
      expect(theme.components?.MuiChip).toBeDefined()
      expect(theme.components?.MuiChip?.styleOverrides).toBeDefined()
    })

    it('has AppBar overrides', () => {
      expect(theme.components?.MuiAppBar).toBeDefined()
      expect(theme.components?.MuiAppBar?.styleOverrides).toBeDefined()
    })
  })

  describe('theme consistency', () => {
    it('uses consistent indigo/purple color scheme', () => {
      expect(theme.palette.primary.main).toMatch(/#[0-9a-f]{6}/)
      expect(theme.palette.secondary.main).toMatch(/#[0-9a-f]{6}/)
    })

    it('has consistent border radius across components', () => {
      expect(theme.shape.borderRadius).toBe(8)
      const buttonRoot = theme.components?.MuiButton?.styleOverrides?.root
      expect(buttonRoot).toHaveProperty('borderRadius', 8)
    })
  })
})
