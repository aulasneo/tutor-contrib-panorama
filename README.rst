Panorama Tutor Plugin
=====================

Introduction
------------

`Panorama`_ is the analytics solution developed by
`Aulasneo <https://www.aulasneo.com>`_ for Open edX.
It is a complete stack that includes data extraction, load, transformation, 
visualization and analysis. The data extracted is used to build a datalake that can easily
combine multiple LMS installations and even other sources of data.

This utility is in charge of connecting to the MySQL and MongoDB tables and extracting 
the most relevant tables. Then it uploads the data to the datalake and updates all tables and partition.

.. image:: https://img.shields.io/badge/linting-pylint-yellowgreen
    :target: https://github.com/pylint-dev/pylint


Installation
------------

1. Install as a Tutor plugin:

.. code-block::

    pip install tutor-contrib-panorama

2. Enable the plugin

.. code-block::

    tutor plugins enable panorama

Panorama Modes
--------------

Starting with version 16.3.0, the Tutor Panorama Plugin now offers three modes to use Panorama:
- DEMO: Full access to the standard Panorama service, with anonymized data
- FREE: Hosted Panorama service for free, with limited functionalities
- SAAS: Hosted Panorama service provided by Aulasneo with most typical
- CUSTOM: Full potentiality of Panorama, in either SaaS modality or self hosted.

Since 16.3.0, the default mode of Panorama is *DEMO*.

Panorama DEMO mode
==================

In DEMO mode you can try the functionality of Panorama with anonymized data.
You will be able to experiment the power of Panorama as you would with your data.
What you will see is the actual Panorama SaaS solution from our production servers, showing the
dashboards offered out-of-the-box to the SAAS mode.

In the DEMO mode, Panorama will not extract any data from your server.

To activate the DEMO mode, just install the plugin, rebuild the `openedx` and the `mfe` images
and restart your deployment. No specific configuration is needed.

.. code-block::

    pip install tutor-contrib-panorama
    tutor plugins enable panorama
    tutor images build openedx
    tutor images build mfe
    tutor {local|k8s} restart

Panorama FREE mode
==================

Panorama FREE mode offers a basic -yet powerful- set of dashboards that you can use for free.
It is part of the Aulasneo SaaS offering.
To get your FREE credentials, please register at `Panorama`_
and send us an email to info@aulasneo.com

In the free mode, only the relational and courseware data is extracted. No logs are processed.
Therefore you will not be able to get statistics about data based on events, like video views,
forum activity or pdf downloads.

The free mode is part of the SaaS offering. Please be aware that data from your instance will be uploaded
to our servers.

To activate the free mode, just install the plugin, rebuild the `openedx` and the `mfe` images
and restart your deployment. No specific configuration is needed. Contact us at info@aulasneo.com to get
the additional settings needed to activate Panorama.

.. code-block::

    pip install tutor-contrib-panorama
    tutor plugins enable panorama
    tutor images build openedx
    tutor images build mfe
    tutor {local|k8s} restart


Panorama SaaS mode
==================

Panorama SaaS mode offers a full set of dashboards that you can use out of the box. This is a paid service offered by
Aulasneo to any Open edX user.

Please be aware that data from your instance will be uploaded to our servers.

To connect to Panorama SaaS, please contact us at info@aulasneo.com to get instructions.

.. code-block::

    pip install tutor-contrib-panorama
    tutor plugins enable panorama
    tutor images build openedx
    tutor images build mfe
    tutor {local|k8s} restart


Panorama Custom mode
====================

The Panorama custom mode offers the highest flexibility to use Panorama. To set up the custom mode, you will have to
deploy your own data infrastructure.


Setting up the datalake
-----------------------

The Panorama plugin for Tutor is configured to work with a AWS datalake.

To set up your AWS datalake, you will need to:

- create or use an IAM user or role with permissions to access the S3 buckets, KMS if encrypted, Glue and Athena.
- create one S3 bucket to store the data, one for raw logs (optional) and another as the Athena queries results location
- we recommend to use encrypted buckets, and to have strict access policies to prevent unauthorized access
- create the Panorama database in Athena with ``CREATE DATABASE panorama``
- create the Athena workgroup 'panorama' to keep the queries isolated from other projects
- set the 'Query result location' to the bucket created for this workgroup

User permissions to work with AWS datalake
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


In order to work with a AWS datalake, you will need to create a user (e.g. ``panorama-elt``)
and assign a policy (named e.g. ``PanoramaELT``) with at least the following permissions.

Replace **\<panorama_data_bucket>**, **\<panorama_logs_bucket>**, **\<panorama_athena_bucket>**, 
**\<region>** and **\<account id>** with proper values. 

