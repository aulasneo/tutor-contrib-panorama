"""Local contract tests; run with Tutor 22 and tutor-mfe 22 installed."""
from pathlib import Path

import pytest
import yaml
from tutor import env
from tutorpanorama import plugin

ROOT = Path(__file__).resolve().parents[1] / "tutorpanorama"


def render(path, **overrides):
    values = {f"PANORAMA_{key}": value for key, value in plugin.config["defaults"].items()}
    values.update(K8S_NAMESPACE="school-a", LMS_HOST="courses.example.org", MFE_HOST="apps.courses.example.org", ENABLE_HTTPS=True,
                  PANORAMA_DOCKER_IMAGE="panorama:test", PANORAMA_LOGS_DOCKER_IMAGE="panorama-logs:test",
                  PANORAMA_AWS_ACCESS_KEY="test-key", PANORAMA_AWS_SECRET_ACCESS_KEY="test-secret")
    values.update(overrides)
    return env.Renderer(values).render_str((ROOT / path).read_text())


@pytest.mark.parametrize("mode", ["DEMO", "FREE", "SAAS", "CUSTOM"])
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("fluent", [False, True])
def test_mode_matrix(mode, enabled, fluent):
    values = dict(PANORAMA_MODE=mode, PANORAMA_MFE_ENABLED=enabled, PANORAMA_RUN_K8S_FLUENTBIT=fluent,
                  PANORAMA_K8S_JOB_MEMORY_REQUEST="256Mi", PANORAMA_K8S_JOB_MEMORY_LIMIT="512Mi")
    jobs = list(yaml.safe_load_all(render("patches/k8s-jobs", **values)))
    cron = next((job for job in jobs if job and job["kind"] == "CronJob"), None)
    assert bool(cron) == (mode != "DEMO")
    if cron:
        assert cron["spec"]["concurrencyPolicy"] == "Forbid"
        assert cron["spec"]["jobTemplate"]["spec"]["activeDeadlineSeconds"] == 3300
        container = cron["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]
        assert container["resources"] == {"requests": {"memory": "256Mi"}, "limits": {"memory": "512Mi"}}
    deploy = list(yaml.safe_load_all(render("patches/k8s-deployments", **values)))
    assert any(deploy) == (fluent and mode in ["SAAS", "CUSTOM"])
    compose = yaml.safe_load(render("patches/local-docker-compose-services", **values)) or {}
    assert ("panorama" in compose) == (mode != "DEMO")
    assert ("panorama_logs" in compose) == (mode in ["SAAS", "CUSTOM"])
    for patch in ["mfe-lms-production-settings", "mfe-lms-development-settings", "mfe-env-config-buildtime-imports", "mfe-env-config-buildtime-definitions", "mfe-site-custom-app-imports", "mfe-site-custom-app-final", "openedx-dockerfile-post-python-requirements"]:
        assert bool(render(f"patches/{patch}", **values).strip()) == enabled
    init = render("templates/panorama/tasks/lms/init", **values)
    assert "makemigrations" not in init
    assert ("./manage.py lms migrate" in init) == (enabled and mode != "DEMO")
    if mode == "DEMO":
        assert "Panorama DEMO mode, skipping" in init


def test_configurable_sources_and_disabled_navigation():
    from tutormfe import plugin as mfe_plugin
    try:
        # Prime Tutor's caches with the old config, as config save/default rendering does.
        plugin._load_panorama_config({"PANORAMA_MFE_ENABLED": True})
        mfe_plugin.get_mfes()
        mfe_plugin.get_plugin_slots("all")
        mfe_plugin.get_frontend_slots()
        plugin._load_panorama_config({"PANORAMA_MFE_ENABLED": False})
        assert "panorama" not in mfe_plugin.get_mfes()
        assert not any("PanoramaSiteLink" in slot for slot in mfe_plugin.get_frontend_slots())
        assert "panorama" not in plugin._add_panorama_mfes({})
        assert plugin._panorama_legacy_slots([]) == []
        assert plugin._panorama_frontend_slots([]) == []
        plugin._load_panorama_config({"PANORAMA_MFE_ENABLED": True, "PANORAMA_MFE_REPO": "https://example.org/test.git", "PANORAMA_MFE_VERSION": "tested-sha", "PANORAMA_MFE_PORT": 2101})
        assert plugin._add_panorama_mfes({})["panorama"] == {"repository": "https://example.org/test.git", "version": "tested-sha", "port": 2101}
        assert len(plugin._panorama_frontend_slots([])) == 2
    finally:
        plugin._load_panorama_config({})


def test_urls_and_collector_state_isolation():
    assert 'https://apps.courses.example.org/panorama/' in render("patches/mfe-lms-production-settings")
    assert 'http://apps.courses.example.org/panorama/' in render("patches/mfe-lms-production-settings", ENABLE_HTTPS=False)
    assert ':2100/panorama/' in render("patches/mfe-lms-development-settings")
    config = render("templates/panorama/apps/panorama-elt/fluent-bit.conf")
    assert '/var/log/containers/lms*_*_lms-*.log' in config
    assert 'multiline.parser  docker, cri' in config
    assert 'store_dir        /var/lib/panorama-fluentbit/s3' in config
    assert '/tracking_logs/$TAG[1]/' in config
    assert 'upload_chunk_size' not in config
    deployment = render("patches/k8s-deployments", PANORAMA_MODE="CUSTOM")
    assert 'panorama-school-a-pod-log-reader' in deployment
    assert '/var/lib/panorama-fluentbit/school-a' in deployment


def test_cluster_collector_matches_sites_and_excludes_workers():
    from fnmatch import fnmatchcase

    config = render("templates/panorama/apps/panorama-elt/fluent-bit.conf")
    options = dict(line.strip().split(None, 1) for line in config.splitlines()
                   if line.strip().startswith(("Path ", "Exclude_Path ")))

    def collects(filename):
        path = f"/var/log/containers/{filename}"
        return fnmatchcase(path, options["Path"]) and not fnmatchcase(path, options["Exclude_Path"])

    for namespace in ("school-a", "school-b", "third-site"):
        assert collects(f"lms-123-abc_{namespace}_lms-deadbeef.log")
        assert not collects(f"lms-worker-123-abc_{namespace}_lms-deadbeef.log")
        assert not collects(f"lms-123-abc_{namespace}_sidecar-deadbeef.log")
        assert not collects(f"cms-123-abc_{namespace}_cms-deadbeef.log")
    assert '/tracking_logs/$TAG[1]/' in config


def test_panorama_bindings_are_namespaced():
    imports = render("patches/mfe-env-config-buildtime-imports")
    assert 'AppContext' not in imports
    assert 'useContext' not in imports
    assert 'as panorama' in imports
    definitions = render("patches/mfe-env-config-buildtime-definitions")
    assert 'panoramaUnsubscribe(subscription)' in definitions
    assert '/panorama/api/get-user-access' in definitions
    assert 'administrator' not in definitions
