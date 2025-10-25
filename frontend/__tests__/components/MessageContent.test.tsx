import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MessageContent from '@/components/MessageContent'
import type { TextCitation } from '@/types'

describe('MessageContent', () => {
  it('renders plain content when no citations provided', () => {
    const content = 'This is a test message with no citations.'
    render(<MessageContent content={content} />)

    expect(screen.getByText(content)).toBeInTheDocument()
  })

  it('renders plain content when citations array is empty', () => {
    const content = 'This is a test message with no citations.'
    render(<MessageContent content={content} citations={[]} />)

    expect(screen.getByText(content)).toBeInTheDocument()
  })

  it('renders citation as a link when citation is found in content', () => {
    const citations: TextCitation[] = [
      {
        id: 1,
        text_id: 1,
        text_title: 'The Republic',
        text_slug: 'the-republic',
      },
    ]
    const content = 'In The Republic, Plato discusses justice.'

    render(<MessageContent content={content} citations={citations} />)

    const link = screen.getByRole('link', { name: 'The Republic' })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/texts/the-republic')
    expect(screen.getByText(/In/)).toBeInTheDocument()
    expect(screen.getByText(/, Plato discusses justice\./)).toBeInTheDocument()
  })

  it('renders multiple different citations', () => {
    const citations: TextCitation[] = [
      {
        id: 1,
        text_id: 1,
        text_title: 'The Republic',
        text_slug: 'the-republic',
      },
      {
        id: 2,
        text_id: 2,
        text_title: 'Nicomachean Ethics',
        text_slug: 'nicomachean-ethics',
      },
    ]
    const content = 'In The Republic and Nicomachean Ethics, they discuss virtue.'

    render(<MessageContent content={content} citations={citations} />)

    const republicLink = screen.getByRole('link', { name: 'The Republic' })
    const ethicsLink = screen.getByRole('link', { name: 'Nicomachean Ethics' })

    expect(republicLink).toHaveAttribute('href', '/texts/the-republic')
    expect(ethicsLink).toHaveAttribute('href', '/texts/nicomachean-ethics')
  })

  it('handles multiple occurrences of the same citation', () => {
    const citations: TextCitation[] = [
      {
        id: 1,
        text_id: 1,
        text_title: 'Ethics',
        text_slug: 'ethics',
      },
    ]
    const content = 'In Ethics, Spinoza discusses Ethics of reason.'

    render(<MessageContent content={content} citations={citations} />)

    const links = screen.getAllByRole('link', { name: 'Ethics' })
    expect(links).toHaveLength(2)
    links.forEach((link) => {
      expect(link).toHaveAttribute('href', '/texts/ethics')
    })
  })

  it('returns plain content when citation title is not found in content', () => {
    const citations: TextCitation[] = [
      {
        id: 1,
        text_id: 1,
        text_title: 'The Republic',
        text_slug: 'the-republic',
      },
    ]
    const content = 'This message does not mention any works.'

    render(<MessageContent content={content} citations={citations} />)

    expect(screen.getByText(content)).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('handles overlapping citation matches correctly', () => {
    const citations: TextCitation[] = [
      {
        id: 1,
        text_id: 1,
        text_title: 'Ethics',
        text_slug: 'ethics',
      },
      {
        id: 2,
        text_id: 2,
        text_title: 'Nicomachean Ethics',
        text_slug: 'nicomachean-ethics',
      },
    ]
    const content = 'In Nicomachean Ethics, Aristotle discusses virtue.'

    render(<MessageContent content={content} citations={citations} />)

    // Should only render the first match (Nicomachean Ethics), not the overlapping "Ethics"
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(1)
    expect(links[0]).toHaveTextContent('Nicomachean Ethics')
    expect(links[0]).toHaveAttribute('href', '/texts/nicomachean-ethics')
  })
})
