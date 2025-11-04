import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTypewriter } from '@/hooks/useTypewriter'

describe('useTypewriter', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('initializes with empty text and not typing', () => {
    const { result } = renderHook(() =>
      useTypewriter({ text: 'Hello world', enabled: false })
    )

    expect(result.current.displayedText).toBe('')
    expect(result.current.isTyping).toBe(false)
  })

  it('types out text word by word', async () => {
    const { result } = renderHook(() =>
      useTypewriter({ text: 'Hello world test', speed: 150 })
    )

    // Initially should be typing but no text yet
    expect(result.current.isTyping).toBe(true)
    expect(result.current.displayedText).toBe('')

    // Speed is 150 words/minute = 400ms per word
    // First word after 400ms
    await act(async () => {
      vi.advanceTimersByTime(400)
    })
    expect(result.current.displayedText).toBe('Hello')
    expect(result.current.isTyping).toBe(true)

    // Second word after another 400ms
    await act(async () => {
      vi.advanceTimersByTime(400)
    })
    expect(result.current.displayedText).toBe('Hello world')
    expect(result.current.isTyping).toBe(true)

    // Third word after another 400ms
    await act(async () => {
      vi.advanceTimersByTime(400)
    })
    expect(result.current.displayedText).toBe('Hello world test')
    expect(result.current.isTyping).toBe(true)

    // One more timer advance to trigger completion
    await act(async () => {
      vi.advanceTimersByTime(400)
    })
    expect(result.current.isTyping).toBe(false)
  })

  it('calls onComplete when typing finishes', async () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() =>
      useTypewriter({ text: 'Hello world', speed: 150, onComplete })
    )

    expect(onComplete).not.toHaveBeenCalled()

    // Wait for all words to type (2 words * 400ms = 800ms) plus one more to trigger completion
    await act(async () => {
      vi.advanceTimersByTime(1200)
    })

    expect(result.current.displayedText).toBe('Hello world')
    expect(result.current.isTyping).toBe(false)
    expect(onComplete).toHaveBeenCalledTimes(1)
  })

  it('respects custom speed setting', async () => {
    const { result } = renderHook(() =>
      useTypewriter({ text: 'Hello world', speed: 300 })
    )

    // Speed is 300 words/minute = 200ms per word
    await act(async () => {
      vi.advanceTimersByTime(200)
    })
    expect(result.current.displayedText).toBe('Hello')

    await act(async () => {
      vi.advanceTimersByTime(200)
    })
    expect(result.current.displayedText).toBe('Hello world')
  })

  it('does not type when enabled is false', async () => {
    const { result } = renderHook(() =>
      useTypewriter({ text: 'Hello world', enabled: false })
    )

    expect(result.current.isTyping).toBe(false)
    expect(result.current.displayedText).toBe('')

    // Advance time
    await act(async () => {
      vi.advanceTimersByTime(1000)
    })

    // Should still be empty
    expect(result.current.isTyping).toBe(false)
    expect(result.current.displayedText).toBe('')
  })

  it('resets when enabled changes from true to false', async () => {
    const { result, rerender } = renderHook(
      ({ enabled }) => useTypewriter({ text: 'Hello world', speed: 150, enabled }),
      { initialProps: { enabled: true } }
    )

    // Start typing
    await act(async () => {
      vi.advanceTimersByTime(400)
    })
    expect(result.current.displayedText).toBe('Hello')
    expect(result.current.isTyping).toBe(true)

    // Disable
    rerender({ enabled: false })

    // Should reset
    expect(result.current.displayedText).toBe('')
    expect(result.current.isTyping).toBe(false)
  })

  it('restarts when text changes', async () => {
    const { result, rerender } = renderHook(
      ({ text }) => useTypewriter({ text, speed: 150 }),
      { initialProps: { text: 'Hello world' } }
    )

    // Type first word
    await act(async () => {
      vi.advanceTimersByTime(400)
    })
    expect(result.current.displayedText).toBe('Hello')

    // Change text
    rerender({ text: 'Goodbye world' })

    // Should restart from beginning
    await act(async () => {
      vi.advanceTimersByTime(400)
    })
    expect(result.current.displayedText).toBe('Goodbye')
  })

  it('handles empty text gracefully', () => {
    const { result } = renderHook(() => useTypewriter({ text: '' }))

    expect(result.current.displayedText).toBe('')
    expect(result.current.isTyping).toBe(false)
  })

  it('handles single word text', async () => {
    const { result } = renderHook(() => useTypewriter({ text: 'Hello', speed: 150 }))

    // Advance for the word plus one more to trigger completion
    await act(async () => {
      vi.advanceTimersByTime(800)
    })

    expect(result.current.displayedText).toBe('Hello')
    expect(result.current.isTyping).toBe(false)
  })

  it('handles text with multiple spaces', async () => {
    const { result } = renderHook(() =>
      useTypewriter({ text: 'Hello   world', speed: 150 })
    )

    await act(async () => {
      vi.advanceTimersByTime(400)
    })
    expect(result.current.displayedText).toBe('Hello')

    await act(async () => {
      vi.advanceTimersByTime(400)
    })
    expect(result.current.displayedText).toBe('Hello world')
  })

  it('reset function clears displayed text and stops typing', async () => {
    const { result } = renderHook(() =>
      useTypewriter({ text: 'Hello world test', speed: 150 })
    )

    // Type some words
    await act(async () => {
      vi.advanceTimersByTime(800)
    })
    expect(result.current.displayedText).toBe('Hello world')
    expect(result.current.isTyping).toBe(true)

    // Call reset
    act(() => {
      result.current.reset()
    })

    expect(result.current.displayedText).toBe('')
    expect(result.current.isTyping).toBe(false)

    // Advance time to ensure typing doesn't continue
    await act(async () => {
      vi.advanceTimersByTime(1000)
    })
    expect(result.current.displayedText).toBe('')
  })

  it('cleans up timeout on unmount', async () => {
    const { result, unmount } = renderHook(() =>
      useTypewriter({ text: 'Hello world', speed: 150 })
    )

    // Start typing
    await act(async () => {
      vi.advanceTimersByTime(400)
    })
    expect(result.current.displayedText).toBe('Hello')

    // Unmount while still typing
    unmount()

    // No errors should occur and timers should be cleaned up
    expect(vi.getTimerCount()).toBe(0)
  })

  it('updates onComplete callback without restarting typing', async () => {
    const onComplete1 = vi.fn()
    const onComplete2 = vi.fn()

    const { rerender } = renderHook(
      ({ onComplete }) => useTypewriter({ text: 'Hello', speed: 150, onComplete }),
      { initialProps: { onComplete: onComplete1 } }
    )

    // Change onComplete callback before typing finishes
    rerender({ onComplete: onComplete2 })

    // Complete typing (word + completion check)
    await act(async () => {
      vi.advanceTimersByTime(800)
    })

    // Should call the new callback, not the old one
    expect(onComplete1).not.toHaveBeenCalled()
    expect(onComplete2).toHaveBeenCalledTimes(1)
  })

  it('maintains typing speed with fast speed setting', async () => {
    const { result } = renderHook(() =>
      useTypewriter({ text: 'Hello world', speed: 600 })
    )

    // Speed is 600 words/minute = 100ms per word
    await act(async () => {
      vi.advanceTimersByTime(100)
    })
    expect(result.current.displayedText).toBe('Hello')

    await act(async () => {
      vi.advanceTimersByTime(100)
    })
    expect(result.current.displayedText).toBe('Hello world')

    // One more to trigger completion
    await act(async () => {
      vi.advanceTimersByTime(100)
    })
    expect(result.current.isTyping).toBe(false)
  })

  it('maintains typing speed with slow speed setting', async () => {
    const { result } = renderHook(() =>
      useTypewriter({ text: 'Hello world', speed: 60 })
    )

    // Speed is 60 words/minute = 1000ms per word
    await act(async () => {
      vi.advanceTimersByTime(1000)
    })
    expect(result.current.displayedText).toBe('Hello')

    await act(async () => {
      vi.advanceTimersByTime(1000)
    })
    expect(result.current.displayedText).toBe('Hello world')

    // One more to trigger completion
    await act(async () => {
      vi.advanceTimersByTime(1000)
    })
    expect(result.current.isTyping).toBe(false)
  })
})
