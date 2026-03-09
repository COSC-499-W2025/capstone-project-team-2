"""AppTest-based tests for ResumeAndPortfoiloMaker.py.

Uses Streamlit's headless AppTest framework to simulate the page,
interact with widgets, and assert on rendered output elements.
"""

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
    """Minimal requests.Response stub for mocking API calls in tests.

    Args:
        ok: whether the response indicates success
        payload: JSON-serialisable object returned by .json()
        text: raw response text used as fallback error message

    Returns:
        _Resp: a stub that quacks like requests.Response for ok, json(), text, and status_code
    """

    def __init__(self, ok=True, payload=None, text=""):
        self.ok, self._payload, self.text = ok, payload, text
        self.status_code = 200 if ok else 400

    def json(self):
        """Return the stored payload or raise ValueError if none was provided.

        Returns:
            dict | list: the JSON payload passed at construction
        """
        if self._payload is None:
            raise ValueError
        return self._payload


_SAMPLE_DOC = {
    "contact": {"name": "Jane Doe", "email": "j@e.com", "phone": "", "location": "", "website": ""},
    "summary": "Dev.", "theme": "sb2nov",
    "connections": [], "education": [], "experience": [], "projects": [], "skills": [],
}


class _Base(unittest.TestCase):
    """Shared setup for all ResumeAndPortfoiloMaker tests.

    Provides a temporary CV files directory and patches the Streamlit sidebar
    so tests run headlessly without side effects.
    """

    def setUp(self):
        """Create a temp directory and start patches for CV_FILES_DIR and the sidebar.

        Returns:
            None: sets up instance attributes _tmp, _cv_patch, and _sb_patch
        """
        self._tmp = tempfile.TemporaryDirectory()
        self._cv_patch = patch(_CV_DIR, Path(self._tmp.name))
        self._sb_patch = patch(_SIDEBAR)
        self._cv_patch.start()
        self._sb_patch.start()

    def tearDown(self):
        """Stop patches and clean up the temp directory.

        Returns:
            None: restores original module state and removes temp files
        """
        self._sb_patch.stop()
        self._cv_patch.stop()
        self._tmp.cleanup()

    def _app(self, **session):
        """Build an AppTest instance for the page with pre-set session state.

        Args:
            **session: key-value pairs to inject into Streamlit session_state
                before running (e.g. view_mode="Public", resume_id="abc")

        Returns:
            AppTest: a configured but not-yet-run AppTest instance
        """
        at = AppTest.from_file(_PAGE, default_timeout=10)
        for k, v in session.items():
            at.session_state[k] = v
        return at

    def _touch(self, name):
        """Create an empty file in the temp CV directory.

        Args:
            name: filename to create (e.g. "Jane_a1b2c3d4_Resume_CV.yaml")

        Returns:
            None: the file is created as a side effect
        """
        (Path(self._tmp.name) / name).touch()


class TestPublicMode(_Base):
    """Verify Public (read-only) mode rendering of the page."""

    @patch(_API_GET, return_value=_Resp(payload=[]))
    def test_shows_readonly_info(self, _):
        """Verify that Public mode displays a read-only info banner.

        Returns:
            None: asserts info banner contains 'read-only'
        """
        at = self._app(view_mode="Public").run()
        assert not at.exception
        assert any("read-only" in v.value.lower() for v in at.info)

    @patch(_API_GET, return_value=_Resp(payload=[]))
    def test_no_create_or_delete_controls(self, _):
        """Verify that Public mode hides create and delete buttons.

        Returns:
            None: asserts no button label contains 'generate' or 'delete'
        """
        at = self._app(view_mode="Public").run()
        for btn in at.button:
            assert "generate" not in btn.label.lower()
            assert "delete" not in btn.label.lower()

    @patch(_API_GET, return_value=_Resp(payload=[]))
    def test_warns_when_no_docs(self, _):
        """Verify that Public mode warns the user when no saved documents exist.

        Returns:
            None: asserts a warning containing 'no saved' is displayed
        """
        at = self._app(view_mode="Public").run()
        assert any("no saved" in w.value.lower() for w in at.warning)

    @patch(_API_GET, return_value=_Resp(payload=[]))
    def test_shows_selector_when_docs_exist(self, _):
        """Verify that Public mode shows a document selector and Load button when docs exist.

        Returns:
            None: asserts a selectbox and a 'load' button are rendered
        """
        self._touch("Jane_a1b2c3d4_Resume_CV.yaml")
        at = self._app(view_mode="Public").run()
        assert len(at.selectbox) > 0
        assert any("load" in b.label.lower() for b in at.button)


