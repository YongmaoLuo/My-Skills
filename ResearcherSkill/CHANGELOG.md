# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-03-24

### Added
- `CHANGELOG.md` — changelog following Keep a Changelog format
- Before building a qualitative rubric, the skill now asks the user whether they already know their criteria or need help figuring them out
- GitHub Actions pipeline that automatically creates a GitHub Release on every version tag push, with release notes extracted from `CHANGELOG.md`

## [1.0.0] - 2026-03-23

### Added
- Initial release of the Researcher Skill (`researcher.md`)
- Autonomous experimentation loop: interview, lab setup, think-test-reflect cycle
- `.lab/` directory as local, untracked experiment log (git-safe)
- `README.md` with use cases, examples, and experiment results
- `GUIDE.md` — detailed usage guide
- FAQ

[Unreleased]: https://github.com/krzysztofdudek/ResearcherSkill/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/krzysztofdudek/ResearcherSkill/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/krzysztofdudek/ResearcherSkill/releases/tag/v1.0.0
