"""
Tests for setup/.env.example

This file was added in the PR to provide a configuration template for the
autonomous SDLC workflow. These tests verify its structure, required variables,
and that placeholder values are used instead of real secrets.
"""

import os
import re
import pytest

ENV_EXAMPLE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "setup", ".env.example"
)


def _parse_env_file(path):
    """Parse a .env file and return a dict of key -> value.
    Ignores comment lines and blank lines."""
    variables = {}
    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key, _, value = stripped.partition("=")
                variables[key.strip()] = value.strip()
    return variables


class TestEnvExampleExists:
    def test_file_exists(self):
        """setup/.env.example must be present in the repository."""
        assert os.path.isfile(ENV_EXAMPLE_PATH), (
            f"Expected setup/.env.example at {ENV_EXAMPLE_PATH}"
        )

    def test_file_is_not_empty(self):
        """The file must contain at least some content."""
        assert os.path.getsize(ENV_EXAMPLE_PATH) > 0


class TestEnvExampleRequiredVariables:
    """All variables required by the docker-compose stack must be declared."""

    REQUIRED_VARS = [
        "N8N_HOST",
        "N8N_API_KEY",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "PROJECT_PATH",
        "OPENROUTER_API_KEY",
    ]

    @pytest.fixture(scope="class")
    def variables(self):
        return _parse_env_file(ENV_EXAMPLE_PATH)

    @pytest.mark.parametrize("var_name", REQUIRED_VARS)
    def test_required_variable_present(self, variables, var_name):
        """Each required variable must appear in .env.example."""
        assert var_name in variables, (
            f"Required variable '{var_name}' is missing from setup/.env.example"
        )

    def test_exactly_seven_variables(self, variables):
        """The file should define exactly the 7 expected configuration variables."""
        assert len(variables) == 7, (
            f"Expected 7 variables, found {len(variables)}: {list(variables.keys())}"
        )


class TestEnvExamplePlaceholderValues:
    """Placeholder text must be used so real secrets are never committed."""

    @pytest.fixture(scope="class")
    def variables(self):
        return _parse_env_file(ENV_EXAMPLE_PATH)

    def test_n8n_api_key_is_placeholder(self, variables):
        """N8N_API_KEY must not look like a real key."""
        value = variables.get("N8N_API_KEY", "")
        assert "your_" in value.lower() or "placeholder" in value.lower() or value == "", (
            f"N8N_API_KEY appears to contain a real secret: '{value}'"
        )

    def test_openrouter_api_key_is_placeholder(self, variables):
        """OPENROUTER_API_KEY must use a placeholder, not a real key."""
        value = variables.get("OPENROUTER_API_KEY", "")
        assert "your_" in value.lower() or "placeholder" in value.lower() or value == "", (
            f"OPENROUTER_API_KEY appears to contain a real secret: '{value}'"
        )


class TestEnvExampleDefaultValues:
    """Sensible defaults should be set for non-secret variables."""

    @pytest.fixture(scope="class")
    def variables(self):
        return _parse_env_file(ENV_EXAMPLE_PATH)

    def test_n8n_host_defaults_to_localhost(self, variables):
        assert variables.get("N8N_HOST") == "localhost"

    def test_postgres_user_has_value(self, variables):
        assert variables.get("POSTGRES_USER") != ""

    def test_postgres_db_has_value(self, variables):
        assert variables.get("POSTGRES_DB") != ""

    def test_postgres_password_has_value(self, variables):
        assert variables.get("POSTGRES_PASSWORD") != ""

    def test_project_path_has_value(self, variables):
        """PROJECT_PATH must have a non-empty default."""
        assert variables.get("PROJECT_PATH") != ""


class TestEnvExampleFormat:
    """The file must follow valid .env file conventions."""

    def test_no_spaces_around_equals(self):
        """KEY=VALUE lines must not have spaces around '='."""
        with open(ENV_EXAMPLE_PATH) as f:
            for lineno, line in enumerate(f, 1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                # A KEY=VALUE line should match KEY=... not KEY = ...
                assert not re.match(r"^\w+\s+=", stripped), (
                    f"Line {lineno} has space before '=': {stripped!r}"
                )
                assert not re.match(r"^\w+=\s+\S", stripped), (
                    f"Line {lineno} has space after '=': {stripped!r}"
                )

    def test_no_trailing_whitespace_in_values(self):
        """Values must not have trailing whitespace."""
        with open(ENV_EXAMPLE_PATH) as f:
            for lineno, line in enumerate(f, 1):
                # Each line (excluding newline) should not end in spaces/tabs
                assert line.rstrip("\n") == line.rstrip("\n").rstrip(), (
                    f"Line {lineno} has trailing whitespace: {line!r}"
                )

    def test_all_variable_names_are_uppercase(self):
        """Environment variable names should be UPPER_CASE."""
        variables = _parse_env_file(ENV_EXAMPLE_PATH)
        for name in variables:
            assert name == name.upper(), (
                f"Variable name '{name}' is not upper-case"
            )

    def test_n8n_api_key_and_openrouter_key_are_distinct(self):
        """The two API key placeholders must be separate entries."""
        variables = _parse_env_file(ENV_EXAMPLE_PATH)
        assert "N8N_API_KEY" in variables
        assert "OPENROUTER_API_KEY" in variables
        # They should be independently configurable (different variable names)
        assert "N8N_API_KEY" != "OPENROUTER_API_KEY"
