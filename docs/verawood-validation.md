# Verawood implementation and validation

Historical validation recorded on 2026-09-08 for the source references below.
The results and temporary artifacts describe that validation run, not the current
release tree. Subsequent edits include package metadata, source defaults and the
Panorama prerelease version; rerun affected checks before release. Publication,
push and deployment status are not established by this historical record.

## Review follow-up (2026-09-26)

The current working tree passed `make test`: lint, strict types, formatting,
wheel/sdist validation, Tutor rendering, 25 Python tests and four JavaScript
tests. CI now runs Python contracts and navigation checks, including parsing
generated standalone and frontend-base configurations. Both CI matrices cover
Python 3.10–3.14; the local run used Python 3.12.

All four opt-in Fluent Bit replay cases passed separately using the existing
local collector image with Fluent Bit 5.0.9. This does not establish a rebuild
of the pinned collector image or Linux Engine execution. The sink invocation
now supplies the Linux host-gateway mapping. Docker/CRI fixtures use a realistic
IP prefix; braces and Unicode remain inside the event payload.

The native slot nesting finding was rejected: frontend-base's
[WidgetAppendOperation](https://github.com/openedx/frontend-base/blob/main/runtime/slots/widget/types.ts)
defines `id` and `component` at the operation root. The standalone header also
supports `mobile_main_menu_slot` as an alias; the contribution now uses its
canonical `org.openedx.frontend.layout.header_mobile_main_menu.v1` identifier.
The backend `22.0.0` release was verified available through PyPI's version JSON
endpoint, so the requested PyPI installation remains in place.

The backend install now mounts platform constraints and runs `pip check`;
final image assembly remains a staging gate. Legacy RBAC removal is an explicit
operator migration in the README, not an automatic cluster-wide deletion.
The broad LMS pod input is intentional and includes matching sidecars, as
required by the workspace collection policy. No live cluster was changed.

## Exact targets

- Tutor 22.0.2 with tutor-mfe 22.0.0; configured platform reference is
  `release/verawood.1` (`9e67d1429d5ab49a36fb9881a26457efeee0bb89`).
- Local edx-platform is clean on `release/verawood` at
  `259473c5dfd1c82eac5e6c4d14bf6095cb25824d`. It is not the exact release-tag commit.
- Backend shared constraints use the exact release requirements; independent
  extractor security updates are not LMS compatibility pins.
- Node 24.17.0; generated site lock uses frontend-base 1.0.1. Both optional authn
  and learner-dashboard apps were included with instructor-dashboard/notifications.
- Fluent Bit image 3.4.15 manifest digest
  `sha256:88e1b56cedb230486afeca6eeb26c5f6bd59c48879d0054d1674d5a58838c607`;
  amd64 binary reports 5.0.9. Manifest also contains arm64, not runtime-tested here.

## Delivered behavior

Panorama remains a standalone MFE. Native desktop/mobile frontend-base slots and
legacy MFE slots ask `/panorama/api/get-user-access` and update on authentication
changes. All Panorama imports are aliased. Legacy patches are omitted from the
compatibility shim files; no duplicate native/compat Panorama links are registered.
Runtime configuration flows through the existing MFE-to-site translation, leaving
explicit frontend-site configuration and database overrides with their normal precedence.

Tutor gates backend/settings/migrations/navigation/app registration together and
invalidates tutor-mfe caches after final configuration loading. Init applies committed
migrations outside DEMO mode; DEMO skips backend initialization. The original
validation used source overrides or mounted reviewed sources and required
operator configuration. Current defaults use backend PyPI version `22.0.0`,
MFE `release/verawood/v20260926` and extractor `v1.0.1`; verify these artifacts
contain the changes being tested.

CronJobs forbid overlap and have bounded deadlines/retries/history and memory
settings. Extractor images use Python 3.12, lock installation and package installation,
retaining cron and legacy script support. One site's Fluent Bit DaemonSet collects
LMS pod log files across all namespaces; other sites must disable their collectors. RBAC
names and persistent offsets/S3 spool remain scoped to the collector installation,
with bounded buffers and CRI/Docker multiline parsing. The input remains
`lms*.log` with `lms-worker*.log` excluded, including matching sidecar files.
This follows the clarified multisite architecture recorded in the updated plan.
Consumer S3 paths and raw event text remain compatible.

The local unpublished `tutor-contrib-branding` checkout was already installed.
Its legacy context import still broke the generated compatibility file. Two narrow
patch changes now select frontend-base SiteContext for compatibility rendering and
legacy AppContext for standalone MFEs, with branding aliases and matching theme/config
access. Existing branding changes and version were preserved.

## Historical local results (2026-09-08)

- Tutor: 20 contract tests cover all 16 mode/MFE/Fluent Bit combinations, source
  overrides, HTTPS/development URLs, collector state isolation, cross-namespace
  LMS selection/worker exclusion and cached registry refresh.
- Navigation: 3 Node tests pass, exercising grants, denial, errors, login/logout,
  stale promises, unsubscribe cleanup, and combined generated import parsing.
- Fluent Bit: 4 Docker tests pass on amd64: local/Docker/CRI replay, split records,
  oversized physical line followed by a valid event, and gzip NDJSON plus exact
  Compose consumer key in a disposable local HTTP S3 sink with fake credentials.
- Backend: 97 tests pass, including malformed provider shapes, access/author checks,
  errors and data migration. Exact-target dependency check and initial packaging pass.
- Extractor: 138 tests pass, 93.86% coverage; runtime audit has no known advisories,
  pip check, wheel/sdist/entrypoint and asset checks pass.
- MFE: clean dependency install, lint, 22 tests and production build pass. Legacy
  Sass theme duplication/imports were removed in favor of Verawood's runtime CSS theme.
  Audit remains at 23 package entries (0 critical, 5 high); see the MFE's detailed triage.
- Generated Learning (`038c8f379a5c280019b03fe38fdda9a4aba2788d`) and Learner Dashboard
  (`28a5e70aead327193fd49337586b22033188fb95`) release/verawood.1 bundles pass with the
  available combined patches. Generated frontend-base site builds pass with the local
  branding fix, Panorama, LET, progress, s3scorm and webhooks enabled. Remaining site
  warnings are upstream missing source maps and bundle sizes, not missing exports.
- Tutor wheel/sdist build and disposable wheel installation pass. Compose configuration
  validation passes for all 16 fully rendered mode/MFE/Fluent Bit combinations;
  all six generated Kubernetes YAML files parse. Installed-wheel checks confirm that
  disabling Panorama removes its image source stage and both navigation registrations.
  Kubernetes server-side schema validation/full Kustomize assembly was not performed.
  No services were started through Tutor.

## Not completed locally / staging gates

- Full final `openedx`, `mfe`, extractor and collector image assembly from reviewed
  source overrides; installed LMS plugin discovery, URL inclusion, migrations/init/upgrade,
  final LMS `pip check`, session/JWT behavior and both runtime configuration endpoints.
- Browser theme switching, deep links, default/optional shell apps, real QuickSight
  dashboard/console behavior and dataset-side student/tenant isolation. URL parameters
  are not an authorization boundary.
- Actual MySQL 8.4.11/MongoDB 7.0.39 schema/auth/topology checks, Athena/S3 end-to-end
  extraction, incremental/stale partitions and consumer counts/CSV comparisons.
- Kubernetes API metadata/RBAC runtime, collector rotation/restart with pending uploads,
  prolonged S3 outage/recovery, spool exhaustion/node loss, duplicate/missing events and
  arm64 execution. Replay tests do not establish production delivery guarantees.
- The event parser preserves brace-delimited payload text; it does not validate arbitrary
  JSON syntax. Malformed payload monitoring remains part of the staging consumer check.

Local artifacts/logs are under `/private/tmp/panorama-upgrade.cNZ9yv`, backend/extractor
artifacts under `/tmp/panorama-{backend,extractor}-verawood-dist`. These temporary paths
are diagnostic evidence, not release artifacts to deploy.
