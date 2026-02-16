"""
Essential tests for portfolio showcase functionality.

This module tests:
- Portfolio showcase construction
- CLI display formatting
"""

import unittest
import io
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from src.reporting.portfolio_service import (
    PortfolioShowcase,
    build_portfolio_showcase,
    display_portfolio_showcase,
    load_portfolio_showcase,
    save_project_role_override,
)
class TestBuildPortfolioShowcase(unittest.TestCase):
    """Test suite for build_portfolio_showcase function."""

    def test_build_portfolio_showcase_full(self):
        """Test building a complete portfolio showcase."""
        analysis = {
            'resume_item': {
                'project_name': 'Full Stack App',
                'summary': 'A complete application',
                'skills': ['Python', 'JavaScript'],
            },
            'oop_analysis': {
                'score': {
                    'oop_score': 0.8,
                    'rating': 'GOOD',
                    'comment': 'Well-structured'
                },
                'classes': {
                    'count': 50,
                    'avg_methods_per_class': 5,
                    'with_inheritance': 20
                },
                'complexity': {
                    'total_functions': 200,
                    'max_loop_depth': 3
                },
                'data_structures': {
                    'list_literals': 100,
                    'dict_literals': 80,
                    'set_literals': 10,
                    'tuple_literals': 20
                },
                'files_analyzed': 75
            },
            'contributors': {
                'Alice': {},
                'Bob': {}
            }
        }

        result = build_portfolio_showcase(analysis)

        self.assertIsInstance(result, PortfolioShowcase)

        self.assertEqual(result.title, 'Full Stack App')
        self.assertEqual(result.overview, 'A complete application')
        self.assertEqual(result.skills, ['Python', 'JavaScript'])

        self.assertIn("50 classes across multiple languages", result.technical_highlights[0])
        self.assertEqual(result.design_quality['oop_rating'], 'GOOD')
        self.assertEqual(result.design_quality['oop_comment'], 'Well-structured')
        self.assertEqual(result.design_quality['max_loop_depth'], 3)

        self.assertEqual(result.evidence['files_analyzed'], 75)
        self.assertEqual(result.evidence['total_functions'], 200)
        self.assertEqual(result.evidence['collection_literals'], 210)

        self.assertIn('Alice', result.contributors)
        self.assertIn('Bob', result.contributors)
class TestDisplayPortfolioShowcase(unittest.TestCase):
    """Test suite for display_portfolio_showcase function."""

    def test_display_portfolio_showcase_full(self):
        """Test full portfolio showcase display with all sections."""
        ps = PortfolioShowcase(
            title='Sample Project',
            role='Lead Developer',
            overview='An excellent sample project',
            technical_highlights=['Feature 1', 'Feature 2'],
            design_quality={
                'oop_rating': 'GOOD',
                'oop_comment': 'Well designed',
                'inheritance_classes': 15,
                'max_loop_depth': 3
            },
            evidence={
                'files_analyzed': 50,
                'total_functions': 200,
                'collection_literals': 150
            },
            skills=['Python', 'SQL'],
            contributors=['Alice', 'Bob']
        )

        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            display_portfolio_showcase(ps)
            captured = captured_output.getvalue()
        finally:
            sys.stdout = sys.__stdout__

        self.assertIn('PORTFOLIO SHOWCASE', captured)
        self.assertIn('Sample Project', captured)
        self.assertIn('Lead Developer', captured)
        self.assertIn('Overview:', captured)
        self.assertIn('Technical Highlights:', captured)
        self.assertIn('Feature 1', captured)
        self.assertIn('Design Quality:', captured)
        self.assertIn('Evidence:', captured)
        self.assertIn('Skills:', captured)
        self.assertIn('Contributors:', captured)


class TestPortfolioRoleOverrides(unittest.TestCase):
    """Tests for YAML-backed role override persistence."""

    def test_save_project_role_override_persists_and_preserves_fields(self):
        with TemporaryDirectory() as tmp_dir:
            override_path = Path(tmp_dir) / "My_Project.yaml"
            override_path.write_text(
                "project:\n"
                "  title: My Project\n"
                "portfolio:\n"
                "  overview: Existing overview\n",
                encoding="utf-8",
            )

            with patch(
                "src.reporting.portfolio_service._portfolio_override_path",
                return_value=override_path,
            ):
                saved = save_project_role_override("My Project", "Backend Developer")

                self.assertEqual(saved["project"]["role"], "Backend Developer")
                self.assertEqual(saved["project"]["title"], "My Project")
                self.assertEqual(saved["portfolio"]["overview"], "Existing overview")

                loaded = load_portfolio_showcase("My Project")
                self.assertEqual(loaded["project"]["role"], "Backend Developer")
                self.assertEqual(loaded["project"]["title"], "My Project")
                self.assertEqual(loaded["portfolio"]["overview"], "Existing overview")

if __name__ == '__main__':
    unittest.main()
