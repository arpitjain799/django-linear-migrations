from __future__ import annotations

import sys
import time
from functools import partial
from textwrap import dedent

import pytest
from django.test import override_settings
from django.test import TestCase

from tests.utils import run_command


class MakeMigrationsTests(TestCase):
    @pytest.fixture(autouse=True)
    def tmp_path_fixture(self, tmp_path):
        migrations_module_name = "migrations" + str(time.time()).replace(".", "")
        self.migrations_dir = tmp_path / migrations_module_name
        self.migrations_dir.mkdir()
        sys.path.insert(0, str(tmp_path))
        try:
            with override_settings(
                MIGRATION_MODULES={"testapp": migrations_module_name}
            ):
                yield
        finally:
            sys.path.pop(0)

    call_command = partial(run_command, "makemigrations")

    def test_dry_run(self):
        out, err, returncode = self.call_command("--dry-run", "testapp")

        assert returncode == 0
        max_migration_txt = self.migrations_dir / "max_migration.txt"
        assert not max_migration_txt.exists()

    def test_creates_max_migration_txt(self):
        out, err, returncode = self.call_command("testapp")

        assert returncode == 0
        max_migration_txt = self.migrations_dir / "max_migration.txt"
        assert max_migration_txt.read_text() == "0001_initial\n"

    def test_creates_max_migration_txt_given_name(self):
        out, err, returncode = self.call_command("testapp", "--name", "brand_new")

        assert returncode == 0
        max_migration_txt = self.migrations_dir / "max_migration.txt"
        assert max_migration_txt.read_text() == "0001_brand_new\n"

    def test_creates_max_migration_txt_second(self):
        (self.migrations_dir / "__init__.py").touch()
        (self.migrations_dir / "0001_initial.py").write_text(
            dedent(
                """\
            from django.db import migrations, models


            class Migration(migrations.Migration):
                initial = True
                dependencies = []
                operations = []
            """
            )
        )
        (self.migrations_dir / "max_migration.txt").write_text("0001_initial\n")

        out, err, returncode = self.call_command("testapp", "--name", "create_book")

        assert returncode == 0
        max_migration_txt = self.migrations_dir / "max_migration.txt"
        assert max_migration_txt.read_text() == "0002_create_book\n"

    @override_settings(FIRST_PARTY_APPS=[])
    def test_skips_creating_max_migration_txt_for_non_first_party_app(self):
        out, err, returncode = self.call_command("testapp")

        assert returncode == 0
        max_migration_txt = self.migrations_dir / "max_migration.txt"
        assert not max_migration_txt.exists()
