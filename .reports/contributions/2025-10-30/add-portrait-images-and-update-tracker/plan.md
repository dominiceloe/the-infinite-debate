# Implementation Plan: Add Portrait Images and Update Tracker

**Date:** 2025-10-30
**Type:** docs
**Complexity:** SMALL
**Scope:** frontend + documentation

## Summary

Adding 28 new persona portrait images to production frontend and updating PERSONAS_IMAGE_TRACKER.md to reflect the newly added images. All images are already generated and placed in the correct directory, requiring only git tracking and documentation updates.

## Affected Files

### New Files (28 portrait images in `frontend/public/portraits/`)
1. abbie-hoffman.png (2.8M)
2. allen-ginsberg.png (2.7M)
3. angela-davis.png (2.7M)
4. bill-hicks.png (2.6M)
5. camille-paglia.png (2.9M)
6. claude-levi-strauss.png (2.8M)
7. clifford-geertz.png (2.8M)
8. dave-chappelle.png (2.6M)
9. david-graeber.png (2.6M)
10. emma-goldman.png (2.8M)
11. franz-boas.png (2.8M)
12. george-carlin.png (2.3M)
13. hannah-gadsby.png (2.7M)
14. howard-zinn.png (2.8M)
15. hunter-s-thompson.png (2.7M)
16. jon-stewart.png (2.7M)
17. jordan-peterson.png (2.9M)
18. lenny-bruce.png (2.3M)
19. malcolm-gladwell.png (2.9M)
20. margaret-mead.png (2.4M)
21. mark-twain.png (2.3M)
22. mary-douglas.png (2.6M)
23. nassim-nicholas-taleb.png (2.8M)
24. noam-chomsky.png (2.8M)
25. slavoj-zizek.png (2.9M)
26. thomas-sowell.png (2.9M)
27. timothy-leary.png (2.7M)
28. zora-neale-hurston.png (2.8M)

### Modified Files (1)
- PERSONAS_IMAGE_TRACKER.md (already modified, needs verification)

**Total file size:** ~75MB for all 28 images (avg 2.7MB each)

## Implementation Steps

### 1. Verify Tracker Document Changes
- Review existing changes to PERSONAS_IMAGE_TRACKER.md
- Confirm all 28 new personas are properly marked with `[x]` checkbox
- Verify filenames match actual image files (snake_case vs kebab-case)
- Ensure correct categorization

### 2. Add Images to Git
- Stage all 28 portrait images: `git add frontend/public/portraits/*.png`
- Verify no extraneous files are included

### 3. Commit Changes
- Commit with conventional format: `docs(personas): add 28 new portrait images and update tracker`
- Include detailed body listing categories affected

## Validation Criteria

### File Tracking
- [ ] All 28 images appear in git status as staged
- [ ] PERSONAS_IMAGE_TRACKER.md changes are staged
- [ ] No other unintended files are staged (e.g., DEPLOYMENT_CHECKLIST.md)

### Documentation Accuracy
- [ ] Each new persona has `[x]` checkbox in tracker
- [ ] Filename conventions match actual files
- [ ] Image counts per category are accurate
- [ ] Markdown linting passes (no syntax errors)

### Image Quality
- [ ] All images are PNG format
- [ ] File sizes are reasonable for web (2-3MB is acceptable)
- [ ] Images display correctly in frontend (manual verification recommended)

## Risk Assessment

### Low Risk
- Documentation-only change with static assets
- No code logic changes required
- Images already generated and placed correctly

### Potential Issues
1. **File Size:** 75MB addition to repo
   - Mitigation: Within acceptable range for static assets
   - Alternative: Consider image optimization (future task)

2. **Filename Mismatches:** Tracker uses underscores (e.g., `mark_twain.png`) but files use hyphens (e.g., `mark-twain.png`)
   - Mitigation: Verify tracker document reflects actual filenames
   - Fix any discrepancies before commit

3. **Missing Personas:** Some images may not have corresponding persona records in database
   - Mitigation: Verify with `python manage.py load_personas` after commit
   - Update backend if needed (separate task)

## Expected Outcome

After successful completion:
- 28 new portrait images committed to git and available in production
- PERSONAS_IMAGE_TRACKER.md accurately reflects all images
- Frontend can display portraits for newly added personas
- Total persona count with images increases from 52 to 80
