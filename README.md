# Total a fictional spending CSV

Save the three source files in a NEW empty local lesson folder.

    python make_sample.py
    python spendsum.py sample/spending.csv
    python -m unittest -v

Two Windows and two Ubuntu replays use exact visible file versions. Final 41 small fixture tests pass (Unix pipe skips on Windows); symlinks may skip where unavailable. Displayed stdout is first Windows run, not mixed or normalized. Paired runs differ in unittest time. The naive prototype is intentionally wrong and only for the fictional sample before full replacement.
Only filesystem/link behavior changes in the final checker: it refuses input or ancestor symbolic links/reparse points, hardlinks, special files and parent traversal before opening the file. Metadata/open failures return exit 2. Setup exclusively creates a NEW fictional sample and now also refuses linked ancestors/traversal. Existing paths are not reset/replaced; partial files remain on failure.
Original CSV/date/amount/category rules and totals are retained, including the original treatment of malformed skipped rows: they are listed and omitted from totals but the report keeps its prior exit 0. That is not a complete-data or accuracy certificate. All amounts are one currency; no conversion or verified bank-export compatibility. No new parsing rule or formula-safety validation is claimed.
The checker has no write/move/delete/network code. It reads rows into memory and can print private excerpts; it is not a resource sandbox, atomic snapshot or hostile-race defense. Stop editors/sync and do not disclose real account details. Small synthetic fixtures do not establish financial advice, real bank compatibility or behavior on every filesystem. No desktop Windows/macOS recording.
Recorder removes only its own temporary fixture folder. Decisions and feedback are teaching text, not recorded output.

MIT code. Python separately licensed and not included.

## Paired recordings

- Windows: https://github.com/faiz12321/lesson-lab/actions/runs/38968578966
- Ubuntu: https://github.com/faiz12321/lesson-lab/actions/runs/38968693311

Python filesystem reference: https://docs.python.org/3/library/os.html
