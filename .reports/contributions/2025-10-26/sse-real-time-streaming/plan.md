# Implementation Plan: Fix SSE Real-Time Message Streaming

**Date:** 2025-10-26
**Type:** bug fix
**Scope:** frontend/lib/hooks/useDebateSSE.ts
**Author:** Claude Code (Contribution Planner Agent)

---

## 1. Problem Analysis

### Current Behavior
- SSE connection establishes successfully (200 OK, `text/event-stream`)
- Browser DevTools EventStream tab shows `message` events arriving with full content
- Frontend receives both `status` and `message` events
- Theater mode shows "Generating... Round X of Y" throughout entire generation
- Messages only appear in UI **after debate completes**
- No real-time message display during generation

### User Experience Impact
- Users cannot see philosophical dialogue as it's generated
- Theater mode's typewriter animation is useless (no messages to animate)
- Appears as if nothing is happening except round counter incrementing
- Defeats the purpose of SSE streaming and theater mode visualization

---

## 2. Root Cause

**File:** `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/frontend/lib/hooks/useDebateSSE.ts`
**Lines:** 92-95

```typescript
} else if (message.type === 'message') {
  // Trigger refetch to get new message with full data
  queryClient.invalidateQueries({ queryKey: ['debate', slug] });
}
```

### The Bug
When a `message` SSE event arrives, the code calls `invalidateQueries()` which:
1. Marks the `['debate', slug]` query as stale
2. **Triggers a full HTTP refetch** of the entire debate
3. Fetches the updated debate with new messages from backend
4. Replaces the cache **only after HTTP request completes**

### Why This Fails
- HTTP refetch adds ~200-500ms latency per message
- Creates race conditions during rapid message generation
- React Query might batch/debounce invalidations
- Messages don't appear until network roundtrip completes
- User sees stale data until refetch succeeds

### Correct Approach
Use `setQueryData()` to **directly update the React Query cache** by:
1. Reading current cached debate data
2. Appending the new message to `debate.messages[]` array
3. Updating cache immediately (0ms latency)
4. Triggering React re-render with updated data
5. No network request needed

---

## 3. Proposed Solution

### Strategy
Replace the 3-line `invalidateQueries()` call with direct cache mutation using `queryClient.setQueryData()`.

### Implementation Location
**File:** `frontend/lib/hooks/useDebateSSE.ts`
**Lines to Replace:** 92-95
**New Code:** ~25 lines (with null checks, deduplication, ordering)

### Cache Update Logic
```typescript
} else if (message.type === 'message') {
  // Directly update React Query cache instead of refetching
  queryClient.setQueryData(['debate', slug], (old: Debate | undefined) => {
    if (!old) return old; // Cache not yet initialized

    // Extract message data from SSE event
    const newMessage: DebateMessage = {
      id: message.message_id!,
      persona: {
        // Find matching persona from participants
        // or create minimal persona object from SSE data
      },
      round_number: message.round_number!,
      content: message.content!,
      text_citations: [],
      created_at: new Date().toISOString(),
    };

    // Check for duplicates (message might already exist from refetch)
    const existingMessages = old.messages || [];
    const isDuplicate = existingMessages.some(m => m.id === newMessage.id);
    if (isDuplicate) return old;

    // Append new message maintaining chronological order
    const updatedMessages = [...existingMessages, newMessage];

    return {
      ...old,
      messages: updatedMessages,
      rounds_completed: message.round_number!, // Update round counter
    };
  });
}
```

### Persona Lookup Strategy
SSE message events include:
- `persona_slug`: String identifier
- `persona_name`: Display name

Options for populating `message.persona`:
1. **Lookup from participants** - Search `debate.participants[]` for matching slug
2. **Minimal object** - Create partial Persona with just slug/name if not found
3. **Hybrid** - Try lookup first, fallback to minimal object

**Recommended:** Option 3 (hybrid) for robustness.

---

## 4. Files to Modify

### Primary File
- **Path:** `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/frontend/lib/hooks/useDebateSSE.ts`
- **Lines:** 92-95
- **Changes:** Replace `invalidateQueries()` with `setQueryData()` cache update logic
- **Additions:** ~22 lines (net +19 lines)

