# Test Coverage Enhancement Plan

This document outlines a phased approach to enhance test coverage for the observant.py library.

---

## 🧪 Phase 1: Assert Current Behavior (No Code Changes Needed)

These tests document and lock in the current behavior.

### ✅ Dirty Tracking
- [x] Computed fields are never dirty
- [x] Validation changes do not affect dirty state
- [x] Undoing a change reverts dirty state (or not—assert current behavior)

### ✅ Undo/Redo
- [x] Computed fields always return `False` for `can_undo()` and `can_redo()`
- [x] `undo()` and `redo()` on computed fields are no-ops
- [x] Undo/redo stacks are isolated per field
- [x] Undo after validation failure (should not be added to stack)

### ✅ Validation
- [x] Computed fields can be validated
- [x] `load_dict()` triggers validation
- [x] `save_to()` includes computed fields if they shadow real fields

---

## 🧠 Phase 2: Edge Case Tests for Existing Features

These are deeper tests for robustness and edge behavior.

### ✅ Validation
- [x] Validator returns non-string (e.g. int, None, object)
- [x] Validator throws unexpected exception (already partially covered)
- [x] Multiple validators return errors simultaneously
- [x] Validation state after undo/redo

### ✅ Computed
- [x] Computed field with no dependencies
- [x] Computed field name collision with real field
- [x] Circular dependency detection (A → B → A)

### ✅ Observable Behavior
- [x] Reentrant `on_change` (callback triggers another set)
- [x] Multiple `on_change` callbacks per field
- [x] Callback that raises an exception

---

## 🧰 Phase 3: Proxy Behavior & Model Integrity

These tests explore how the proxy behaves in less common or error-prone scenarios.

- [x] Observing a non-existent field
- [x] Wrapping a non-dataclass object
- [x] Calling `save_to()` into a different object
- [x] Proxy reuse after `save_to()`

---

## 🧼 Phase 4: New Feature – `reset_validation()`

### Implementation
- [ ] Add `reset_validation()` method
  - Clears all validation errors
  - Optionally re-runs validators
- [ ] Add `reset_validation(field_name)` for per-field reset

### Tests
- [ ] `reset_validation()` clears all errors
- [ ] `reset_validation(revalidate=True)` re-runs validators
- [ ] `reset_validation("field")` clears only that field's errors

---

## 🧪 Phase 5: Integration & Meta Behavior

These tests combine multiple features to ensure they interact correctly.

- [ ] Validation + Computed: errors show up in `validation_errors()`
- [ ] Undo + Computed: no effect, no crash
- [ ] Validation + Dirty: fixing validation does not affect dirty state
- [ ] Computed + Dirty: computed fields never appear in `dirty_fields()`
- [ ] `save_to()` includes computed fields
- [ ] `load_dict()` triggers validation
- [ ] `reset_dirty()` does not affect validation state
