"""Tests for the self-ping keepalive (no network). Run: python -m unittest discover."""

from __future__ import annotations

import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient


class TestKeepaliveLifespan(unittest.TestCase):
    def test_no_keepalive_task_without_env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("KEEPALIVE_")}
        with mock.patch.dict(os.environ, env, clear=True):
            from pricewise_engine.app import _lifespan

            import asyncio

            async def run():
                async with _lifespan(None):
                    # no KEEPALIVE_URL -> the lifespan must not create a task
                    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                    self.assertEqual(tasks, [])

            asyncio.run(run())

    def test_ping_swallows_errors_and_cancels(self):
        with mock.patch.dict(
            os.environ,
            {"KEEPALIVE_URL": "http://127.0.0.1:9/health", "KEEPALIVE_INTERVAL_SECONDS": "0.01"},
        ):
            from pricewise_engine.app import _lifespan

            import asyncio

            async def run():
                async with _lifespan(None):
                    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                    self.assertEqual(len(tasks), 1)  # pinger started
                    await asyncio.sleep(0.05)  # a few failing pings to port 9
                    self.assertFalse(tasks[0].done())  # still alive despite errors

            asyncio.run(run())  # exits cleanly (task cancelled on shutdown)

    def test_health_still_works(self):
        with TestClient(__import__("pricewise_engine.app", fromlist=["app"]).app) as client:
            self.assertEqual(client.get("/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
