# Panorama upgrade plan: Tutor 22 / Open edX Verawood

Originally reviewed 2026-09-08; updated for the current Verawood implementation. This decision record retains the historical review findings and validation baseline below. Packaging and compatibility changes have since landed, including the Panorama prerelease version; publishing and release tagging remain manual steps after testing. See [implementation validation](verawood-validation.md) for the historical implementation checks and outstanding staging gates.

## Recommended approach

Deliver Verawood compatibility first, including native frontend-base navigation contributions. Keep Panorama itself registered as a standalone MFE for that delivery. Then migrate its application entry point to a frontend-base package as a separate, independently testable change.

Verawood supports both architectures. Its instructor dashboard and notifications use frontend-base by default; authn and learner-dashboard apps are optional. This makes navigation compatibility necessary even if Panorama stays an MFE. Panorama does not currently inject an instructor dashboard tab through the retired legacy rendering filter, so that particular migration does not apply. [Verawood release notes](https://docs.openedx.org/en/latest/community/release_notes/verawood/dev_op_release_notes.html#frontend-base).

## Baseline and boundaries

Historical review repositories and commits (not the current artifact provenance):

| Repository | Commit | Relevant existing state |
| --- | --- | --- |
| tutor-contrib-panorama | `01a6e49` | Uncommitted Hatch/PEP 621 migration already targets Tutor 22; CHANGELOG edits and requirements file deletions also pre-exist this review |
| frontend-app-panorama | `da6c90f` | Existing `.gitignore` change; standalone React MFE |
| panorama-openedx-backend | `927c51e` | Django 5.2 application; Boto3 pinned to 1.40.62 |
| panorama-extract-load | `d5c4bc8` | Standalone Python package; runtime lock generated on Python 3.12 |
| Local edx-platform | `259473c5df` | Clean `release/verawood` checkout, dated 2026-08-11 |

Upstream checks use Tutor/tutor-mfe `v22.0.0` and edx-platform `release/verawood.1`, the release reference configured by that Tutor version. The shared backend dependency versions below agree with the local platform checkout. Recheck the exact deployment patch release before implementation; a moving `main` branch is not the compatibility baseline.

The original review used isolated diagnostic environments and did not change production configuration, AWS resources or Kubernetes objects. The current tree includes subsequent package metadata, source-reference, dependency and Panorama version changes; the original review does not validate those later artifacts. The existing extractor `venv` is Python 3.8.6 and is unsuitable for the package's declared Python >=3.11; tests used an isolated Python 3.12 environment instead.

## 1. Tutor installation and integration

Primary files: [pyproject.toml](../pyproject.toml), [plugin.py](../tutorpanorama/plugin.py), and [patches](../tutorpanorama/patches).

1. The Hatch/PEP 621 migration is complete: `setup.py` has been removed and `pyproject.toml` declares Tutor/tutor-mfe 22 compatibility. Historical validation covered wheel/sdist contents, entry-point discovery and packaged templates, patches and plugin-slot files, plus a disposable wheel installation under Tutor 22. Repeat packaging checks for the artifact selected for release.
2. Configure the backend PyPI version and MFE/extractor Git references for testing. Current defaults are backend `22.0.0`, MFE `release/verawood/v20260926`, and extractor `v1.0.1`. Local edits alone do not change what Docker builds install; use a reviewed published backend version and explicit source overrides or mounted MFE sources during validation. Leave publishing and tags for the user's manual release step.
3. Fix `mfe-lms-production-settings`: it currently generates an `http://` Panorama link on an HTTPS deployment. Derive the scheme from Tutor's HTTPS setting. Preserve port 2100 for standalone development.
4. Fix the legacy navigation imports: generated `env.config.jsx` calls `useContext(AppContext)` but imports neither name. Both missing imports were confirmed in configuration rendered with Tutor 22. A standalone Panorama build does not exercise this generated file.
5. Apply `PANORAMA_MFE_ENABLED` consistently. Currently it gates backend installation, but `_add_panorama_mfes` registers Panorama unconditionally and the LMS init task still requests backend migrations in SAAS/CUSTOM mode. Gate the app, navigation, configuration, and migration task together while retaining any separately enabled ingestion behavior. Replace initialization-time `makemigrations` with committed, reviewed migrations; initialization should only apply them.
6. Fix CronJob operational controls: use `concurrencyPolicy: Forbid`, bounded retries/history/deadline appropriate to the schedule, and the configured memory requests/limits. Currently memory settings affect the one-off Job but not the recurring CronJob. Overlapping runs can overwrite the same S3 partition files out of order.
7. Keep one enabled Fluent Bit DaemonSet deployment per cluster, collecting `lms*.log` across all site namespaces and excluding `lms-worker*.log`. Matching sidecar files remain included. Scope only state directories and cluster RBAC resource names to the collector installation; namespace-specific names do not restrict permissions or input. Remove the old global RBAC objects after validating the replacement binding, following the [README migration steps](../README.md#configuration).

Acceptance: render all four modes with MFE enabled/disabled and Fluent Bit enabled/disabled; validate Compose/Kubernetes output and build the actual generated MFE configuration. Test install/init/upgrade using the built plugin artifact in a disposable Tutor root.

## 2. MFE dependencies and frontend-base

### Standalone Verawood compatibility

The [Verawood learning MFE manifest](https://github.com/openedx/frontend-app-learning/blob/release/verawood/package.json) provides a useful reference for shared packages. Panorama already uses compatible React 18, Router 6, Paragon 23, and frontend-build 14 families. Its lockfile is more current than several minimum ranges in `package.json`.

| Dependency | Panorama manifest / resolved lock | Planned alignment |
| --- | --- | --- |
| Node | `>=24`; `.nvmrc` 24 | Keep Node 24 in development, CI, and Tutor image builds |
| frontend-platform | `^8.4.0` / 8.7.0 | Raise minimum to the tested Verawood baseline, `^8.7.0` |
| frontend-component-header | `^8.0.0` / 8.1.0 | Test `^8.2.1`, matching the reference MFE |
| frontend-component-footer | `^14.6.0` / 14.9.5 | Retain compatible 14.x; verify navigation and peer dependencies |
| frontend-build | `^14.6.2` / 14.6.6 | Raise minimum to `^14.6.6`; review transitive security updates |
| browserslist-config | 1.5.0 | Align to 1.5.1 and refresh browser data |
| React / React DOM | 18.3.1 | Retain paired React 18 versions |
| React Router / DOM | 6.30.4 | Retain compatible Router 6; do not downgrade to the reference app's older pin |
| Paragon | `^23.4.5` / 23.22.0 | Keep compatible 23.x and verify theme output |
| frontend-plugin-framework | `^1.7.0` / 1.8.0 | Keep while using the standalone MFE |
| QuickSight embedding SDK | `^2.6.0` / 2.11.3 | Review updates within SDK 2.x against dashboard and console behavior |

Regenerate and review `package-lock.json` with Node 24, then run a clean `npm ci`. Keep React/MUI/Emotion/i18next upgrades scoped to demonstrated compatibility or security needs. Audit unused direct dependencies before removing them; do not remove a package needed to satisfy an upstream peer dependency.

The current lockfile's npm audit reports 38 affected package entries: 1 critical, 15 high, 19 moderate, 3 low. These include transitive/metavulnerability entries, not 38 demonstrated production exploits. The critical `websocket-driver` path runs through development tooling (`webpack-dev-server`/SockJS). Triage runtime versus build/dev exposure, refresh compatible transitive dependencies, and review hard overrides such as `shell-quote` individually. Automated suggestions include incompatible downgrades and Router major upgrades; do not apply `npm audit fix --force` wholesale. Review `i18next-http-backend`, QuickSight SDK, and remaining upstream advisories explicitly.

Functional changes to include: handle failure of the independent role request in `Embed.jsx`; make access-denied and expired-session states explicit; test unmount/remount and dashboard switching during asynchronous QuickSight initialization. Replace the empty example test with real route, role, error, and embedding tests. The build currently emits a large vendor bundle and duplicate-looking core theme assets; investigate theme ownership and lazy loading, particularly when moving into the shell.

### Navigation on frontend-base sites

Keep the existing `PLUGIN_SLOTS` contributions for standalone MFEs. Add native contributions using `FRONTEND_SLOTS` and the `mfe-site-custom-app-imports`/`mfe-site-custom-app-final` patches. Tutor 22 does not automatically translate existing slot registrations into the shell. [Tutor-mfe v22 documentation](https://github.com/overhangio/tutor-mfe/blob/v22.0.0/README.rst#using-frontend-slots).

The Tutor 22.0.0 site lock resolves frontend-base 1.0.1. Its native target slots are:

| Panorama contribution | Native frontend-base target |
| --- | --- |
| Desktop secondary link | `org.openedx.frontend.slot.header.secondaryLinks.v1` |
| Mobile menu link | `org.openedx.frontend.slot.header.mobileMenuLinks.v1` |

These IDs are verified in [SecondaryNavLinks](https://github.com/openedx/frontend-base/blob/v1.0.1/shell/header/desktop/SecondaryNavLinks.tsx) and [MobileNavLinks](https://github.com/openedx/frontend-base/blob/v1.0.1/shell/header/mobile/MobileNavLinks.tsx). Read runtime configuration and authentication through frontend-base APIs and make desktop/mobile visibility consistent with the backend's actual access policy. Panorama roles must not be inferred from the frontend's `administrator` flag alone.

Verify custom config through `/api/frontend_site_config/v1/` and the existing MFE config endpoint. Native frontend-base configuration takes precedence where explicitly set; avoid overwriting customer database/site overrides accidentally. Test both default Verawood apps and the optional authn/learner-dashboard apps.

The compat shim is an alternative transition mechanism, but native contributions are small enough here to avoid depending on legacy widget mutation mappings. Do not register both native and compat contributions for the same link.

### Separate application migration

Convert Panorama from a document-owning SPA into a package exporting a frontend-base `App`. Replace `initialize`, subscriptions, `createRoot`, `AppProvider`, and locally rendered Header/Footer with shell lifecycle, route registration, authentication/config APIs, and `/panorama` route ownership. Preserve `/panorama/panels`, refresh/deep-link behavior, locale assets, and authenticated backend requests.

Replace frontend-platform/build/header/footer/plugin-framework dependencies with frontend-base. Shared React, Router, Paragon, and frontend-base dependencies become peers. For the reviewed frontend-base 1.0.1, peer families include React 18.3.1, Router >=6.26.1 within 6.x, and Paragon >=23.20 within 23.x. Add package exports, distributable assets, and both library and assembled-site builds. Register via `FRONTEND_APPS` and Tutor's site-config patches; Git `source` support permits testing without publishing or bumping Panorama's npm version. [Migration guide](https://github.com/openedx/frontend-base/blob/main/docs/how_tos/migrate-frontend-app.md), [Tutor custom frontend apps](https://github.com/overhangio/tutor-mfe/blob/v22.0.0/README.rst#frontend-apps).

Scope CSS to Panorama and replace viewport calculations that assume a fixed 161px header/footer. Consolidate i18next asset loading with the shell's locale/translation model. The finished package must mount without creating a second router, root, header, or footer.

## 3. Django backend alignment and review

Use Python 3.12 and Django 5.2 in the Verawood test target. There is no Django major-version migration required from the backend's current 5.2 constraint.

| Shared dependency | Backend lock | Verawood platform baseline |
| --- | --- | --- |
| Django | 5.2.11 | 5.2.13 |
| django-model-utils | 5.0.0 | 5.0.0 |
| Django REST framework | 3.16.1 | 3.17.1 |
| Boto3 / Botocore | 1.40.62 | 1.42.97 |
| s3transfer | 0.14.0 | 0.16.1 |
| requests | 2.33.1 | 2.33.1 |
| openedx-atlas | 0.7.0 | 0.7.0 |
| urllib3 | 2.5.0 | 2.6.3 |

Source: [edx-platform release/verawood.1 requirements](https://github.com/openedx/edx-platform/blob/release/verawood.1/requirements/edx/base.txt). These are compatibility constraints for the reviewed platform, not claims that they are the newest security releases.

Remove the backend's strict `boto3==1.40.62` installation requirement in favor of a tested compatible range that admits Verawood's version. Otherwise the plugin's post-requirements `pip install` can downgrade the LMS's shared AWS SDK stack. Install/test against constraints from the exact target platform, compile the backend's development/test locks together, and run `pip check` inside the final LMS image. Avoid forcing an unrelated newer SDK into edx-platform. Keep Django `<5.3` until another line is deliberately supported; `requests>=2.33.0` already admits the platform pin. Update stale Ulmo comments and the Python 3.11-only tox/CI target.

Code review findings to address before release:

| Priority | Location | Finding and required behavior |
| --- | --- | --- |
| High | `views.py`: `GetDashboardEmbedUrl`, `GetStudioEmbedUrl` | Both require authentication but do not enforce `has_access_to_panorama`; console generation also lacks an AUTHOR check. Reject unauthorized direct API calls before external requests. A hidden UI button is insufficient. Actual AWS impact depends on the configured/default QuickSight principal. |
| High, validation required | `models.py`: student dashboard help; `views.py`: fragment parameters | Student filtering is controlled through client-visible parameters. Verify dataset-side isolation with tampered userId/lms values and distinct students; the review cannot establish deployed QuickSight data isolation from these repositories. |
| Medium | `views.py`: HTTPError handler | `HTTPError.response` can be `None`; checking only `hasattr` then reading `status_code` can cause another exception. Handle missing responses, timeouts, malformed upstream JSON, and SDK failures consistently. |
| Medium | `views.py`: unsupported-mode branch | Returns HTTP 200 with an error envelope and interpolates the function instead of the resolved mode. Return a proper error response with the actual mode. |
| Medium | `models.py`: role default | Default `Reader` is not one of the defined uppercase choices. Change to `READER`, inspect existing rows, and make any correction an explicit migration. |

Retain Panorama's existing mode/role semantics. Verawood's course-authoring RBAC does not automatically replace Panorama's dashboard grants. Test LMS plugin discovery, URL inclusion, settings, migrations, session/JWT authentication, profile-name lookup, and registered-user embedding inside the target edx-platform image.

## 4. Extractor dependencies and generic review

The extractor is a separate container: it does not need the LMS's Boto3 or PyMongo pins. Keep its dependencies independently resolved and verify its database protocols against Tutor 22's MySQL 8.4 and MongoDB 7 defaults. The platform's split-modulestore course index still contains the fields used by this extractor; this is source compatibility evidence, not a full database-schema verification.

| Package | Current lock | Registry candidate checked 2026-09-08 |
| --- | --- | --- |
| Boto3 | 1.43.22 | 1.43.89; resolve matching Botocore/s3transfer together |
| PyMongo | 4.17.0 | 4.18.0 |
| PyMySQL | 1.2.0 | 1.2.0 |
| cryptography | 48.0.1 | 50.0.1; review major-version compatibility before selection |
| Click | 8.4.1 | 8.5.0 |
| openpyxl | 3.1.5 | 3.1.5 |

Candidates come from each package's PyPI JSON metadata and are not tested upgrade pins. Recompile with Python 3.12, review package release notes/advisories, and run the suite against the resulting lock. The runtime-lock audit flags `cryptography==48.0.1`; treat its security update as required dependency work, with exploitability assessed against the application's use. Retain direct `botocore` because application code imports it; audit apparently transitive entries (`jmespath`, `s3transfer`, `six`, `urllib3`, `python-dateutil`) before removing them from `requirements.in`. Keep MySQL authentication dependencies explicit, for example through the appropriate PyMySQL extra if adopted.

Align Tutor's Python 3.11 extractor Dockerfile with the standalone Python 3.12 Dockerfile, or deliberately test/support both. Tutor currently clones `panorama-elt` and runs `/panorama-elt/panorama.py`; the standalone image installs the package and uses `panorama-elt` from `/app`. Unify the build recipe or verify both entry points, working directories, views/assets, and dependencies. Preserve local cron support when changing the image.

Code review work, in priority order:

1. **Remove database passwords from debug logs.** `CourseStructuresDatasource.__init__` logs both MongoDB and MySQL passwords when debug logging is enabled. Test logs with sentinel credentials.
2. **Report partial failures to Kubernetes.** MySQL extraction catches table errors, skips tables, and finishes successfully; Athena submission errors are logged and swallowed. `_extract_and_load` never checks completion of partition-update queries. Collect failures, finish any deliberately independent work, and exit nonzero for incomplete required extraction/partition updates. Bound Athena polling and report failed/cancelled/timed-out queries with reasons.
3. **Make invalid selections fail.** CLI invalid-option combinations print messages and return successfully; unknown datasource/table selectors can do no work. Validate configuration structure and selected names before connecting or uploading.
4. **Stream exports and close connections.** MySQL uses buffered `fetchall`, then `save_rows` duplicates the rows in another list. Use bounded fetching/streaming, temporary files with deterministic cleanup, and close database clients. Excel export also materializes whole datasets.
5. **Correct falsy-value handling.** SQL constant generation treats `0`, `False`, and empty strings as NULL; course problem weight `0` triggers weight inference. Distinguish missing values from legitimate zero values and add regression fixtures.
6. **Avoid mutating field configuration.** Partition extraction removes fields from the list returned by `get_fields`, which can be the datasource's cached list. Copy before modification so repeated runs in one process are safe.
7. **Harden queries and metadata checks.** Parameterize data values, validate/quote configured identifiers, handle apostrophes and NULL partition values, normalize non-string partition values, and test the CSV/Athena escaping contract before removing old escaping workarounds. Mongo `get_collection` alone does not establish connectivity; use an actual read/ping. Review `directConnection=True` for replica-set deployments.
8. **Handle incomplete course structures explicitly.** Missing definitions currently use cursor index `[0]`; failures and absent structures can cause crashes or incomplete snapshots. Define whether to fail the snapshot or report a partial result; avoid silently publishing an apparently complete export.

Before staging, compare every configured source table/column to the migrated Verawood database, including optional enterprise tables. Test incremental refreshes, zero-row results, published/unpublished courses, problem weights, Unicode, multiline text, credentials with special characters, replica-set topology, and deletion/stale-partition behavior. Preserve the existing datalake CSV/schema and S3 partition contracts unless a separately planned migration is required.

## 5. Fluent Bit image and configuration

Upgrade candidate: `public.ecr.aws/aws-observability/aws-for-fluent-bit:3.4.15`, then pin the verified image digest. The current image is from October 2024. The candidate uses Amazon Linux 2023, and its release line incorporates Fluent Bit 5.0.9. AWS's `stable` marker still resolves to a 2.x tag at review time, so a floating `stable`/`latest` tag would not express the intended major-version migration. [AWS image changelog](https://github.com/aws/aws-for-fluent-bit/blob/mainline/CHANGELOG.md).

In the logs Dockerfile, remove the AWS CLI download/install and build-time `aws configure` after confirming no downstream patch invokes the CLI. No supplied runtime template invokes it; the S3 output already has an explicit region. This also removes the hard-coded x86_64 CLI dependency. Prefer the maintained base image over an unpinned OS-wide `yum update`; if additional packages are necessary, use the AL2023-compatible package manager and explicit requirements. Preserve the user's image label/project versions.

Configuration changes:

1. Replace `Parser docker`, `Docker_Mode`, and `Docker_Mode_Flush` with `multiline.parser docker, cri` for Kubernetes container logs. Retain the plain-file path in `fluent-bit-local.conf`. Remove the custom Docker parser only once no input refers to it. Verify full and partial CRI records and Docker split records. [Tail input documentation](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail).
2. Preserve cluster-wide `lms*.log` input and the `lms-worker*.log` exclusion, without restricting the namespace or container-name suffix. Enable the collector in exactly one site; all collected logs use that site's bucket and credentials. Keep tags compatible with Kubernetes metadata lookup: `$TAG[1]` split on `_` identifies the source namespace, whereas Compose uses LMS-host-based prefixes. Preserve those consumer paths during the upgrade.
3. Retain tracking-event selection: Tutor 22 still configures the standard console formatter with `[tracking]`, so the current tracking regex is not inherently obsolete. Tighten/test the event parser against actual rendered LMS logs, CR/LF endings, braces in metadata, malformed JSON, and ordinary application logs. Preserve raw event JSON for `log_key event` and correct the obsolete comment claiming a `date` capture exists.
4. Add a persistent writable S3 `store_dir` and a bounded `store_dir_limit_size`, separately from the tail offset DB. Currently the offset DB lives on the host but S3 buffering defaults to container storage, so a restart can discard buffered records after offsets have advanced. Document and test spool-limit data loss and node-loss behavior; a hostPath only survives pod restarts on the same node. [S3 output buffering](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3).
5. Budget memory with headroom: `Mem_Buf_Limit 256MB` currently consumes the same scale as the pod's total 256Mi limit, before parser/metadata/output overhead. Bound Kubernetes metadata responses instead of `Buffer_Size 0`; measure realistic log volumes and tune multiline/line limits.
6. Define oversized-record handling deliberately. `Skip_Long_Lines Off` plus a 256k cap can stop monitoring a file after an oversized record. Test both a large event and a subsequent valid event; choose an observable skip/quarantine policy or adequately sized buffers. No setting should promise lossless collection without tested limits.
7. Keep gzip and PutObject semantics initially. `upload_chunk_size` applies to multipart uploads, so it is misleading with `use_put_object On`; remove it from that active path or make upload mode explicit. Add S3 object-arrival/backlog checks; generic Fluent Bit output-success metrics do not establish S3 delivery. [S3 output options](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3).
8. Apply persistence and restart verification to Compose as well. Its tail input currently has no offset DB. Render `[SERVICE] Log_Level` from `PANORAMA_FLB_LOG_LEVEL` rather than relying on an unreferenced environment variable.

Acceptance: validate the new binary's configuration; replay Docker/CRI/local fixtures to stdout; verify gzip NDJSON and exact S3 keys in a test sink; test rotation, collector restart with pending uploads, S3 outage/recovery, duplicate/missing event detection, cross-namespace routing and collector-state isolation, and each supported CPU architecture. Canary the collector with a separate test prefix to avoid duplicate production ingestion.

## Historical review checks (2026-09-08, before implementation)

| Check | Result | Limit |
| --- | --- | --- |
| Tutor 22.0.0 + tutor-mfe 22.0.0 plugin import | Passed | Does not execute browser components |
| Plugin wheel install and CUSTOM-mode configuration render | Passed | Found missing navigation imports and HTTP URL in generated output; no deployment |
| Backend pytest | 4 passed | Existing Python 3.12 venv, mocked AWS and SQLite; not a target-platform integration test |
| Extractor pytest | 98 passed | Isolated Python 3.12 with existing runtime lock; external services mocked |
| MFE lint | Passed | Existing node_modules, Node 24.17.0 |
| MFE test | 1 passed | Empty template test, no functional assurance |
| MFE production build | Passed with size/theme/browser-data warnings | Existing lock-matching core dependencies; no generated Tutor navigation or shell integration |
| npm audit | 38 affected entries | Needs exposure-aware triage and post-upgrade rerun |
| Extractor runtime `pip-audit` | Flags cryptography 48.0.1: three distinct advisory IDs after deduplication | Two list a fix in 49.0.0; `PYSEC-2026-3552` lists 50.0.0. Test candidate 50.0.1; application exploitability remains unassessed |

## Delivery sequence and release gates

1. Finish Tutor packaging/source-override work and establish reproducible target constraints.
2. Update backend dependencies and fix access/error handling with meaningful negative tests.
3. Update extractor dependencies, failure semantics, credential logging, and container runtime.
4. Upgrade Fluent Bit and validate parsing, persistence, routing, and resource controls.
5. Refresh the standalone MFE and add native shell navigation; validate all four Panorama modes and role/student-view combinations.
6. Build `openedx`, `mfe`, and both Panorama images from the exact reviewed sources. In staging, run migrations/checks, login and role tests, dashboard/console embedding, scheduled extraction, S3/Athena data comparisons, and collector outage/restart tests. Confirm the student isolation check before accepting student dashboards.
7. Record image digests, source commits, dependency locks, config, export counts, and freshness. Observe at least a full extraction cycle and the longest upload timeout; include a scheduled-job failure/retry test. Retain prior image digests and database backups. Roll back application/collector changes with their matching configuration; an Open edX database rollback requires a compatible backup and is not just an image rollback. Drain pending log buffers before collector replacement.
8. Perform the full Panorama frontend-base app conversion as a separately validated follow-up, unless it is explicitly chosen as a prerequisite for this release.
9. Update repository READMEs and the workspace architecture/mode documentation as implementation lands. The user bumps versions and creates release tags after testing; this plan does not authorize publishing or deployment.
