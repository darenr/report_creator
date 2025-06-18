# Change Log

All notable changes to this project will be documented in this file.

## 1.1.0 (June 18, 2025)

- Refactored code into modules for improved maintainability
- Added support for `Path` objects in `logo` parameter of `ReportCreator`
- Added new language components: `rc.Shell()`, `rc.Bash()`, and `rc.Sh()`
- Enhanced `rc.Sql()` component with `prettify` option for automatic SQL formatting
- Added `scroll_long_content` option for code components to manage long content display
- Improved documentation with additional examples and clearer explanations
- Fixed Mermaid diagram rendering issues in collapsed sections
- Optimized pan/zoom functionality for diagrams
- Updated styling and CSS for better component appearance and layout
- Theme consistency improvements throughout components

## 1.0.38

- Make pan and zoom support for `rc.Diagram()` optional (defaults True)
- Add `rc.Radar()` component that sources data from a Pandas `DataFrame`
- Docs improvements (numerous)
- `tabulate` (MIT License) added as dependency
- Doubled the number of tests, increased tewst coverage to 72%

## 1.0.37

- Optional put code blocks in vertical scrollable windows to limit the report length.
- Add pan/zoom for `rc.Diagram()`
- Markdown now allows mermaid fenced code blocks (like Github does)

## 1.0.36

- Style code blocks better (remove injected comment)
- fix quirky behavior when it comes to width and layout issue for contents within a `rc.Collapse()`

## 1.0.35

- Added missing dependency package (`python-dateutil`)

## 1.0.34

- Block \<script\> tags in Markdown when converting to HTML (while preserving other HTML)
- Added emoji support to `rc.Markdown()` for full GitHub-flavored-markdown compatibility :red_heart:
- Fixed [c.Diagram() do not get re-sized when they are initially hidden](https://github.com/darenr/report_creator/issues/13)
- Code default theme changed to highlight.js `xcode` colors
  eibcccntjuefdretbjgefbucldrcehetcgrnbtdtdftb
