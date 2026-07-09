# Project Milestone Roadmap

| Milestone | Status | Goal / Deliverable | Timebox (working days) | Key Tasks | Success Criteria |
|-----------|--------|-------------------|------------------------|-----------|-------------------|
| **M1 – Foundations** | **Complete** | Local development environment & CI ready | 1 | • Use existing `feature/ios-app` branch  <br>• Keep `mobile-ios/` scaffold  <br>• Keep iOS `.gitignore` coverage  <br>• Maintain GitHub Actions workflow `ios-ci.yml`  <br>• Verify CI fails on real build failures instead of skipping them | CI run shows **✅ Success** from a real XcodeGen-generated project build |
| **M2 – Project Skeleton** | **Complete** | Xcode project and shared API layer | 2 | • Keep XcodeGen config in `mobile-ios/project.yml`<br>• Commit generated/openable Xcode project strategy documentation<br>• Keep minimal API models (`Job`) as `Decodable` structs<br>• Add unit-test target for model parsing | XcodeGen generates a project without errors; Xcode opens without errors; unit tests for model parsing pass locally and in CI |
| **M3 – First Feature – Job List** | **Ready for simulator QA** | Fetch and display job list | 4 | • Keep networking layer (`APIService`)<br>• Keep job list view model<br>• Keep SwiftUI job list/detail views<br>• Validate API response shape against backend<br>• Add UI unit test / snapshot test if needed | CI verifies build, tests, and backend-compatible `JobReport` decoding; final completion requires running the app on a macOS simulator to confirm the list displays jobs from the API |
| **M4 – CRUD Operations** | **Backend + iOS network layer done; UI blocked on simulator QA** | Add / edit / delete a job | 5 | • ✅ Define persistence strategy (file store behind swappable interface)<br>• ✅ Add POST/PUT/DELETE endpoints in backend API layer<br>• ✅ Add API tests for CRUD behavior<br>• ✅ Add iOS `APIService` create/update/delete methods (iOS CI green)<br>• ⏸ Add UI for adding/editing/deleting jobs — deferred, needs interactive simulator QA<br>• ⏸ Add corresponding UI tests — deferred with the UI | Backend CRUD + iOS `APIService` methods merged to `develop` with CI ✅. Remaining view model/UI work (steps 5–6) paused: final acceptance requires interactive simulator QA, unavailable in the current environment. |

**Known debt / blockers**

- **iOS simulator QA gap**: M3 final acceptance and M4 UI steps both require running the app on an iOS 17 simulator. Not possible on the current macOS Big Sur (11.6.7) machine (max Xcode 13.2.1 / iOS 15 SDK). Unblocked by a newer Mac, an OS upgrade, or a cloud Mac. iOS CI still covers build + unit tests headlessly.
- **black CI debt**: `ci.yml`'s `black --check src/scraper` is red repo-wide (src/scraper was never black-formatted). Pre-existing; to be fixed on a dedicated branch (pin `black==24.10.0` + one-time `black src/`).
| **M5 – Offline & Persistence** | **Planned** | Cache jobs locally for offline use | 3 | • Choose persistence (CoreData or SwiftData)<br>• Store fetched jobs locally<br>• Sync strategy on app launch<br>• Add integration test for offline mode | App displays cached jobs when network unavailable; CI passes offline-mode test |
| **M6 – Polish & Release Prep** | **Planned** | App Store readiness | 4 | • Add app icons & launch screen assets<br>• Configure `Fastlane` for build, code-sign, TestFlight upload<br>• Integrate crash-reporting (Sentry/Firebase)<br>• Write release notes & update README<br>• Run final end-to-end CI (including Fastlane) | Fastlane produces a signed `.ipa` and publishes to TestFlight; CI shows all steps **✅** |
| **M7 – Post-Launch Ops** | **Planned** | Monitoring & feedback | Ongoing | • Set up monitoring dashboards (App Store Connect, Sentry)<br>• Collect user feedback, triage bugs<br>• Plan next feature sprint | Bugs resolved within sprint; roadmap updated in the repo’s `PROJECT.md` |

**Windows Desktop Client** (`desktop-win/`)

Cross-platform companion to the iOS app, built with PySide6 (Qt for Python). Reuses the same REST API — no backend changes.

| Milestone | Status | Goal / Deliverable | Key Tasks | Success Criteria |
|-----------|--------|-------------------|-----------|-------------------|
| **W1 – Client Feature Parity** | **Complete** | Desktop client mirroring iOS | • `Job` model aligned with `Job.swift` (incl. legacy `salary` → `salaryRange`)<br>• `APIClient` for `GET /api/latest-report` + CRUD (`POST/PUT/DELETE /api/jobs`)<br>• Job list, score-filter slider, open-URL-to-apply, add/edit/delete UI<br>• Configurable API base URL (`%APPDATA%/JobMonitor/settings.json`) | Client runs on Windows, loads jobs, filters, opens URLs, and performs CRUD; `pytest desktop-win` green (model parsing + request construction) |
| **W2 – CI Coverage** | **Complete** | Windows client in CI | • Add GitHub Actions workflow running `pytest desktop-win` (headless, no GUI)<br>• Gate PRs to `develop` on it | CI run shows **✅** on the desktop-win test suite |
| **W3 – Offline & Persistence** | **Planned** | Cache jobs locally for offline use | • Store fetched jobs locally<br>• Load cache when the API is unreachable<br>• Add test for offline fallback | Client displays cached jobs when offline; CI passes offline-mode test |
| **W4 – Packaging & Release** | **Planned** | Standalone Windows executable | • PyInstaller build (`--onefile --windowed`)<br>• Optional: build the `.exe` in CI and attach as artifact<br>• Document install/run in `desktop-win/README.md` | PyInstaller produces a runnable `dist/JobMonitor.exe` |


**How to use this roadmap**

1. Create a GitHub Milestone for each row (M1-M7).
2. Add Issues that map to each milestone’s “Key Tasks”.
3. Link PRs to the appropriate milestone – GitHub will track progress automatically.
4. Keep each milestone gated on successful CI runs; any failing step blocks the milestone from advancing.
