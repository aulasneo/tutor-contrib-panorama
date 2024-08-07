"""
Tutor plugin to enable Panorama in Open edX.
"""
from __future__ import annotations

from glob import glob
import os

import click
import importlib_resources

from tutor import hooks, config as tutor_config
from tutormfe.hooks import MFE_APPS

from .__about__ import __version__

# Version of openedx-backend-version in PyPI

PANORAMA_OPENEDX_BACKEND_VERSION = '16.0.9'

PANORAMA_MFE_REPO = "https://github.com/aulasneo/frontend-app-panorama.git"

# Tag at https://github.com/aulasneo/frontend-app-panorama.git
PANORAMA_MFE_VERSION = 'open-release/redwood.20240729'

# Tag at https://github.com/aulasneo/panorama-elt.git
PANORAMA_ELT_VERSION = 'v0.3.1'

# Tag at https://github.com/aulasneo/frontend-component-header-panorama
PANORAMA_FRONTEND_COMPONENT_HEADER_VERSION = 'panorama/palm/20240529'
PANORAMA_FRONTEND_COMPONENT_HEADER_REPO = 'github:aulasneo/frontend-component-header-panorama'

PANORAMA_MFE_PORT = 2100

# Configuration
config = {
    # Add here your new settings
    "defaults": {
        "VERSION": __version__,
        "CRONTAB": "55 * * * *",
        "BUCKET": "",
        "RAW_LOGS_BUCKET": "{{ PANORAMA_BUCKET }}",
        "BASE_PREFIX": "openedx",
        "AWS_ACCOUNT_ID": "",
        "REGION": "us-east-1",
        "DATALAKE_DATABASE": "panorama",
        "DATALAKE_WORKGROUP": "panorama",
        "AWS_ACCESS_KEY": "{{ OPENEDX_AWS_ACCESS_KEY }}",
        "AWS_SECRET_ACCESS_KEY": "{{ OPENEDX_AWS_SECRET_ACCESS_KEY }}",
        "FLB_LOG_LEVEL": 'info',
        "USE_SPLIT_MONGO": True,
        "RUN_K8S_FLUENTBIT": True,
        "DEBUG": False,
        "LOGS_TOTAL_FILE_SIZE": "1M",
        "LOGS_UPLOAD_TIMEOUT": "15m",
        "DOCKER_IMAGE": "{{ DOCKER_REGISTRY }}aulasneo/panorama-elt:{{ PANORAMA_VERSION }}",
        "LOGS_DOCKER_IMAGE":
            "{{ DOCKER_REGISTRY }}aulasneo/panorama-elt-logs:{{ PANORAMA_VERSION }}",
        "MFE_ENABLED": True,
        "ADD_HEADER_LINK": False,
        "MODE": "DEMO",
        "MFE_PORT": PANORAMA_MFE_PORT,
        "FRONTEND_COMPONENT_HEADER_VERSION": PANORAMA_FRONTEND_COMPONENT_HEADER_VERSION,
        "FRONTEND_COMPONENT_HEADER_REPO": PANORAMA_FRONTEND_COMPONENT_HEADER_REPO,
        "ENABLE_STUDENT_VIEW": True,
        "DEFAULT_USER_ARN":
            "arn:aws:quicksight:{{ PANORAMA_REGION }}:{{ PANORAMA_AWS_ACCOUNT_ID }}:"
            "user/default/{{ LMS_HOST }}",
    },
    # Add here settings that don't have a reasonable default for all users. For
    # instance: passwords, secret keys, etc.
    "unique": {
    },
    # Danger zone! Add here values to override settings from Tutor core or other plugins.
    "overrides": {
    },
}

# Initialization tasks
MY_INIT_TASKS: list[tuple[str, str, int]] = [
    ("panorama", "panorama-elt", hooks.priorities.LOW),
    ("lms", "lms", hooks.priorities.LOW),  # backend migrations
]

# init script
for service, template_path, priority in MY_INIT_TASKS:
    with open(
            str(importlib_resources.files(
                "tutorpanorama") / "templates" / "panorama" / "tasks" / template_path / "init"),
            encoding="utf-8",
    ) as task_file:
        hooks.Filters.CLI_DO_INIT_TASKS.add_item((service, task_file.read()), priority=priority)


