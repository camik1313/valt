# `ml/` — Machine-learning models (future)

This directory is intentionally empty for now. It exists to mark **where** machine-learning
models will live so the architecture is ready for them from day one.

## What will go here (later)

Once the rule-based biomechanics pipeline (Stage 7) is working and validated, this is where
learned models plug in — for example:

- **Risk-band classifiers** — models trained on labeled landing clips to categorize a
  landing's overall movement quality, instead of relying only on fixed angle thresholds.
- **Landing-frame detectors** — a learned model to identify the landing frame more robustly
  than the rule-based detector in `cv/landing_detector.py`.
- **Landmark smoothing / correction** — models that clean up noisy pose estimates.

## How it stays decoupled

Code in `ml/` will be called by the `services/` layer, never directly by the API routes.
That means adding, swapping, or removing a model never changes the endpoints or the
frontend — exactly the property that lets the project grow without rewrites.

Each model will document: what it was trained on, how it was validated, and its known
limitations. That documentation is part of doing this responsibly.
