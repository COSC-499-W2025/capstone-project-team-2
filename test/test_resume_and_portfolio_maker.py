"""AppTest-based tests for ResumeAndPortfoiloMaker.py."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import requests
from streamlit.testing.v1 import AppTest

_PAGE = "src/web/pages/ResumeAndPortfoiloMaker.py"

# Patches applied to every test: sidebar (avoid real widget) + CV dir (use temp)
_SIDEBAR = "src.web.mode.st.sidebar"
_CV_DIR = "src.web.streamlit_helpers.CV_FILES_DIR"
_API_GET = "src.web.streamlit_helpers.requests.get"
_PAGE_POST = "src.web.pages.ResumeAndPortfoiloMaker.requests.post"


class _Resp:
    """Minimal requests.Response stub."""
    def __init__(self, ok=True, payload=None, text=""):
        self.ok, self._payload, self.text = ok, payload, text
        self.status_code = 200 if ok else 400
    def json(self):
        if self._payload is None: raise ValueError
        return self._payload


_SAMPLE_DOC = {
    "contact": {"name": "Jane Doe", "email": "j@e.com", "phone": "", "location": "", "website": ""},
    "summary": "Dev.", "theme": "sb2nov",
    "connections": [], "education": [], "experience": [], "projects": [], "skills": [],
}


class _Base(unittest.TestCase):
    """Shared setup: temp CV dir + sidebar patch."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._cv_patch = patch(_CV_DIR, Path(self._tmp.name))
        self._sb_patch = patch(_SIDEBAR)
        self._cv_patch.start()
        self._sb_patch.start()

    def tearDown(self):
        self._sb_patch.stop()
        self._cv_patch.stop()
        self._tmp.cleanup()

    def _app(self, **session):
        at = AppTest.from_file(_PAGE, default_timeout=10)
        for k, v in session.items():
            at.session_state[k] = v
        return at

    def _touch(self, name):
        (Path(self._tmp.name) / name).touch()


class TestPublicMode(_Base):

    @patch(_API_GET, return_value=_Resp(payload=[]))
    def test_shows_readonly_info(self, _):
        at = self._app(view_mode="Public").run()
        assert not at.exception
        assert any("read-only" in v.value.lower() for v in at.info)

    @patch(_API_GET, return_value=_Resp(payload=[]))
    def test_no_create_or_delete_controls(self, _):
        at = self._app(view_mode="Public").run()
        for btn in at.button:
            assert "generate" not in btn.label.lower()
            assert "delete" not in btn.label.lower()

    @patch(_API_GET, return_value=_Resp(payload=[]))
    def test_warns_when_no_docs(self, _):
        at = self._app(view_mode="Public").run()
        assert any("no saved" in w.value.lower() for w in at.warning)

    @patch(_API_GET, return_value=_Resp(payload=[]))
    def test_shows_selector_when_docs_exist(self, _):
        self._touch("Jane_a1b2c3d4_Resume_CV.yaml")
        at = self._app(view_mode="Public").run()
        assert len(at.selectbox) > 0
        assert any("load" in b.label.lower() for b in at.button)


class TestPrivateNoDoc(_Base):

    def test_renders_cleanly(self):
        at = self._app(view_mode="Private").run()
        assert not at.exception

    def test_page_title(self):
        at = self._app(view_mode="Private").run()
        assert any("resume" in t.value.lower() or "portfolio" in t.value.lower() for t in at.title)

    def test_resume_count_expander(self):
        self._touch("Jane_a1b2c3d4_Resume_CV.yaml")
        self._touch("John_deadbeef_Resume_CV.yaml")
        at = self._app(view_mode="Private").run()
        assert any("2 resume" in e.label.lower() for e in at.expander)


class TestActiveResume(_Base):

    @patch(_API_GET, return_value=_Resp(payload=_SAMPLE_DOC))
    def test_shows_resume_id(self, _):
        at = self._app(view_mode="Private", resume_id="Jane_Doe_a1b2c3d4").run()
        assert not at.exception
        assert any("Jane_Doe_a1b2c3d4" in v.value for v in at.info)

    @patch(_API_GET, return_value=_Resp(payload=_SAMPLE_DOC))
    def test_close_button_present(self, _):
        at = self._app(view_mode="Private", resume_id="Jane_Doe_a1b2c3d4").run()
        assert any("close" in b.label.lower() for b in at.button)

    @patch(_API_GET, return_value=_Resp(ok=False, payload={"detail": "Not found"}, text="Not found"))
    def test_api_failure_shows_error(self, _):
        at = self._app(view_mode="Private", resume_id="Jane_Doe_a1b2c3d4").run()
        assert len(at.error) > 0

    @patch(_API_GET, side_effect=requests.ConnectionError)
    def test_connection_error_shows_error(self, _):
        at = self._app(view_mode="Private", resume_id="Jane_Doe_a1b2c3d4").run()
        assert len(at.error) > 0


class TestActivePortfolio(_Base):

    @patch(_API_GET, return_value=_Resp(payload=_SAMPLE_DOC))
    def test_shows_portfolio_id(self, _):
        at = self._app(view_mode="Private", portfolio_id="Jane_abcd1234").run()
        assert any("Jane_abcd1234" in v.value for v in at.info)


class TestResumeCreation(_Base):

    def test_form_has_name_input(self):
        at = self._app(view_mode="Private").run()
        assert len(at.text_input) > 0

    @patch(_PAGE_POST)
    def test_empty_name_no_api_call(self, mock_post):
        at = self._app(view_mode="Private").run()
        if at.text_input:
            at.text_input[0].input("").run()
        mock_post.assert_not_called()


class TestPortfolioTab(_Base):

    def test_renders_without_errors(self):
        at = self._app(view_mode="Private").run()
        assert not at.exception


if __name__ == "__main__":
    unittest.main()