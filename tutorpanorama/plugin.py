"""
Tutor plugin to enable Panorama in Open edX.
"""

from __future__ import annotations

from glob import glob
import os
import shlex
from typing import Any

import click
import importlib_resources

from tutor import hooks
from tutormfe.hooks import MFE_APPS, PLUGIN_SLOTS, FRONTEND_SLOTS

from .__about__ import __version__

# PyPI package version.
PANORAMA_OPENEDX_BACKEND_VERSION = "22.0.0"

PANORAMA_MFE_REPO = "https://github.com/aulasneo/frontend-app-panorama.git"
PANORAMA_MFE_VERSION = "release/verawood/v20260926"

# Tag at https://github.com/aulasneo/panorama-elt.git
PANORAMA_ELT_VERSION = "v1.0.1"

PANORAMA_MFE_PORT = 2100

# Configuration
config = {
    # Add here your new settings
    "defaults": {
        "VERSION": __version__,
        "OPENEDX_BACKEND_VERSION": PANORAMA_OPENEDX_BACKEND_VERSION,
        "MFE_REPO": PANORAMA_MFE_REPO,
        "MFE_VERSION": PANORAMA_MFE_VERSION,
        "ELT_REPO": "https://github.com/aulasneo/panorama-elt.git",
        "ELT_VERSION": PANORAMA_ELT_VERSION,
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
        "FLB_LOG_LEVEL": "info",
        "USE_SPLIT_MONGO": True,
        "RUN_K8S_FLUENTBIT": True,
        "DEBUG": False,
        "LOGS_TOTAL_FILE_SIZE": "50M",
        "LOGS_UPLOAD_TIMEOUT": "10m",
        "LOGS_UPLOAD_CHUNK_SIZE": "10M",
        "FLB_BASE_IMAGE": "public.ecr.aws/aws-observability/aws-for-fluent-bit:3.4.15@sha256:88e1b56cedb230486afeca6eeb26c5f6bd59c48879d0054d1674d5a58838c607",
        "FLB_STORE_LIMIT": "1G",
        "FLB_TAIL_MEMORY_LIMIT": "32M",
        "FLB_LINE_MAX_SIZE": "1M",
        "K8S_JOB_BACKOFF_LIMIT": 1,
        "K8S_JOB_ACTIVE_DEADLINE_SECONDS": 3300,
        "K8S_CRON_STARTING_DEADLINE_SECONDS": 300,
        "DOCKER_IMAGE": "{{ DOCKER_REGISTRY }}aulasneo/panorama-elt:{{ PANORAMA_VERSION }}",
        "LOGS_DOCKER_IMAGE": "{{ DOCKER_REGISTRY }}aulasneo/panorama-elt-logs:{{ PANORAMA_VERSION }}",
        "MFE_ENABLED": True,
        "MODE": "DEMO",
        "MFE_PORT": PANORAMA_MFE_PORT,
        "ENABLE_STUDENT_VIEW": True,
        "DEFAULT_USER_ARN": "arn:aws:quicksight:{{ PANORAMA_REGION }}:{{ PANORAMA_AWS_ACCOUNT_ID }}:"
        "user/default/{{ LMS_HOST }}",
        "K8S_JOB_MEMORY_REQUEST": None,
        "K8S_JOB_MEMORY_LIMIT": None,
        "FLB_CPU_LIMIT": "500m",
        "FLB_MEM_LIMIT": "256Mi",
        "FLB_CPU_REQUEST": "100m",
        "FLB_MEM_REQUEST": "100Mi",
    },
    # Add here settings that don't have a reasonable default for all users. For
    # instance: passwords, secret keys, etc.
    "unique": {},
    # Danger zone! Add here values to override settings from Tutor core or other plugins.
    "overrides": {},
}

# Initialization tasks
MY_INIT_TASKS: list[tuple[str, str, int]] = [
    ("panorama", "panorama-elt", hooks.priorities.LOW),
    ("lms", "lms", hooks.priorities.LOW),  # backend migrations
]

# init script
for service, template_path, priority in MY_INIT_TASKS:
    with open(
        str(
            importlib_resources.files("tutorpanorama")
            / "templates"
            / "panorama"
            / "tasks"
            / template_path
            / "init"
        ),
        encoding="utf-8",
    ) as task_file:
        hooks.Filters.CLI_DO_INIT_TASKS.add_item(
            (service, task_file.read()), priority=priority
        )