class TestPrivateNoDoc(_Base):
    """Verify Private mode when no resume or portfolio is loaded."""

    def test_renders_cleanly(self):
        """Verify the page renders without exceptions when no document is active.

        Returns:
            None: asserts no exception was raised during rendering
        """
        at = self._app(view_mode="Private").run()
        assert not at.exception

    def test_page_title(self):
        """Verify the page displays a title containing 'resume' or 'portfolio'.

        Returns:
            None: asserts the title element text matches expected keywords
        """
        at = self._app(view_mode="Private").run()
        assert any("resume" in t.value.lower() or "portfolio" in t.value.lower() for t in at.title)

    def test_resume_count_expander(self):
        """Verify the resume count expander reflects the number of saved files.

        Returns:
            None: asserts an expander label contains '2 resume'
        """
        self._touch("Jane_a1b2c3d4_Resume_CV.yaml")
        self._touch("John_deadbeef_Resume_CV.yaml")
        at = self._app(view_mode="Private").run()
        assert any("2 resume" in e.label.lower() for e in at.expander)


class TestActiveResume(_Base):
    """Verify Private mode when a resume is actively loaded."""

    @patch(_API_GET, return_value=_Resp(payload=_SAMPLE_DOC))
    def test_shows_resume_id(self, _):
        """Verify the active resume ID is displayed in an info banner.

        Returns:
            None: asserts 'Jane_Doe_a1b2c3d4' appears in an info element
        """
        at = self._app(view_mode="Private", resume_id="Jane_Doe_a1b2c3d4").run()
        assert not at.exception
        assert any("Jane_Doe_a1b2c3d4" in v.value for v in at.info)

    @patch(_API_GET, return_value=_Resp(payload=_SAMPLE_DOC))
    def test_close_button_present(self, _):
        """Verify a Close button is rendered to deactivate the loaded resume.

        Returns:
            None: asserts a button with 'close' label exists
        """
        at = self._app(view_mode="Private", resume_id="Jane_Doe_a1b2c3d4").run()
        assert any("close" in b.label.lower() for b in at.button)

    @patch(_API_GET, return_value=_Resp(ok=False, payload={"detail": "Not found"}, text="Not found"))
    def test_api_failure_shows_error(self, _):
        """Verify an error is displayed when the API returns a non-OK response.

        Returns:
            None: asserts at least one error element is rendered
        """
        at = self._app(view_mode="Private", resume_id="Jane_Doe_a1b2c3d4").run()
        assert len(at.error) > 0

    @patch(_API_GET, side_effect=requests.ConnectionError)
    def test_connection_error_shows_error(self, _):
        """Verify an error is displayed when the API server is unreachable.

        Returns:
            None: asserts at least one error element is rendered
        """
        at = self._app(view_mode="Private", resume_id="Jane_Doe_a1b2c3d4").run()
        assert len(at.error) > 0


class TestActivePortfolio(_Base):
    """Verify Private mode when a portfolio is actively loaded."""

    @patch(_API_GET, return_value=_Resp(payload=_SAMPLE_DOC))
    def test_shows_portfolio_id(self, _):
        """Verify the active portfolio ID is displayed in an info banner.

        Returns:
            None: asserts 'Jane_abcd1234' appears in an info element
        """
        at = self._app(view_mode="Private", portfolio_id="Jane_abcd1234").run()
        assert any("Jane_abcd1234" in v.value for v in at.info)


class TestResumeCreation(_Base):
    """Verify the resume creation form in Private mode."""

    def test_form_has_name_input(self):
        """Verify the create-resume form includes a text input for the name.

        Returns:
            None: asserts at least one text_input widget is rendered
        """
        at = self._app(view_mode="Private").run()
        assert len(at.text_input) > 0

    @patch(_PAGE_POST)
    def test_empty_name_no_api_call(self, mock_post):
        """Verify that submitting with an empty name does not trigger an API call.

        Args:
            mock_post: patched requests.post on the page module

        Returns:
            None: asserts mock_post was never called
        """
        at = self._app(view_mode="Private").run()
        if at.text_input:
            at.text_input[0].input("").run()
        mock_post.assert_not_called()


class TestPortfolioTab(_Base):
    """Verify the Portfolio tab renders in Private mode."""

    def test_renders_without_errors(self):
        """Verify the portfolio tab renders without raising any exceptions.

        Returns:
            None: asserts no exception was raised during rendering
        """
        at = self._app(view_mode="Private").run()
        assert not at.exception


if __name__ == "__main__":
    unittest.main()