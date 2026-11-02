# Test-release document snapshot

2 November 2026. Prepared only the public package's `06_SUBMISSION/` folder for v2.1.2-r0. No GitHub, Git push, release, model fitting or scientific rerun was performed by this subtask.

## Files and exact changes

- `Manuscript.docx` comes from the latest accepted clean author master. The single Data Availability Statement version string changes from v2.1.2-r1 to v2.1.2-r0 in the repository copy only. Raw document XML differs by this one ASCII digit; every other ZIP part is byte-identical. Native equations, tables, figures, references and all scientific text remain unchanged.
- `Supplementary_Information.docx` is a byte-identical copy of the latest author-saved accepted SI (saved at 17:57). Compared with the previously accepted logical baseline, its only paragraph-text change is two blank paragraphs before S3. All cell text in all five tables matches that baseline exactly: S1 11×6, S2 10×5, S3 4×6, S4 13×5 and S5 24×6. No CSV scientific values need updating for this resave.
- Replaced the staged old tracked submission files and old revision-change/map text with a current README, concise manuscript-file map and master/copy checksum identity record. The local editorial tracked documents and reviewer response letters are not included publicly.

## Executed verification

All checks and exact hashes are in `publication_document_snapshot.json`. All local author masters remain unchanged. Repository manuscript and SI contain no tracked-change or comment anchors, and tracking is disabled. Every relative link in the submission README and file map resolves within the package.

Both repository Word files rendered successfully with the bundled 26.1026.10807 document runtime and bundled LibreOffice. The manuscript has 23 pages. Its only pixel difference from the previously reviewed author-master render is page 20, where the version label is now v2.1.2-r0; that page was opened and inspected. The other 22 pages are pixel-identical. All six pages of the latest author-saved SI were opened and inspected. The preserved author layout gives each of S1–S5 its own page after the title page; captions and complete tables stay together, values are legible, and S5's 23 rows fit on one page. This is six clean SI pages, not the earlier five-page snapshot.

The final v2.1.2-r1 release remains unpublished by this subtask. This test snapshot does not represent journal submission or final author approval.