### Type Imports (if needed)
- **Path:** Same file (line 3)
- **Current:** `import type { Debate } from '@/types';`
- **Add:** `import type { Debate, DebateMessage, Persona } from '@/types';`

---

## 5. Implementation Steps

### Step 1: Update Type Imports
```typescript
import type { Debate, DebateMessage, Persona } from '@/types';
```

### Step 2: Replace invalidateQueries Logic
Replace lines 92-95 with:

```typescript
} else if (message.type === 'message') {
  // Directly update React Query cache for real-time message display
  queryClient.setQueryData(['debate', slug], (old: Debate | undefined) => {
    if (!old) return old;

    // Find persona from participants list
    const persona = old.participants?.find(p => p.slug === message.persona_slug);

    // Create new message object from SSE event
    const newMessage: DebateMessage = {
      id: message.message_id!,
      persona: persona || {
        // Fallback minimal persona if not found in participants
        id: 0,
        name: message.persona_name || 'Unknown',
        slug: message.persona_slug || 'unknown',
        title: '',
        category: '',
        era: '',
        birth_year: null,
        death_year: null,
        religion_worldview: '',
      } as Persona,
      round_number: message.round_number!,
      content: message.content!,
      text_citations: [],
      created_at: new Date().toISOString(),
    };

    // Deduplicate: Check if message already exists
    const existingMessages = old.messages || [];
    const isDuplicate = existingMessages.some(m => m.id === newMessage.id);
    if (isDuplicate) {
      return old; // Already have this message, no update needed
    }

    // Append new message to array
    return {
      ...old,
      messages: [...existingMessages, newMessage],
      rounds_completed: message.round_number || old.rounds_completed,
    };
  });
}
```

### Step 3: Keep Completion Refetch
**Do NOT remove** the `invalidateQueries()` on lines 86-90 for status changes. When debate completes, a full refetch ensures:
- Final summary is fetched
- Any missing messages are retrieved
- Completed_at timestamp is accurate
- Citations are fully populated

---

## 6. Testing Strategy

### Manual Testing
1. **Start fresh debate** with 3+ participants, 3+ rounds
2. **Switch to theater mode** immediately after clicking "Generate"
3. **Verify real-time streaming:**
   - Messages appear one-by-one as they generate
   - Theater mode shows typewriter animation
   - Persona portraits highlight when speaking
   - Round counter increments correctly
4. **Check for duplicates:** No message should appear twice
5. **Verify completion:** All messages present after "completed" status
6. **Test network interruption:** Disconnect WiFi mid-generation, reconnect, verify recovery

### Browser DevTools Checks
- **Network tab:** Should show `stream/` request but minimal additional debate API calls
- **React DevTools:** Watch `debate.messages` array grow in real-time
- **EventStream tab:** Verify `message` events match rendered UI timing

### Edge Cases
- **First message:** Verify it appears immediately (not waiting for second message)
- **Fast generation:** Messages arriving <500ms apart don't create race conditions
- **SSE reconnect:** Messages don't duplicate after connection recovery
- **Page refresh:** Loading completed debate shows all messages (no streaming)

### Automated Testing
Update `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/frontend/__tests__/lib/hooks/useDebateSSE.test.tsx`:
- Mock `queryClient.setQueryData()` calls
- Verify it's called with correct message structure
- Verify deduplication logic prevents duplicate messages
- Test persona lookup (found vs not found scenarios)

---

## 7. Risks and Mitigations

### Risk 1: Race Conditions
**Scenario:** Multiple messages arrive rapidly before React re-renders.

**Mitigation:**
- React Query's `setQueryData` uses functional updater: `(old) => new`
- This ensures we always work with latest cache state
- Each update appends to array atomically
- No risk of message loss

### Risk 2: Duplicate Messages
**Scenario:** Message arrives via SSE, then refetch includes same message.

**Mitigation:**
- Deduplication check: `existingMessages.some(m => m.id === newMessage.id)`
- Only append if message ID not already present
- Message IDs are unique (database primary keys)