# Load all configuration entries
hooks.Filters.CONFIG_DEFAULTS.add_items(
    [(f"PANORAMA_{key}", value) for key, value in config["defaults"].items()]
)
hooks.Filters.CONFIG_UNIQUE.add_items(
    [(f"PANORAMA_{key}", value) for key, value in config["unique"].items()]
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
        (
            "panorama",
            "{{ PANORAMA_DOCKER_IMAGE }}",
        ),
        ("panorama", "{{ PANORAMA_LOGS_DOCKER_IMAGE }}"),
    ]
)
hooks.Filters.IMAGES_PUSH.add_items(
    [
        (
            "panorama",
            "{{ PANORAMA_DOCKER_IMAGE }}",
        ),
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


# Load patches from files
for path in glob(str(importlib_resources.files("tutorpanorama") / "patches" / "*")):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))

# Load plugin slot configs from files (slot strings are not Jinja-rendered by Tutor).
_panorama_slots = []
for path in glob(
    str(importlib_resources.files("tutorpanorama") / "plugin_slots" / "*" / "*")
):
    with open(path, encoding="utf-8") as slot_file:
        mfe_name = os.path.basename(os.path.dirname(path))
        slot_name = os.path.basename(path)
        _panorama_slots.append((mfe_name, slot_name, slot_file.read()))

_loaded_config: dict[str, Any] = {}


@hooks.Actions.CONFIG_LOADED.add()
def _load_panorama_config(loaded_config: dict[str, Any]) -> None:
    _loaded_config.clear()
    _loaded_config.update(loaded_config)
    # tutor-mfe may resolve its cached registry while defaults are being rendered,
    # before CONFIG_LOADED. Refresh it for the final configuration (including --set).
    from tutormfe import plugin as mfe_plugin
    for getter in (mfe_plugin.get_mfes, mfe_plugin.get_plugin_slots, mfe_plugin.get_frontend_slots):
        getter.cache_clear()


def _setting(name: str) -> Any:
    return _loaded_config.get(f"PANORAMA_{name}", config["defaults"][name])


@PLUGIN_SLOTS.add()
def _panorama_legacy_slots(slots: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    if _setting("MFE_ENABLED"):
        slots.extend(_panorama_slots)
    return slots


@FRONTEND_SLOTS.add()
def _panorama_frontend_slots(slots: list[str]) -> list[str]:
    if _setting("MFE_ENABLED"):
        for target in ("secondaryLinks", "mobileMenuLinks"):
            slots.append("{ op: PanoramaWidgetOperationTypes.APPEND, slotId: 'org.openedx.frontend.slot.header."
                         + target + ".v1', id: 'panorama_" + target
                         + "', component: PanoramaSiteLink }")
    return slots


# Commands
@click.command()
@click.option(
    "--all",
    "-a",
    "all_",
    is_flag=True,
    default=False,
    help="Panorama: Extract and load all tables of all datasource",
)
@click.option(
    "--tables",
    "-t",
    required=False,
    default=None,
    help="Comma separated list of tables to extract and load",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force upload all partitions. False by default",
)
@click.option("--debug", is_flag=True, default=False, help="Enable debugging")
def extract_and_load(
    all_: bool,
    tables: str | None,
    force: bool,
    debug: bool,
) -> list[tuple[str, str]]:
    """
    Extract and load all, or a specific tablename
    """

    command = [
        "/usr/local/bin/python /panorama-elt/panorama.py",
        "--settings /config/panorama_openedx_settings.yaml",
    ]

    if debug:
        command.append("--debug")

    command.append("extract-and-load")

    if all_:
        if tables:
            raise click.BadParameter("--all and --table cannot be used together")
        command.append("--all")
    else:
        if not tables:
            raise click.BadParameter("Define either --all or --tables")
        command.append(f"--tables {shlex.quote(tables)}")

    if force:
        command.append("--force")

    return [("panorama", " ".join(command))]


@MFE_APPS.add()  # type: ignore[untyped-decorator]
def _add_panorama_mfes(mfes: dict[str, Any]) -> dict[str, Any]:
    if not _setting("MFE_ENABLED"):
        mfes.pop("panorama", None)
        return mfes
    mfes["panorama"] = {
        "repository": _setting("MFE_REPO"),
        "port": _setting("MFE_PORT"),
        "version": _setting("MFE_VERSION"),
    }

    return mfes


hooks.Filters.CLI_DO_COMMANDS.add_item(extract_and_load)
