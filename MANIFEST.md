# Public package inventory

## Entry and project documentation

- `SKILL.md`: workflow entry, license and icon metadata.
- `README.md`, `README.zh-CN.md`: English and Chinese quick start.
- `LICENSE`, `THIRD_PARTY_NOTICES.md`, `CHANGELOG.md`, `.gitignore`.
- `agents/openai.yaml`: optional Codex display/invocation metadata.
- `tests/test_public_package.py`: offline package checks; no presentation/model execution.

## Core references

- `contracts.md`, `reference-and-template.md`, `figures-and-evidence.md`.
- `tools-and-interfaces.md`, `acceptance-and-recovery.md`, `provenance-and-validation.md`.
- `platform-contract.md`, `cover-and-navigation.md`, `audience-content.md`, `migration.md`.
- `platforms/hana.md`, `platforms/dsh.md`, `platforms/codex.md`.

All are under `references/`. Platform adapters map capabilities and permissions; they do not establish end-to-end compatibility.

## Templates and original artwork

Under `assets/`:

- `job-contract.json`, `platform-contract.json`, `frontmatter-contract.json`.
- `evidence-ledger.csv`, `page-plan.csv`, `audience-review.csv`.
- `scene-contract.json`, `delivery-report.md`, `revision-examples.json`.
- `icon.svg`, `icon.png` (1024×1024), `banner.svg`.

## Six core helpers

Under `scripts/`:

- `preflight.py`: read-only capability discovery.
- `inspect_deck.py`: local PDF/PPTX inventory.
- `audit_pptx.py`: existing PPTX relationship audit.
- `check_fonts.py`: macOS font registration probe.
- `build_deck.mjs`: scene-to-PPTX components; needs explicit Node project.
- `apply_ooxml_styles.py`: explicit native gradients/preset adjustments.

The repository includes 41 files before Git metadata/build artifacts. No private session records, source decks, papers, research data, fonts or runtime dependencies are included.
