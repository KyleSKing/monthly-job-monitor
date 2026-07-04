import os
import sys
import tempfile
import unittest

API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

import _store  # noqa: E402


class CrudStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store_file = os.path.join(self.tmp.name, "manual_jobs.json")
        self._orig_path = _store._store_path
        _store._store_path = lambda: self.store_file

    def tearDown(self):
        _store._store_path = self._orig_path
        self.tmp.cleanup()

    def _sample(self, **overrides):
        job = {
            "title": "Senior Security Engineer",
            "company": "Tencent",
            "location": "Beijing",
            "url": "https://careers.tencent.com/job/123",
            "score": 2,
        }
        job.update(overrides)
        return job

    # 1. GET returns a list
    def test_list_returns_list(self):
        self.assertEqual(_store.list_jobs(), [])

    # 2. POST creates a job and generates an id
    def test_create_generates_id(self):
        created = _store.create_job(self._sample())
        self.assertIn("id", created)
        self.assertTrue(created["id"])
        self.assertEqual(len(_store.list_jobs()), 1)

    # 3. POST rejects missing required fields
    def test_validate_rejects_missing_fields(self):
        from jobs import validate_job

        errors = validate_job({"title": "x"})
        self.assertTrue(any("company" in e for e in errors))
        self.assertTrue(any("url" in e for e in errors))

    def test_validate_rejects_non_integer_score(self):
        from jobs import validate_job

        errors = validate_job(self._sample(score="high"))
        self.assertTrue(any("score" in e for e in errors))

    # 4. PUT updates an existing job
    def test_update_existing(self):
        created = _store.create_job(self._sample())
        updated = _store.update_job(created["id"], self._sample(title="Updated"))
        self.assertIsNotNone(updated)
        self.assertEqual(updated["title"], "Updated")
        self.assertEqual(updated["id"], created["id"])

    # 5. PUT returns None (-> 404) for unknown ids
    def test_update_unknown_returns_none(self):
        self.assertIsNone(_store.update_job("nope", self._sample()))

    # 6. DELETE removes a job
    def test_delete_existing(self):
        created = _store.create_job(self._sample())
        self.assertTrue(_store.delete_job(created["id"]))
        self.assertEqual(_store.list_jobs(), [])

    # 7. DELETE returns False (-> 404) for unknown ids
    def test_delete_unknown_returns_false(self):
        self.assertFalse(_store.delete_job("nope"))


if __name__ == "__main__":
    unittest.main()