### Risk 3: Ordering Issues
**Scenario:** Messages arrive out of order (e.g., message #5 before #4).

**Current State:** Backend sends messages in chronological order via SSE.

**Mitigation:**
- Trust SSE ordering (backend generates sequentially)
- If needed, add sort by `round_number` + `created_at` after append
- **Not implementing** initial version (premature optimization)

### Risk 4: Missing Persona Data
**Scenario:** `persona_slug` in SSE event doesn't match any participant.

**Mitigation:**
- Fallback to minimal Persona object with slug/name from SSE
- Prevents crash, allows message to display
- Can refine persona data on completion refetch

### Risk 5: Memory Leaks
**Scenario:** Large debates with 100+ messages grow cache unbounded.

**Assessment:** Not a concern
- Messages are already stored in backend database
- React Query automatically garbage collects unused queries
- Debate page unmount triggers cleanup

### Risk 6: TypeScript Errors
**Scenario:** `Persona` type requires fields we don't have in SSE event.

**Mitigation:**
- Use `as Persona` type assertion for fallback minimal object
- Provides all required fields with empty/default values
- TypeScript will validate at compile time

---

## 8. Success Criteria

### Primary Goals
- ✅ Messages appear in theater mode **as they generate** (real-time)
- ✅ Typewriter animation activates during generation (not just on completion)
- ✅ Round counter increments in sync with visible messages
- ✅ No duplicate messages in UI
- ✅ No regression in completed debate viewing

### Performance Targets
- Message display latency: <50ms after SSE event received
- Zero additional HTTP requests during generation (except completion refetch)
- No UI jank or stuttering during rapid message arrival

### User Experience
- Theater mode feels "live" and engaging
- Users can read philosophical arguments as they develop
- Progress feels tangible (not just spinning loader)
- Completed debates load instantly (no streaming)

---

## 9. Rollback Plan

If this change causes issues:

### Immediate Rollback
```typescript
// Revert to original code (lines 92-95)
} else if (message.type === 'message') {
  // Trigger refetch to get new message with full data
  queryClient.invalidateQueries({ queryKey: ['debate', slug] });
}
```

### Diagnostics
- Check browser console for React Query errors
- Verify `debate.messages` structure in DevTools
- Test with single-participant debate (simplest case)
- Add verbose logging to setQueryData updater function

---

## 10. Alternative Approaches Considered

### Alternative 1: Optimistic Updates with Refetch
```typescript
// Immediately add message, then refetch to replace with full data
queryClient.setQueryData(['debate', slug], optimisticUpdate);
queryClient.invalidateQueries({ queryKey: ['debate', slug] });
```

**Rejected:** Adds unnecessary network traffic, defeats purpose of SSE.

### Alternative 2: Separate Messages Query
```typescript
// Store messages in separate React Query cache key
['debate', slug, 'messages']
```

**Rejected:** Complicates data fetching, requires changes to API client, breaks existing code.

### Alternative 3: WebSocket Instead of SSE
**Rejected:** SSE is simpler, unidirectional (server→client), no WebSocket infrastructure needed.

---

## 11. Post-Implementation Tasks

### Documentation
- Update `/Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/frontend/README.md` with SSE architecture notes
- Document cache update pattern for future streaming features

### Monitoring
- No special monitoring needed (client-side only)
- User feedback will indicate success (visible real-time updates)

### Future Enhancements
- Add message ordering safeguard (sort by round + timestamp)
- Stream citations in real-time (currently only on completion)
- Animate persona portraits during speaking (already implemented, will activate)

---

## 12. Estimated Effort

**Development:** 30 minutes
**Testing:** 30 minutes
**Code Review:** 15 minutes
**Documentation:** 15 minutes

**Total:** ~1.5 hours

---

## 13. Dependencies

### External Dependencies
- None (pure frontend change)

### Internal Dependencies
- React Query v5 (already installed)
- TypeScript types from `/types/index.ts` (already defined)
- SSE backend endpoint (already working)

### Breaking Changes
- None (purely internal optimization)

---

## Approval

This plan is ready for implementation. The solution is:
- **Minimal:** 22-line change in single file
- **Safe:** No breaking changes, preserves all existing functionality
- **Testable:** Clear success criteria and manual test steps
- **Reversible:** Simple rollback if issues arise

**Next Step:** Proceed to Implementation Phase
