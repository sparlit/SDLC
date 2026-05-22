# Version: 1.1.0
# Version: 1.1.0
"""
Tests for setup/docker-compose.yml

This file was significantly refactored in the PR:
- Renamed from src/infrastructure/docker-compose.yml to setup/docker-compose.yml
- Removed custom Dockerfile build in favour of the upstream n8nio/n8n:latest image
- Removed heavy services: chroma, redis, gitea, grafana
- Added ollama for local LLM support
- Added new n8n environment variables: N8N_PORT, N8N_PROTOCOL, NODE_ENV, WEBHOOK_URL
- Added version: '3.8' declaration
"""

import os
import pytest

COMPOSE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "setup", "docker-compose.yml"
)

# ---------------------------------------------------------------------------
# Attempt to load PyYAML; fall back to a minimal YAML-ish text reader.
# ---------------------------------------------------------------------------
try:
    import yaml as _yaml

    def _load_compose():
        with open(COMPOSE_PATH) as f:
            return _yaml.safe_load(f)

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

    def _load_compose():
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compose_text():
    with open(COMPOSE_PATH) as f:
        return f.read()


# ---------------------------------------------------------------------------
# File-level tests (no YAML parser needed)
# ---------------------------------------------------------------------------

class TestDockerComposeFileExists:
    def test_file_exists(self):
        assert os.path.isfile(COMPOSE_PATH), (
            f"setup/docker-compose.yml not found at {COMPOSE_PATH}"
        )

    def test_file_is_not_empty(self):
        assert os.path.getsize(COMPOSE_PATH) > 0


class TestDockerComposeVersionDeclaration:
    def test_version_38_declared(self):
        """PR added 'version: 3.8' at the top of the file."""
        text = _compose_text()
        assert "version:" in text, "version declaration is missing"
        assert "3.8" in text, "Expected compose file version 3.8"


class TestDockerComposeRequiredServices:
    """The three expected services must be present."""

    def test_db_service_present(self):
        assert "db:" in _compose_text()

    def test_n8n_service_present(self):
        assert "n8n:" in _compose_text()

    def test_ollama_service_present(self):
        """ollama service was added in this PR as a local LLM option."""
        assert "ollama:" in _compose_text()


class TestDockerComposeRequiredServices:
    """All architectural services must be present."""

    def test_db_service_present(self):
        assert "db:" in _compose_text()

    def test_n8n_service_present(self):
        assert "n8n:" in _compose_text()

    def test_ollama_service_present(self):
        assert "ollama:" in _compose_text()

    def test_chroma_service_present(self):
        assert "chroma:" in _compose_text()

    def test_redis_service_present(self):
        assert "redis:" in _compose_text()

    def test_gitea_service_present(self):
        assert "gitea:" in _compose_text()

    def test_grafana_service_present(self):
        assert "grafana:" in _compose_text()


class TestN8nServiceConfiguration:
    """n8n service should use the upstream image, not a custom build."""

    def test_n8n_uses_image_not_build(self):
        """PR replaced `build: context: . dockerfile: Dockerfile` with a plain image pull."""
        text = _compose_text()
        assert "n8nio/n8n:latest" in text, "n8n should use n8nio/n8n:latest image"

    def test_n8n_does_not_reference_dockerfile(self):
        """Custom Dockerfile was deleted; compose must not reference it."""
        assert "Dockerfile" not in _compose_text()

    def test_n8n_exposes_port_5678(self):
        assert "5678:5678" in _compose_text()

    def test_n8n_protocol_env_var_present(self):
        """N8N_PROTOCOL was added in this PR."""
        assert "N8N_PROTOCOL" in _compose_text()

    def test_n8n_port_env_var_present(self):
        """N8N_PORT was added in this PR."""
        assert "N8N_PORT" in _compose_text()

    def test_node_env_production_present(self):
        """NODE_ENV=production was added in this PR."""
        assert "NODE_ENV" in _compose_text()

    def test_webhook_url_env_var_present(self):
        """WEBHOOK_URL was added in this PR."""
        assert "WEBHOOK_URL" in _compose_text()

    def test_n8n_depends_on_db(self):
        assert "depends_on" in _compose_text()
        assert "- db" in _compose_text()

    def test_n8n_depends_on_chroma(self):
        assert "- chroma" in _compose_text()

    def test_n8n_depends_on_redis(self):
        assert "- redis" in _compose_text()

    def test_n8n_mounts_project_path(self):
        """n8n should mount the project directory under /data/project."""
        assert "/data/project" in _compose_text()


