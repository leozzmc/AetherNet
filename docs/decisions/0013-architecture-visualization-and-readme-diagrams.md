# ADR 0013: Architecture Visualization and README Diagrams

**Date**: 2026-03-13
**Status**: Accepted

## Context
As Phase 1 of AetherNet reached completion, the repository successfully transformed into a rigorous Delay-Tolerant Networking (DTN) research platform. However, text-heavy explanations of Store-Carry-Forward mechanics and strict priority queues present a high cognitive load for new readers, collaborators, or researchers reviewing the project.

## Decision
We integrated Mermaid.js diagrams directly into `README.md` and created a dedicated `docs/architecture.md`. The visualizations explicitly cover the High-Level Architecture, Multi-Hop Data Flow, and Codebase Module Mapping.

## Rationale
1. **GitHub Native Rendering**: Mermaid diagrams render natively on GitHub without needing to commit binary image files (`.png`, `.jpg`).
2. **Docs-as-Code**: Because the diagrams are text-based, they remain perfectly version-controlled. Any future topological changes (e.g., adding a Mars node) can be updated via simple PR diffs.
3. **Immediate Clarity**: A sequence diagram showing a bundle pausing at a relay node instantly communicates the core value proposition of DTN better than paragraphs of text. This fulfills the requirement of making the MVP "Demo & Research Ready".