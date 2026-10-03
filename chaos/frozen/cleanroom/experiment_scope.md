# EXPERIMENT SCOPE (clean-room)

## What was run

A synthetic referential-communication loop.

- A world of **3 objects**, each with 3 attributes taken from a fixed vocabulary
  (2 values per attribute).
- A **sender** who knows which object is the target and emits a short message
  naming attributes of some object.
- A **receiver** holding a prior over the 3 objects. On receiving a message it
  forms a posterior by multiplying its prior by per-object likelihoods, then
  **samples** a decision according to that posterior at a temperature `T`.
- An **evaluator** scoring the decision against the intended target
  (`correct` = 1/0).

## The two arms

- `relevant`            the message names attributes of the **intended target**
- `irrelevant_matched`  the message names attributes of a **different object**,
                        matched for token count, vocabulary, channel, and order

`H_before` is constant at 1.5849625 (= log2 3) and `n_candidates_before` is
constant at 3, so both arms begin from an identical, uniform state.

## Design factors crossed in the file

`arm` x `target` x `rho_channel` x `temperature`

- `rho_channel`: 2 values (one noiseless, one degraded)
- `temperature`: 3 decision policies (sampled, not argmax)

## What the file does NOT contain

There is no feedback loop in `06_RAW_ROWS.jsonl`. Feedback trials were written
to a separate file and are NOT part of this package.

## Known scope limits

- 3 objects, 3 attributes, one message, one decision, no dialogue.
- The receiver's parser resolves a message token to exactly one attribute axis.
- No cost, no intent, no pragmatics, no human participants.
