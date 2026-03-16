# AetherNet Phase-2 Whitepaper

## Deterministic Fragmentation, Reassembly, and DTN Transport Lifecycle

### Version

Phase-2 Implementation Whitepaper
Generated after **Wave-25 completion**

### Status

```
All tests passing
Wave-25 completed
107 pytest tests passing
```

---

# 1. Overview

AetherNet is a **research prototype of a delay-tolerant networking (DTN) infrastructure** designed to explore routing, storage, and transport behaviors in highly intermittent connectivity environments such as lunar communications.

Phase-1 of AetherNet established the core DTN primitives:

```
bundle generation
store-carry-forward routing
contact-aware transmission
multi-hop relay simulation
bundle lifecycle tracking
metrics and reporting
```

Phase-2 extends the architecture to support **bundle fragmentation and reassembly**, enabling realistic transport of large bundles across constrained contact windows.

This whitepaper describes the architecture and implementation of **Phase-2 (Wave-23 → Wave-25)**.

---

# 2. Phase-2 Goals

Phase-2 introduces three core capabilities:

| Capability            | Description                                              |
| --------------------- | -------------------------------------------------------- |
| Fragmentation         | Large bundles are deterministically split into fragments |
| Reassembly            | Fragment sets are reconstructed into the original bundle |
| Simulator Integration | Destination nodes automatically reassemble fragments     |

These capabilities enable the following lifecycle:

```
Bundle creation
→ Fragmentation
→ Multi-hop DTN transport
→ Fragment buffering at destination
→ Deterministic reassembly
→ Final bundle delivery
```

---

# 3. Phase-2 Architecture

The new Phase-2 transport pipeline:

```
Bundle
↓
fragment_bundle()
↓
Fragments
↓
DTN multi-hop routing
↓
Destination node
↓
ReassemblyBuffer
↓
reassemble_bundle()
↓
Final bundle delivered
```

---

# 4. Fragmentation Design (Wave-23)

Fragmentation was introduced in **Wave-23**.

### Fragment Metadata

Fragments inherit original bundle fields but include additional metadata:

```
is_fragment
original_bundle_id
fragment_index
total_fragments
```

Example fragment identifiers:

```
sci-001.frag-0
sci-001.frag-1
sci-001.frag-2
```

Fragment payload references are also deterministic:

```
payload.bin.frag-0
payload.bin.frag-1
payload.bin.frag-2
```

---

## Fragmentation Rules

Fragmentation obeys deterministic rules:

```
total_fragments = ceil(bundle_size / max_fragment_size)
```

Example:

```
Bundle size: 2500 bytes
Max fragment size: 1000 bytes

Fragments:
1000
1000
500
```

---

# 5. Reassembly Design (Wave-24)

Wave-24 introduced deterministic fragment reassembly.

Module:

```
protocol/reassembly.py
```

Key APIs:

```
can_reassemble(fragments)
reassemble_bundle(fragments)
```

---

## Reassembly Validation

A fragment set is considered valid if:

```
all bundles marked is_fragment
same original_bundle_id
same total_fragments
unique fragment_index values
fragment indices form complete sequence
metadata consistency across fragments
```

Fields required to match:

```
source
destination
type
priority
created_at
ttl_sec
```

---

## Reassembly Behavior

Fragments may arrive in **any order**.

Reassembly sorts fragments using:

```
fragment_index
```

The reconstructed bundle:

```
id = original_bundle_id
size_bytes = sum(fragment sizes)
is_fragment = False
fragment metadata cleared
```

Payload handling uses deterministic placeholder reference:

```
reassembled/{original_bundle_id}
```

---

# 6. Reassembly Integration (Wave-25)

Wave-25 integrates fragment reassembly into the simulator.

Fragments are intercepted at the **final hop**.

Integration point:

```
Simulator._process_hop()
```

When a fragment reaches its destination:

```
fragment
→ ReassemblyBuffer.add()
→ check can_reassemble()
→ if complete
→ reassemble_bundle()
→ deliver final bundle
```

---

## Reassembly Buffer

Module:

```
protocol/reassembly_buffer.py
```

Structure:

```
original_bundle_id → list[fragment bundles]
```

Example:

```
{
  "sci-001": [frag0, frag1, frag2]
}
```

Buffer operations:

```
add(fragment)
get(bundle_id)
remove(bundle_id)
```

---

# 7. Simulator Behavior

Final hop logic now supports two cases.

### Normal Bundle

```
bundle
→ delivered
→ metrics recorded
```

### Fragment

```
fragment arrives
→ added to reassembly buffer
→ check completeness
→ if complete
→ reassemble bundle
→ deliver reconstructed bundle
```

Fragments themselves are not treated as final deliverables.

---

# 8. Testing Coverage

Phase-2 introduced multiple new test groups.

### Fragmentation

```
tests/test_fragmentation.py
```

Validates:

```
deterministic fragment sizes
metadata inheritance
serialization compatibility
```

---

### Reassembly

```
tests/test_reassembly.py
```

Validates:

```
out-of-order arrival
incomplete fragments
duplicate fragments
mismatched metadata
invalid fragment sets
```

---

### Integration

```
tests/test_fragment_reassembly_integration.py
```

Validates:

```
buffer behavior
mixed fragment sets
fragment grouping
buffer cleanup
```

---

# 9. Test Status

After Wave-25:

```
pytest tests/
107 tests passing
0 failures
```

Phase-2 has full regression coverage.

---

# 10. Current Limitations

The following features are **not yet implemented**:

### Fragment retransmission

Lost fragments cannot be retransmitted.

### Fragment garbage collection

Incomplete fragment sets remain in memory.

### Contact-aware fragmentation

Fragment size is not yet determined by contact capacity.

### Custody transfer

Bundles are not yet protected by custody acknowledgements.

---

# 11. Known Technical Debt

Two improvements have been identified for future waves.

### Fragment Metrics Separation

Current metrics may mix fragment and bundle delivery events.

Future work will separate:

```
fragments_delivered
bundles_reassembled
bundles_delivered
```

---

### Fragment Artifact Cleanup

Currently the store may contain:

```
fragment bundles
reassembled bundle
```

Future work may remove fragment artifacts after successful reassembly.

---

# 12. Future Roadmap

Phase-3 will focus on improving transport realism and DTN protocol semantics.

Planned work:

```
Wave-26  Contact-aware fragmentation
Wave-27  Partial contact transmission
Wave-28  Contact plan parser
Wave-29  Custody transfer
Wave-30  Fragment retransmission
Wave-31  Fragment garbage collection
Wave-32  Fragment metrics separation
Wave-33  Fragment artifact cleanup
Wave-34  Experiment runner
Wave-35  Research visualization
```

---

# 13. Conclusion

Phase-2 transforms AetherNet from a DTN routing prototype into a **complete delay-tolerant transport simulator**.

The system now supports:

```
fragmentation
multi-hop DTN transport
destination-side reassembly
deterministic lifecycle tracking
```

These capabilities position AetherNet as a **research-grade DTN simulation platform** suitable for exploring contact-aware routing strategies and deep-space networking architectures.

---
