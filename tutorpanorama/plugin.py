from glob import glob
import os
import pkg_resources

from tutor import hooks

from .__about__ import __version__

################# Configuration
config = {
    # Add here your new settings
    "defaults": {
        "VERSION": __version__,
        "CRONTAB": "55 * * * *",
        "BUCKET": "aulasneo-panorama",
        "RAW_LOGS_BUCKET": "{{ BUCKET }}",
        "BASE_PREFIX": "openedx",
        "REGION": "us-east-1",
        "DATALAKE_DATABASE": "panorama",
        "DATALAKE_WORKGROUP": "panorama",
        "AWS_ACCESS_KEY": "{{ OPENEDX_AWS_ACCESS_KEY }}",
        "AWS_SECRET_ACCESS_KEY": "{{ OPENEDX_AWS_SECRET_ACCESS_KEY }}",
        "FLB_LOG_LEVEL": 'info',
        "USE_SPLIT_MONGO": True,
    },
    # Add here settings that don't have a reasonable default for all users. For
    # instance: passwords, secret keys, etc.
    "unique": {
        # "SECRET_KEY": "\{\{ 24|random_string \}\}",
    },
    # Danger zone! Add here values to override settings from Tutor core or other plugins.
    "overrides": {
        # "PLATFORM_NAME": "My platform",
    },
}

################# Initialization tasks
# To run the script from templates/panorama/tasks/myservice/init, add:
hooks.Filters.COMMANDS_INIT.add_item((
    "panorama",
    ("panorama", "tasks", "panorama-elt", "init.sh"),
))

################# Docker image management
# To build an image with `tutor images build myimage`
hooks.Filters.IMAGES_BUILD.add_item((
    "panorama-elt",
    ("plugins", "panorama", "build", "panorama-elt"),
    "docker.io/aulasneo/panorama-elt:{{ PANORAMA_VERSION }}",
    (),
))
hooks.Filters.IMAGES_BUILD.add_item((
    "panorama-elt",
    ("plugins", "panorama", "build", "panorama-elt-logs"),
    "docker.io/aulasneo/panorama-elt-logs:{{ PANORAMA_VERSION }}",
    (),
))
# To pull/push an image with `tutor images pull myimage` and `tutor images push myimage`:
hooks.Filters.IMAGES_PULL.add_item((
    "panorama-elt",
    "docker.io/aulasneo/panorama-elt:{{ PANORAMA_VERSION }}",
))
hooks.Filters.IMAGES_PULL.add_item((
    "panorama-elt-logs",
    "docker.io/aulasneo/panorama-elt-logs:{{ PANORAMA_VERSION }}",
))
hooks.Filters.IMAGES_PUSH.add_item((
    "panorama-elt",
    "docker.io/aulasneo/panorama-elt:{{ PANORAMA_VERSION }}",
))
hooks.Filters.IMAGES_PUSH.add_item((
    "panorama-elt-logs",
    "docker.io/aulasneo/panorama-elt-logs:{{ PANORAMA_VERSION }}",
))

# TODO: implement logs extraction and load of tracking logs in local installations

################# You don't really have to bother about what's below this line,
################# except maybe for educational purposes :)

# Plugin templates
hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    pkg_resources.resource_filename("tutorpanorama", "templates")
)
hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    [
        ("panorama/build", "plugins"),
        ("panorama/apps", "plugins"),
    ],
)
# Load all patches from the "patches" folder
for path in glob(
        os.path.join(
            pkg_resources.resource_filename("tutorpanorama", "patches"),
            "*",
        )
):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))

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
