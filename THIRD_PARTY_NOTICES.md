# Sources and third-party notices

## This repository

The workflow guides, templates, helper scripts and original icon/banner are distributed under the MIT license in [LICENSE](LICENSE). The helper scripts were developed as part of the reference-driven presentation workflow; they are not copied from third-party Office skill implementations.

No reference deck, unpublished paper, research dataset, personal session log, font, model weight or third-party runtime is included.

## Runtime dependencies

Depending on the operation, users provide Python, Node.js, PptxGenJS, pdfplumber, pypdfium2 and Pillow. These packages are not vendored here and retain their respective licenses. Installing this skill does not install those dependencies.

Fonts and source figures remain subject to their own usage rights. A reference deck being readable does not automatically authorize redistribution of its assets.

## Documentation and packaging references

The project presentation borrows general documentation practices, not code, brand artwork or logos, from:

- [Anthropic Skills](https://github.com/anthropics/skills): concise skill metadata, per-skill directories and usage examples. Its repository contains components under different terms; no Office skill code is reused here.
- [Superpowers](https://github.com/obra/superpowers): workflow overview, categorized capabilities and platform-specific setup instructions.
- [OpenAI Build skills](https://developers.openai.com/codex/skills/): standard SKILL.md structure, local skill discovery and optional agents/openai.yaml metadata.

Hana, DeepSeek Harness and Codex are the target hosts described by the adapters. Their runtime and tool policies are not supplied or overridden by this repository.
