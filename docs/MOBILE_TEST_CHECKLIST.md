# APFA Mobile Test Checklist
## From QA Script v3 Tests 1.12, 11.1-11.3

**Test environment:** Chrome DevTools device emulation OR real device
**Test devices:** iPhone 12 (390×844), Pixel 6 (412×915), iPad Mini (768×1024)

---

### Test 1.12 — Landing Page Mobile (375px)
- [ ] No horizontal scrolling/overflow
- [ ] Hero stacks vertically
- [ ] All buttons tappable (44px+ touch target)
- [ ] Feature cards stack to single column
- [ ] Navigation adapts (hamburger or simplified)

### Test 11.1 — Landing Page Mobile
- [ ] Set viewport to 375×812 (iPhone SE)
- [ ] No horizontal overflow
- [ ] Hero stacks vertically
- [ ] All buttons tappable (44px+)
- [ ] Feature cards stack to single column

### Test 11.2 — App Mobile
- [ ] Login form fits mobile viewport
- [ ] Sidebar collapsed (hamburger or hidden)
- [ ] Advisor composer at bottom, messages scrollable
- [ ] Send button reachable
- [ ] Dashboard loads without horizontal overflow

### Test 11.3 — Dashboard Mobile
- [ ] KPI cards stack vertically
- [ ] Widgets stack to single column
- [ ] No horizontal overflow
- [ ] Investment Growth Calculator inputs usable on mobile

---

**Status:** INCONCLUSIVE from CoWork (resize_window didn't constrain viewport).
No code changes in v4/v5 affect mobile CSS — treating as no-regression.
Manual verification needed.
