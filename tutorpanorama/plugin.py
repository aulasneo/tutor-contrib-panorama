"""
Tutor plugin to enable Panorama in Open edX.
"""
from __future__ import annotations

from glob import glob
import os

import click
import importlib_resources

from tutor import fmt, hooks, config as tutor_config
from tutormfe.hooks import MFE_APPS

from .__about__ import __version__

# Version of openedx-backend-version in PyPI

PANORAMA_OPENEDX_BACKEND_VERSION = '16.0.12'

PANORAMA_MFE_REPO = "https://github.com/aulasneo/frontend-app-panorama.git"

# Tag at https://github.com/aulasneo/frontend-app-panorama.git
PANORAMA_MFE_VERSION = 'open-release/redwood.20240729'

# Tag at https://github.com/aulasneo/panorama-elt.git
PANORAMA_ELT_VERSION = 'v0.3.2'

# Tag at https://github.com/aulasneo/frontend-app-learner-dashboard
PANORAMA_FRONTEND_APP_LEARNER_DASHBOARD_VERSION = 'panorama/redwood/v20250327'
PANORAMA_FRONTEND_APP_LEARNER_DASHBOARD_REPO = \
    'https://github.com/aulasneo/frontend-app-learner-dashboard.git'

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
        "ADD_DASHBOARD_LINK": False,
        "MODE": "DEMO",
        "MFE_PORT": PANORAMA_MFE_PORT,
        "FRONTEND_APP_LEARNER_DASHBOARD_VERSION": PANORAMA_FRONTEND_APP_LEARNER_DASHBOARD_VERSION,
        "FRONTEND_APP_LEARNER_DASHBOARD_REPO": PANORAMA_FRONTEND_APP_LEARNER_DASHBOARD_REPO,
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

    command = [
        '/usr/local/bin/python /panorama-elt/panorama.py',
        '--settings /config/panorama_openedx_settings.yaml',
    ]

    if debug:
        command.append('--debug')

    command.append('extract-and-load')

    if all_:
        if tables:
            raise click.BadParameter("--all and --table cannot be used together")
        command.append('--all')
    else:
        if not tables:
            raise click.BadParameter("Define either --all or --tables")
        command.append(f'--tables {tables}')

    if force:
        command.append("--force")

    return [('panorama', ' '.join(command))]

@MFE_APPS.add()
def _use_panorama_learner_dashboard(mfes):
    current_context = click.get_current_context()
    root = current_context.params.get('root')
    if root:
        configuration = tutor_config.load(root)
        if configuration['PANORAMA_ADD_DASHBOARD_LINK']:
            repo = mfes['learner-dashboard']['repository']
            if (repo !=
                    'https://github.com/openedx/frontend-app-learner-dashboard.git'):
                fmt.echo_alert(f"You have a custom learner-dashboard MFE set at {repo}. "
                               f"Setting PANORAMA_USE_DASHBOARD_LINK to True "
                               f"will override your custom MFE.")
            mfes['learner-dashboard']['repository'] = PANORAMA_FRONTEND_APP_LEARNER_DASHBOARD_REPO
            mfes['learner-dashboard']['version'] = PANORAMA_FRONTEND_APP_LEARNER_DASHBOARD_VERSION
    return mfes


hooks.Filters.CLI_DO_COMMANDS.add_item(extract_and_load)
