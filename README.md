# Panorama Tutor Plugin

## Introduction

[Panorama](https://www.aulasneo.com/panorama-analytics/) is the analytics
solution developed by [Aulasneo](https://www.aulasneo.com) for Open edX. It is
a complete stack that includes data extraction, load, transformation,
visualization and analysis. The data extracted is used to build a datalake
that can easily combine multiple LMS installations and even other sources of
data.

This utility is in charge of connecting to the MySQL and MongoDB tables and
extracting the most relevant tables. Then it uploads the data to the datalake
and updates all tables and partitions.

[![Linting](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)

## Installation

1. Install as a Tutor plugin:

   ```text
   pip install tutor-contrib-panorama
   ```

2. Enable the plugin:

   ```text
   tutor plugins enable panorama
   ```

## Panorama Modes

Starting with version 16.3.0, the Tutor Panorama Plugin now offers four modes
to use Panorama:

- `DEMO`: Full access to the standard Panorama service, with anonymized data.
- `FREE`: Hosted Panorama service for free, with limited functionalities.
- `SAAS`: Hosted Panorama service provided by Aulasneo with most typical
  features enabled.
- `CUSTOM`: Full Panorama flexibility, either in SaaS modality or self-hosted.

Since 16.3.0, the default mode of Panorama is `DEMO`.

### Panorama DEMO Mode

In DEMO mode you can try the functionality of Panorama with anonymized data.
You will be able to experiment with the power of Panorama as you would with
your own data. What you will see is the actual Panorama SaaS solution from our
production servers, showing the dashboards offered out of the box for the
`SAAS` mode.

In `DEMO` mode, Panorama will not extract any data from your server.

To activate `DEMO` mode, install the plugin, rebuild the `openedx` and `mfe`
images, and restart your deployment. No specific configuration is needed.

```text
pip install tutor-contrib-panorama
tutor plugins enable panorama
tutor images build openedx
tutor images build mfe
tutor {local|k8s} restart
```

### Panorama FREE Mode

Panorama `FREE` mode offers a basic yet powerful set of dashboards that you can
use for free. It is part of the Aulasneo SaaS offering. To get your `FREE`
credentials, please register at
[Panorama](https://www.aulasneo.com/panorama-analytics/) and send us an email
to <info@aulasneo.com>.

In `FREE` mode, only the relational and courseware data is extracted. No logs
are processed. Therefore you will not be able to get statistics based on
events, such as video views, forum activity, or PDF downloads.

The free mode is part of the SaaS offering. Please be aware that data from your
instance will be uploaded to our servers.

To activate `FREE` mode, install the plugin, rebuild the `openedx` and `mfe`
images, and restart your deployment. No specific configuration is needed.
Contact us at <info@aulasneo.com> to get the additional settings needed to
activate Panorama.

```text
pip install tutor-contrib-panorama
tutor plugins enable panorama
tutor images build openedx
tutor images build mfe
tutor {local|k8s} restart
```

### Panorama SaaS Mode

Panorama `SAAS` mode offers a full set of dashboards that you can use out of
the box. This is a paid service offered by Aulasneo to any Open edX user.

Please be aware that data from your instance will be uploaded to our servers.

To connect to Panorama SaaS, please contact us at <info@aulasneo.com> to get
instructions.

```text
pip install tutor-contrib-panorama
tutor plugins enable panorama
tutor images build openedx
tutor images build mfe
tutor {local|k8s} restart
```

### Panorama Custom Mode

The Panorama `CUSTOM` mode offers the highest flexibility to use Panorama. To
set up custom mode, you will have to deploy your own data infrastructure.

#### Setting Up the Datalake

The Panorama plugin for Tutor is configured to work with an AWS datalake.

To set up your AWS datalake, you will need to:

- Create or use an IAM user or role with permissions to access the S3 buckets,
  KMS if encrypted, Glue, and Athena.
- Create one S3 bucket to store the data, one for raw logs (optional), and
  another as the Athena query results location.
- Use encrypted buckets and strict access policies to prevent unauthorized
  access.
- Create the Panorama database in Athena with `CREATE DATABASE panorama`.
- Create the Athena workgroup `panorama` to keep the queries isolated from
  other projects.
- Set the query result location to the bucket created for this workgroup.

##### User Permissions to Work With the AWS Datalake

In order to work with an AWS datalake, you will need to create a user, for
example `panorama-elt`, and assign a policy, for example `PanoramaELT`, with at
least the following permissions.

Replace `<panorama_data_bucket>`, `<panorama_logs_bucket>`,
`<panorama_athena_bucket>`, `<region>`, and `<account_id>` with proper values.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": [
        "arn:aws:s3:::<panorama_data_bucket>/openedx/*",
        "arn:aws:s3:::<panorama_logs_bucket>/tracking_logs/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::<panorama_data_bucket>/PanoramaConnectionTest"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketLocation",
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::<panorama_athena_bucket>",
        "arn:aws:s3:::<panorama_athena_bucket>/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:BatchCreatePartition",
        "glue:GetDatabase",
        "athena:StartQueryExecution",
        "glue:CreateTable",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "glue:GetDatabases",
        "glue:GetTable",
        "glue:DeleteTable",
        "glue:GetPartitions",
        "glue:UpdateTable"
      ],
      "Resource": [
        "arn:aws:athena:<region>:<account_id>:workgroup/panorama",
        "arn:aws:glue:<region>:<account_id>:database/panorama",
        "arn:aws:glue:<region>:<account_id>:catalog",
        "arn:aws:glue:<region>:<account_id>:table/panorama/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:GenerateDataKey",
        "kms:Decrypt"
      ],
      "Resource": "*"
    }
  ]
}
```

If you have encrypted S3 buckets with KMS, you may need to add permissions to
get the KMS keys.

Additionally, the user must have Lake Formation permissions to access the data
locations and query the database and all tables.

Finally, you will have to connect QuickSight to Athena to visualize the data.

## Configuration

Set the following variables to configure Panorama:

| Variable | Default | Description |
| --- | --- | --- |
| `PANORAMA_BUCKET` |  | S3 bucket to store the raw data |
| `PANORAMA_MODE` | `DEMO` | Panorama mode: `DEMO`, `FREE`, `SAAS`, `CUSTOM` |
| `PANORAMA_MFE_ENABLED` | `True` | Enable the Panorama MFE |
| `PANORAMA_DEFAULT_USER_ARN` | `arn:aws:quicksight:{{ PANORAMA_REGION }}:{{ PANORAMA_AWS_ACCOUNT_ID }}:user/default/{{ LMS_HOST }}` | QuickSight user to map by default |
| `PANORAMA_ENABLE_STUDENT_VIEW` | `True` | Allow students to access the student's panel |
| `PANORAMA_MFE_PORT` | `2100` | Internal port of the Panorama MFE |
| `PANORAMA_RAW_LOGS_BUCKET` | `PANORAMA_BUCKET` | S3 bucket to store the tracking logs |
| `PANORAMA_CRONTAB` | `55 * * * *` | Crontab entry to update the datasets |
| `PANORAMA_BASE_PREFIX` | `openedx` | Directory inside the `PANORAMA_BUCKET` to store the raw data |
| `PANORAMA_REGION` | `us-east-1` | AWS default region |
| `PANORAMA_DATALAKE_DATABASE` | `panorama` | Name of the AWS Athena database |
| `PANORAMA_DATALAKE_WORKGROUP` | `panorama` | Name of the AWS Athena workgroup |
| `PANORAMA_AWS_ACCESS_KEY` | `OPENEDX_AWS_ACCESS_KEY` | AWS access key |
| `PANORAMA_AWS_SECRET_ACCESS_KEY` | `OPENEDX_AWS_SECRET_ACCESS_KEY` | AWS access secret |
| `PANORAMA_USE_SPLIT_MONGO` | `True` | Set to false for versions older than Maple |
| `PANORAMA_FLB_LOG_LEVEL` | `info` | Set the Fluent Bit logging level |
| `PANORAMA_RUN_K8S_FLUENTBIT` | `True` | In K8s deployments, set to false to disable the Fluent Bit daemonset. Leave only one namespace running Fluent Bit |
| `PANORAMA_DEBUG` | `False` | Set to true to run Panorama ELT in verbose debug mode |
| `PANORAMA_LOGS_TOTAL_FILE_SIZE` | `50M` | Maximum size of log files before uploading to S3 |
| `PANORAMA_LOGS_UPLOAD_TIMEOUT` | `10m` | Maximum time before log files are uploaded even if they don't reach the size limit |
| `PANORAMA_LOGS_UPLOAD_CHUNK_SIZE` | `10M` | Chunk size for multipart uploads to S3 |
| `PANORAMA_K8S_JOB_MEMORY` |  | Memory request for Panorama job in K8s. Use only if you get OOM-killed pods |

## Datalake Directory Structure

For each table, or for each field-based partition in each table when enabled,
one CSV file will be generated and uploaded. The file will have the same name
as the table, with a `.csv` extension.

Each CSV file will be uploaded to the following directory structure:

```text
s3://<bucket>/[<base prefix>/]<table name>/[<base partitions>/][field partitions/]<table name>.csv
```

Where:

- `bucket`: Bucket name, configured in the `panorama_raw_data_bucket` setting.
- `base prefix`: Optional subdirectory to hold tables of the same kind of
  system, for example `openedx`. It can receive files from multiple sources, as
  long as the table names are the same and share a field structure.
- `table name`: Base location of the datalake table. All text files inside this
  directory must have exactly the same column structure.
- `base partitions`: Partitions common to the same installation, in Hive
  format. These are not based on fields in the data sources, but will appear as
  fields in the datalake. For multiple Open edX installations, the default is
  to use `lms` as field name and the LMS host as the value, for example
  `lms=openedx.example.com`.
- `field partitions`: Optional partitioning for large tables. The field will be
  removed from the CSV file, but will appear as a partition field in the
  datalake. In Open edX installations, the default setting is to partition
  `courseware_studentmodule` by `course_id`.

## License

This software is licensed under the Apache 2.0 license. Please see `LICENSE`
for more details.

## Contributing

Contributions are welcome. Please submit your PR and we will review it.
For questions, please send an email to <andres@aulasneo.com>.
