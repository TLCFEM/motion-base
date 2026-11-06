#  Copyright (C) 2022-2026 Theodore Chang
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pytest

import mb
from mb import Config


def test_config_defaults():
    config = Config()

    assert config.workers == 2
    assert config.port == 8000
    assert config.worker is False
    assert config.worker_config == []


@pytest.mark.parametrize("workers", [0, -1])
def test_config_rejects_invalid_workers(workers):
    with pytest.raises(ValueError):
        Config(workers=workers)


def test_run_app_uses_env(monkeypatch):
    captured: dict = {}

    def fake_run(app, **kwargs):
        captured["app"] = app
        captured.update(kwargs)

    monkeypatch.setattr("uvicorn.run", fake_run)
    monkeypatch.setattr("mb.utility.env.MB_FASTAPI_WORKERS", "3")
    monkeypatch.setattr("mb.utility.env.MB_PORT", "9000")

    mb.run_app(Config(host="127.0.0.1"))

    assert captured == {
        "app": "mb.app.main:app",
        "workers": 3,
        "port": 9000,
        "host": "127.0.0.1",
    }


def test_run_app_uses_settings(monkeypatch):
    captured: dict = {}

    def fake_run(app, **kwargs):
        captured["app"] = app
        captured.update(kwargs)

    monkeypatch.setattr("uvicorn.run", fake_run)

    mb.run_app(
        Config(
            workers=1,
            host="0.0.0.0",
            port=9001,
            overwrite_env=True,
            debug=True,
        )
    )

    assert captured == {
        "app": "mb.app.main:app",
        "reload": True,
        "log_level": "debug",
        "port": 9001,
        "host": "0.0.0.0",
    }


def test_run_worker(monkeypatch):
    captured: dict = {}

    class FakeArgs:
        @classmethod
        def from_cli(cls, args):
            return args

    def fake_run_worker(args):
        captured["args"] = args

    monkeypatch.setattr("taskiq.cli.worker.args.WorkerArgs", FakeArgs, raising=False)
    monkeypatch.setattr("taskiq.cli.worker.run.run_worker", fake_run_worker)

    mb.run_worker(Config(worker_config=["--workers", "2"]))

    assert captured["args"][:3] == [
        "mb.taskiq:broker",
        "mb.app.jp",
        "mb.app.nz",
    ]
    assert captured["args"][3:] == ["--workers", "2"]