# Load all configuration entries
hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        (f"PANORAMA_{key}", value)
        for key, value in config["defaults"].items()
    ]
)
hooks.Filters.CONFIG_UNIQUE.add_items(
    [
        (f"PANORAMA_{key}", value)
        for key, value in config["unique"].items()
    ]
)

hooks.Filters.CONFIG_OVERRIDES.add_items(list(config["overrides"].items()))

# Docker image management
# To build an image with `tutor images build myimage`
hooks.Filters.IMAGES_BUILD.add_items(
    [
        (
            "panorama",
            ("plugins", "panorama", "build", "panorama-elt"),
            "{{ PANORAMA_DOCKER_IMAGE }}",
            (),
        ),
        (
            "panorama",
            ("plugins", "panorama", "build", "panorama-elt-logs"),
            "{{ PANORAMA_LOGS_DOCKER_IMAGE }}",
            (),
        ),
    ]
)

# To pull/push an image with `tutor images pull myimage` and `tutor images push myimage`:
hooks.Filters.IMAGES_PULL.add_items(
    [
        ("panorama", "{{ PANORAMA_DOCKER_IMAGE }}",),
        ("panorama", "{{ PANORAMA_LOGS_DOCKER_IMAGE }}"),
    ]
)
hooks.Filters.IMAGES_PUSH.add_items(
    [
        ("panorama", "{{ PANORAMA_DOCKER_IMAGE }}",),
        ("panorama", "{{ PANORAMA_LOGS_DOCKER_IMAGE }}"),
    ]
)

# Add the "templates" folder as a template root
hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    str(importlib_resources.files("tutorpanorama") / "templates")
)

hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    [
        ("panorama/build", "plugins"),
        ("panorama/apps", "plugins"),
    ],
)


@MFE_APPS.add()
def _add_my_mfe(mfes):
    conf = tutor_config.load('')

    if conf.get("PANORAMA_MFE_ENABLED"):
        mfes["panorama"] = {
            "repository": PANORAMA_MFE_REPO,
            "port": PANORAMA_MFE_PORT,
            "version": PANORAMA_MFE_VERSION
        }
    return mfes


# Load patches from files
for path in glob(str(importlib_resources.files("tutorpanorama") / "patches" / "*")):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))

hooks.Filters.ENV_TEMPLATE_VARIABLES.add_items(
    [
        ('PANORAMA_OPENEDX_BACKEND_VERSION', PANORAMA_OPENEDX_BACKEND_VERSION),
        ('PANORAMA_ELT_VERSION', PANORAMA_ELT_VERSION),
    ]
)


# Commands
@click.command()
@click.option("--all", "-a", "all_", is_flag=True, default=False,
              help="Panorama: Extract and load all tables of all datasource")
@click.option("--tables", "-t", required=False, default=None,
              help="Comma separated list of tables to extract and load")
@click.option('--force', is_flag=True, default=False,
              help='Force upload all partitions. False by default')
@click.option("--debug", is_flag=True, default=False, help="Enable debugging")
def extract_and_load(all_, tables, force, debug) -> list[tuple[str, str]]:
    """
    Extract and load all, or a specific tablename
    """
    if all_:
        if tables:
            raise click.BadParameter("--all and --table cannot be used together")
        return [
            (
                'panorama',
                '/usr/local/bin/python /panorama-elt/panorama.py --settings '
                f'/config/panorama_openedx_settings.yaml extract-and-load --all'
                f'{" --debug" if debug else ""}'
            )
        ]
    if not tables:
        raise click.BadParameter("Define either --all or --tables")

    command = ('/usr/local/bin/python /panorama-elt/panorama.py '
               '--settings /config/panorama_openedx_settings.yaml '
               'extract-and-load --tables {tables}')

    if force:
        command += " --force"
    if debug:
        command += " --debug"

    return [('panorama', command)]


hooks.Filters.CLI_DO_COMMANDS.add_item(extract_and_load)
