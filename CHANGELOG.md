# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.3.0] - 2020-04-10
### Changed
 - Split functions and config into `helper.py` and `config.py`.
 - Moved more elements over to `replacements.json` than hard-coding.
 - Replaced all string joining of path to `os.path.join()` for better OS compatibility.
 - More intelligent dropping of rows using anchor text.
 - Better console printing.

## [0.2.3] - 2020-04-09
### Changed
 - Amended list of regions to pick up those where the first character is not read by `tabula-py`.
 - Amended `region` and `location_type` generation to take care of the above accordingly.

## [0.2.2] - 2020-04-08
 - Updated README.md
 - Updated CHANGELOG.md

## [0.2.1] - 2020-04-07
### Added
 - Created CHANGELOG.md
### Changed
 - Fixed DF merge by adding `ignore_index=True`.
 - Updated README.md

## [0.2.0] - 2020-04-07
### Changed
 - Changed the `trim_all_columns(...)` function to a more general cleaning function `clean_text(...)`.
 - Amended output file naming convention to match source PDF file.

## [0.1.1] - 2020-04-07
 - General progress

## [0.1.0] - 2020-03-19
 - General progress
