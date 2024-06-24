# Change log

## Version 16.3.1 (2024-06-24)
- Install backend from pypi

## Version 16.3.0 (2024-06-05)
- Panorama new experience: introducing DEMO, FREE, SAAS and CUSTOM modes
- Integration into Open edX via the Panorama MFE

## Version 16.2.3 (2024-05-03)
- Fix a bug causing an error when db password is all numeric

## Version 16.2.2 (2024-03-04)
- Upgraded panorama-elt to 0.3.1

## Version 16.2.1 (2024-02-19)
- Fixed plugin load priority

## Version 16.2.0 (2024-02-19)
- Fixed call to init task

## Version 16.1.0 (2023-12-19)
- Upgrade Fluentbit to 2.32.0

## Version 16.0.0 (2023-11-17)
- Upgrade to Palm

## Version 16.0.1 (2023-12-01)
- Fix wrong default raw logs bucket

## Version 14.1.1 (2023-10-06)
- Fix: Set weight field type as double

## Version 14.1.0 (2023-09-26)
- Add problem weight to course structures

## Version 14.0.2 (2023-09-04)
- Use panorama-elt 0.2.4. Fix bug with course re-runs

## Version 14.0.1 (2023-07-17)
- Add support for tracking logs in Tutor local installations
- Update versioning numbers to match Tutor versioning

## Version 0.4.10 (2023-07-17)
- Fix crontab in local docker image

## Version 0.4.9 (2023-06-24)
- Use panorama-elt 0.2.3. Fix bug that skipped the first course in the db

## Version 0.4.8 (2023-04-26)
- Use variables to set docker image names

## Version 0.4.2 (2023-04-17)
- Add enterprise_pendingenterprisecustomeruser

## Version 0.4.1 (2023-04-14)
- Add enterprise_enterprisecustomer and enterprise_enterprisecustomeruser tables

## Version 0.4.0 (2023-04-10)
- Add completion_blockcompletion table

## Version 0.3.1 (2023-02-15)
- Fix bug in push hooks that prevented panorama-elt-logs image to be pushed.

## Version 0.3.0 (2023-01-12)
- Added two settings to control when fluentbit uploads log files: PANORAMA_LOGS_TOTAL_FILE_SIZE (default 1M) and 
PANORAMA_LOGS_UPLOAD_TIMEOUT (default 15m). A new file will be uploaded when it exceeds the total file size,
or after the upload timeout, whatever happens first. Increase these values to reduce traffic (and cost)
when uploading to the datalake. Reduce them to have faster updates.

## 0.2.4
- Improved init command in K8s
- Added PANORAMA_DEBUG option (default=False) to have debug logs
- Added PANORAMA_RUN_K8S_FLUENTBIT option (default=True) to skip fluentbit manifests in K8s

## 0.2.1
- Add the option PANORAMA_USE_SPLIT_MONGO (default True)
## 0.1.9
- Fix: use PANORAMA_REGION in fluentbit configuration
- Improve fluentbit config
- Add student anonymous user id table
- Add site configuration table
- Add PANORAMA_FLB_LOG_LEVEL to set fluent-bit logging level (default: info). 
Set to 'debug' to debug fluentbit.
- Use the aws credentials configured for Panorama, for fluentbit
## 0.1.8
- Fixed a bug in panorama-elt
## 0.1.7
- Enable image building. 
- Create datalake tables and views in the init routine
- Improve readme.
## 0.0.1
- Initial release