class TestOllamaServiceConfiguration:
    """ollama was added to provide an optional local LLM runner."""

    def test_ollama_uses_correct_image(self):
        assert "ollama/ollama:latest" in _compose_text()

    def test_ollama_exposes_port_11434(self):
        assert "11434:11434" in _compose_text()

    def test_ollama_has_restart_policy(self):
        """ollama should restart automatically, consistent with other services."""
        text = _compose_text()
        # restart: always appears for each service; just confirm it appears globally
        assert "restart: always" in text


class TestDockerComposeVolumes:
    """Named volumes should match the new simplified service set."""

    def test_n8n_db_data_volume_present(self):
        assert "n8n_db_data:" in _compose_text()

    def test_n8n_data_volume_present(self):
        assert "n8n_data:" in _compose_text()

    def test_ollama_data_volume_present(self):
        """ollama_data was added in this PR."""
        assert "ollama_data:" in _compose_text()

    def test_chroma_data_volume_present(self):
        assert "chroma_data:" in _compose_text()

    def test_gitea_data_volume_present(self):
        assert "gitea_data:" in _compose_text()


# ---------------------------------------------------------------------------
# YAML-structure tests (only run when PyYAML is available)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed; skipping structured YAML tests")
class TestDockerComposeYAMLStructure:
    @pytest.fixture(scope="class")
    def compose(self):
        return _load_compose()

    def test_top_level_keys(self, compose):
        """Compose file must have 'services' and 'volumes' top-level keys."""
        assert "services" in compose
        assert "volumes" in compose

    def test_service_count(self, compose):
        """Exactly seven services."""
        services = compose["services"]
        assert set(services.keys()) == {"db", "n8n", "ollama", "chroma", "redis", "gitea", "grafana"}

    def test_db_image(self, compose):
        assert compose["services"]["db"]["image"] == "postgres:16-alpine"

    def test_n8n_image(self, compose):
        assert compose["services"]["n8n"]["image"] == "n8nio/n8n:latest"

    def test_n8n_no_build_key(self, compose):
        """build: key must not exist on the n8n service."""
        assert "build" not in compose["services"]["n8n"]

    def test_ollama_image(self, compose):
        assert compose["services"]["ollama"]["image"] == "ollama/ollama:latest"

    def test_volume_count(self, compose):
        """Exactly five top-level volumes."""
        volumes = compose["volumes"]
        assert set(volumes.keys()) == {"n8n_db_data", "n8n_data", "ollama_data", "chroma_data", "gitea_data"}

    def test_n8n_restart_policy(self, compose):
        assert compose["services"]["n8n"]["restart"] == "always"

    def test_ollama_restart_policy(self, compose):
        assert compose["services"]["ollama"]["restart"] == "always"

    def test_n8n_port_mapping(self, compose):
        ports = compose["services"]["n8n"]["ports"]
        assert "5678:5678" in ports

    def test_ollama_port_mapping(self, compose):
        ports = compose["services"]["ollama"]["ports"]
        assert "11434:11434" in ports

    def test_n8n_env_includes_new_vars(self, compose):
        """New env vars added in this PR must be present."""
        env_list = compose["services"]["n8n"]["environment"]
        env_keys = [e.split("=")[0] for e in env_list]
        for expected in ("N8N_PORT", "N8N_PROTOCOL", "NODE_ENV", "WEBHOOK_URL"):
            assert expected in env_keys, f"Missing env var '{expected}' in n8n service"

    def test_n8n_depends_on_required_services(self, compose):
        depends = compose["services"]["n8n"].get("depends_on", [])
        assert "db" in depends
        assert "chroma" in depends
        assert "redis" in depends