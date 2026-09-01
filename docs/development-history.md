# Smart Carpool development history

This document records how Smart Carpool evolved from an initial repository into a validated and published web application. It is a retrospective based on the repository's immutable Git history: commit identifiers and dates were preserved, and no historical commit was rewritten.

## Relationship with UniCar

UniCar was the earlier academic prototype, developed in MIT App Inventor with block-based programming. It established the original carpooling requirements, user flows and business rules.

Smart Carpool is a separate web implementation built from the ground up with FastAPI, SQLAlchemy, PostgreSQL, HTML, CSS and JavaScript. It applies lessons from UniCar while maintaining its own source code, architecture, database migrations, tests and deployment history.

## Phase 1 — Repository foundation and planning

| Date | Commit | What changed |
| --- | --- | --- |
| 2026-07-14 | [`aef5187`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/aef51878014c7861f7fc5fcfa38735e234cbffda) | Created the repository foundation with a Python-oriented `.gitignore` and the initial project description. |
| 2026-07-14 | [`49c74e6`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/49c74e6257aefa434ae0a924d6f2ebdba10ce290) | Added the initial project plan and expanded the README. |
| 2026-07-14 | [`cce0699`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/cce06997d3b3260f522ab8c98f10d39774d364b0) | Merged pull request #1, incorporating the first planning documentation into `main`. |
| 2026-07-14 | [`9fbf56e`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/9fbf56ef077e4cee3d5a73a1019c40dc7d5920cc) | Defined the intended version 1.0 feature set in the project plan. |
| 2026-07-14 | [`60b9221`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/60b92212c2a4123d7cc70691c374eae9ef4593c6) | Introduced the initial SQL database schema. |
| 2026-07-14 | [`141a372`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/141a372c4543fe3688c9eb1a2d36844234a14a5b) | Initialized the FastAPI backend, database connection and Python dependencies. |

## Phase 2 — Demonstrable MVP

| Date | Commit | What changed |
| --- | --- | --- |
| 2026-08-25 | [`a0d1921`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/a0d1921d84cc3b27193a3b3a0d26c32644f994d6) | Published the v0.1 demonstrable MVP, adding the API, web interface, data model, security, seed data, documentation and automated tests. |

## Phase 3 — Local usability and production readiness

| Date | Commit | What changed |
| --- | --- | --- |
| 2026-08-28 | [`57b56bf`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/57b56bf343bc2c5892244c63db4e24f3351e98a1) | Finalized local project setup and adjusted model configuration. |
| 2026-08-28 | [`1818b05`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/1818b05ce88cbe5a05a9b13571cb1a3c57536daf) | Restored readable interface styles and added a simpler Windows startup path. |
| 2026-08-28 | [`547f2e3`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/547f2e37180cf89f02cba1dd73ca3ef0bee6ea79) | Completed the ride and booking lifecycle while adding migrations, Docker support, continuous integration and broader tests. |
| 2026-08-28 | [`fcf8755`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/fcf8755274d2df33f7d3e4581099a23a1de0c488) | Streamlined vehicle selection during ride publication and updated the interface and tests. |
| 2026-08-28 | [`d564fd8`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/d564fd809824e21542d2a2721aa0bf529444b9b8) | Prevented stale frontend assets and added coverage for the delivery behavior. |
| 2026-08-28 | [`cff37ea`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/cff37ea1292766315715aefd80b0862155ab74fa) | Added profile editing across the API, schemas, interface and tests. |
| 2026-08-28 | [`8531cb0`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/8531cb0e13783ee70142b54136b454cb7af1186a) | Added driver vehicle management with validation, interface support and automated tests. |

## Phase 4 — Validation and public documentation

| Date | Commit | What changed |
| --- | --- | --- |
| 2026-08-31 | [`441b015`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/441b01569f13d0d81054399a9821a7bc7c933ff8) | Updated the documented project status, validation evidence and roadmap. |
| 2026-09-01 | [`cce6f0d`](https://github.com/leonardo-h-oliveira/smart-carpool/commit/cce6f0d31604425167c12979ae8cb408548bdf14) | Translated the public documentation into English and closed issue #3. |

## Traceability notes

- The 16 commits above are the complete `main` history that existed when issue [#4](https://github.com/leonardo-h-oliveira/smart-carpool/issues/4) was opened.
- Earlier commits predate issue #4 and are linked here retrospectively rather than being presented as issue-driven work.
- This history document itself is delivered through a dedicated branch and pull request, establishing the issue → branch → commit → pull request workflow for subsequent work.
- Merge commits are identified separately from implementation commits so the record does not double-count delivered features.
