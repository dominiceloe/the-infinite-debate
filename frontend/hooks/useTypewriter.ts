import { useState, useEffect, useRef } from 'react';

interface UseTypewriterOptions {
  text: string;
  speed?: number; // words per minute
  onComplete?: () => void;
  enabled?: boolean; // whether typing should be active
}

interface UseTypewriterReturn {
  displayedText: string;
  isTyping: boolean;
  reset: () => void;
}

/**
 * Custom hook for typewriter effect that displays text word-by-word
 * at a readable pace (~150 words/minute by default).
 *
 * @param text - The full text to display
 * @param speed - Words per minute (default: 150)
 * @param onComplete - Callback when typing completes
 * @param enabled - Whether typing should be active (default: true)
 */
export function useTypewriter({
  text,
  speed = 150,
  onComplete,
  enabled = true,
}: UseTypewriterOptions): UseTypewriterReturn {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const wordsRef = useRef<string[]>([]);
  const currentIndexRef = useRef(0);

  // Reset function
  const reset = () => {
    setDisplayedText('');
    setIsTyping(false);
    currentIndexRef.current = 0;
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  // Store onComplete callback in ref to avoid re-running effect when it changes
  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    if (!enabled || !text) {
      reset();
      return;
    }

    // Split text into words
    wordsRef.current = text.split(/\s+/);
    currentIndexRef.current = 0;
    setDisplayedText('');
    setIsTyping(true);

    // Calculate delay between words (milliseconds)
    const delayMs = (60 / speed) * 1000;

    const typeNextWord = () => {
      if (currentIndexRef.current < wordsRef.current.length) {
        const words = wordsRef.current.slice(0, currentIndexRef.current + 1);
        setDisplayedText(words.join(' '));
        currentIndexRef.current++;

        timeoutRef.current = setTimeout(typeNextWord, delayMs);
      } else {
        // Typing complete
        setIsTyping(false);
        if (onCompleteRef.current) {
          onCompleteRef.current();
        }
      }
    };

    // Start typing
    timeoutRef.current = setTimeout(typeNextWord, delayMs);

    // Cleanup on unmount or when dependencies change
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [text, speed, enabled]); // Remove onComplete from dependencies

  return { displayedText, isTyping, reset };
}
