# Project Milestone Roadmap

| Milestone | Status | Goal / Deliverable | Timebox (working days) | Key Tasks | Success Criteria |
|-----------|--------|-------------------|------------------------|-----------|-------------------|
| **M1 – Foundations** | **Complete** | Local development environment & CI ready | 1 | • Use existing `feature/ios-app` branch  <br>• Keep `mobile-ios/` scaffold  <br>• Keep iOS `.gitignore` coverage  <br>• Maintain GitHub Actions workflow `ios-ci.yml`  <br>• Verify CI fails on real build failures instead of skipping them | CI run shows **✅ Success** from a real XcodeGen-generated project build |
| **M2 – Project Skeleton** | **Complete** | Xcode project and shared API layer | 2 | • Keep XcodeGen config in `mobile-ios/project.yml`<br>• Commit generated/openable Xcode project strategy documentation<br>• Keep minimal API models (`Job`) as `Decodable` structs<br>• Add unit-test target for model parsing | XcodeGen generates a project without errors; Xcode opens without errors; unit tests for model parsing pass locally and in CI |
| **M3 – First Feature – Job List** | **Partially complete** | Fetch and display job list | 4 | • Keep networking layer (`APIService`)<br>• Keep job list view model<br>• Keep SwiftUI job list/detail views<br>• Validate API response shape against backend<br>• Add UI unit test / snapshot test if needed | Running the app on a macOS simulator shows a list of jobs pulled from the API; CI passes relevant tests |
| **M4 – CRUD Operations** | **Planned** | Add / edit / delete a job | 5 | • UI for adding a job (modal form)<br>• POST/PUT/DELETE endpoints in `JobService`/API layer<br>• Local state sync with server responses<br>• Add corresponding unit & UI tests<br>• Update CI to include new tests | All CRUD actions work on simulator; CI shows **✅** for all new tests |
| **M5 – Offline & Persistence** | **Planned** | Cache jobs locally for offline use | 3 | • Choose persistence (CoreData or SwiftData)<br>• Store fetched jobs locally<br>• Sync strategy on app launch<br>• Add integration test for offline mode | App displays cached jobs when network unavailable; CI passes offline-mode test |
| **M6 – Polish & Release Prep** | **Planned** | App Store readiness | 4 | • Add app icons & launch screen assets<br>• Configure `Fastlane` for build, code-sign, TestFlight upload<br>• Integrate crash-reporting (Sentry/Firebase)<br>• Write release notes & update README<br>• Run final end-to-end CI (including Fastlane) | Fastlane produces a signed `.ipa` and publishes to TestFlight; CI shows all steps **✅** |
| **M7 – Post-Launch Ops** | **Planned** | Monitoring & feedback | Ongoing | • Set up monitoring dashboards (App Store Connect, Sentry)<br>• Collect user feedback, triage bugs<br>• Plan next feature sprint | Bugs resolved within sprint; roadmap updated in the repo’s `PROJECT.md` |

**How to use this roadmap**

1. Create a GitHub Milestone for each row (M1-M7).
2. Add Issues that map to each milestone’s “Key Tasks”.
3. Link PRs to the appropriate milestone – GitHub will track progress automatically.
4. Keep each milestone gated on successful CI runs; any failing step blocks the milestone from advancing.