.. code-block:: json

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

If you have encrypted S3 buckets with KMS, you may need to add permissions to get
the KMS keys.

Additionally, the user must have LakeFormation permissions to access the data locations
and query the database and all tables.

Finally, you will have to connect Quicksight to Athena to visualize the data.

Configuration
=============

Set the following variables to configure Panorama

.. csv-table:: Panorama variables
    :header: "Variable", "Default", "Description"

    "PANORAMA_BUCKET", "", "S3 bucket to store the raw data"
    "PANORAMA_MODE", "DEMO", "Panorama mode: DEMO, FREE, SAAS, CUSTOM"
    "PANORAMA_MFE_ENABLED", "True", "Enable the Panorama MFE"
    "PANORAMA_ADD_HEADER_LINK", "False", "Set to True to replace the header of the learning MFE with one that includes a link to Panorama"
    "PANORAMA_DEFAULT_USER_ARN", "arn:aws:quicksight:{{ PANORAMA_REGION }}:{{ PANORAMA_AWS_ACCOUNT_ID }}:user/default/{{ LMS_HOST }}", "Quicksight user to map by default"
    "PANORAMA_ENABLE_STUDENT_VIEW", "True", "Allow students to access the student's panel"
    "PANORAMA_MFE_PORT", "2100", "Internal port of the Panorama MFE"
    "PANORAMA_RAW_LOGS_BUCKET", "PANORAMA_BUCKET", "S3 bucket to store the tracking logs"
    "PANORAMA_CRONTAB", "55 \* \* \* \*", "Crontab entry to update the datasets"
    "PANORAMA_BASE_PREFIX", "openedx", "Directory inside the PANORAMA_BUCKET to store the raw data"
    "PANORAMA_REGION", "us-east-1", "AWS default region"
    "PANORAMA_DATALAKE_DATABASE", "panorama", "Name of the AWS Athena database"
    "PANORAMA_DATALAKE_WORKGROUP", "panorama", "Name of the AWS Athena workgroup"
    "PANORAMA_AWS_ACCESS_KEY", "OPENEDX_AWS_ACCESS_KEY", "AWS access key"
    "PANORAMA_AWS_SECRET_ACCESS_KEY", "OPENEDX_AWS_SECRET_ACCESS_KEY", "AWS access secret"
    "PANORAMA_USE_SPLIT_MONGO", "True", "Set to false for versions older than Maple"
    "PANORAMA_FLB_LOG_LEVEL", "info", "Set the Fluentbit logging level"
    "PANORAMA_RUN_K8S_FLUENTBIT", "True", "In K8s deployments set to false to disable the Fluentbit daemonset. Leave only one namespace running Fluentbit"
    "PANORAMA_DEBUG", "False", "Set to true to run Panorama ELT in verbose debug mode"
    "PANORAMA_LOGS_TOTAL_FILE_SIZE", "1M", "Change the size of the logfiles before uploading"
    "PANORAMA_LOGS_UPLOAD_TIMEOUT", "15m", "Time before log files are uploaded even if they don't have the size limit"



Datalake directory structure
----------------------------

For each table (or for each field-based partition in each table when enabled), one file in csv format
will be generated and uploaded. The file will have the same name as the table, with '.csv' extension.

Each CSV file will be uploaded to the following directory structure:

.. code-block::

    s3://<bucket>/[<base prefix>/]<table name>/[<base partitions>/][field partitions/]<table name>.csv

Where:

- bucket:
    Bucket name, configured in the ``panorama_raw_data_bucket`` setting.

- base prefix:
    (Optional) subdirectory to hold tables of a same kind of system. E.g.: openedx.
    It can receive files from multiple sources, as long as the table names are the same and share a field structure

- table name:
    Base location of the datalake table. All text files inside this directory must have exactly the same column structure

- base partitions:
    Partitions common to a same installation, in Hive format.
    These are not based on fields in the data sources, but will appear as fileds in the datalake.
    For multiple Open edX installations, the default is to use 'lms' as field name and the LMS_HOST as the value, which is the LMS url.
    E.g.: 'lms=openedx.example.com'

- field partitions:
    (Optional) For large tables, it's possible to split the datasource in multiple csv files.
    The field will be removed from the csv file, but will appear as a partition field in the datalake.
    In Open edX installations, the default setting is to partition courseware_studentmodule table by course_id.

License
-------

This software is licenced under Apache 2.0 license. Please see LICENSE for more details.

Contributing
------------

Contributions are welcome! Please submit your PR and we will check it.
For questions, please send an email to <mailto:andres@aulasneo.com>.

.. _Panorama: https://www.aulasneo.com/panorama-analytics/: