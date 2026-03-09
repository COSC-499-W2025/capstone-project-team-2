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
                'evidence': {
                    'duration': '3 months',
                    'test_file_count': 5,
                    'doc_metrics': [],
                    'doc_key_points': ['Key finding about architecture'],
                    'doc_types_found': ['software/technical'],
                    'contributor_count': 2,
                    'contributor_breakdown': {'Alice': '60%', 'Bob': '40%'},
                },
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
        self.assertEqual(result.skills, ['Python', 'JavaScript'])

        # Overview should include base summary + duration
        self.assertIn('A complete application', result.overview)
        self.assertIn('3 months', result.overview)

        # Design quality populated from OOP
        self.assertEqual(result.design_quality['oop_rating'], 'GOOD')
        self.assertEqual(result.design_quality['oop_comment'], 'Well-structured')
        self.assertEqual(result.design_quality['max_loop_depth'], 3)

        # Evidence populated from OOP + evidence block
        self.assertEqual(result.evidence['files_analyzed'], 75)
        self.assertEqual(result.evidence['total_functions'], 200)
        self.assertEqual(result.evidence['collection_literals'], 210)
        self.assertEqual(result.evidence['test_files'], 5)
        self.assertEqual(result.evidence['project_duration'], '3 months')
        self.assertIn('contributor_breakdown', result.evidence)

        self.assertIn('Alice', result.contributors)
        self.assertIn('Bob', result.contributors)

    def test_build_portfolio_showcase_no_evidence(self):
        """Test that missing evidence block degrades gracefully."""
        analysis = {
            'resume_item': {
                'project_name': 'Minimal Project',
                'summary': 'Simple project',
                'skills': [],
            },
        }
        result = build_portfolio_showcase(analysis)
        self.assertIsInstance(result, PortfolioShowcase)
        self.assertEqual(result.title, 'Minimal Project')
        self.assertEqual(result.overview, 'Simple project')
        # Evidence should be empty dict (all conditions failed)
        self.assertIsInstance(result.evidence, dict)

    def test_overview_includes_contributor_count(self):
        """Team context appears in overview when contributor_count > 1."""
        analysis = {
            'resume_item': {
                'project_name': 'Team Project',
                'summary': 'Built by a team.',
                'skills': [],
                'evidence': {
                    'duration': '6 months',
                    'contributor_count': 3,
                    'doc_metrics': [],
                    'doc_key_points': [],
                    'doc_types_found': [],
                    'contributor_breakdown': {},
                    'test_file_count': 0,
                },
            },
        }
        result = build_portfolio_showcase(analysis)
        self.assertIn('3 contributors', result.overview)
        self.assertIn('6 months', result.overview)


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
                
    def test_load_portfolio_showcase_raises_on_corrupt_yaml(self):
        """Test that corrupted YAML raises ValueError."""
        with TemporaryDirectory() as tmp_dir:
            override_path = Path(tmp_dir) / "Corrupt_Project.yaml"
            # Write invalid YAML (unclosed bracket)
            override_path.write_text(
                "project:\n"
                "  title: [unclosed bracket\n",
                encoding="utf-8",
            )

            with patch(
                "src.reporting.portfolio_service._portfolio_override_path",
                return_value=override_path,
            ):
                with self.assertRaises(ValueError) as context:
                    load_portfolio_showcase("Corrupt Project")
                
                self.assertIn("Could not parse portfolio overrides", str(context.exception))    

    def test_save_project_role_override_raises_on_write_failure(self):
        """Test that write failure raises OSError."""
        with TemporaryDirectory() as tmp_dir:
            override_path = Path(tmp_dir) / "nonexistent_dir" / "Project.yaml"
            # Don't create the parent directory - write should fail

            with patch(
                "src.reporting.portfolio_service._portfolio_override_path",
                return_value=override_path,
            ):
                with self.assertRaises(OSError) as context:
                    save_project_role_override("Project", "Developer")
                
                self.assertIn("Could not save portfolio overrides", str(context.exception))

if __name__ == '__main__':
    unittest.main()