"""
Essential tests for portfolio showcase functionality.

This module contains 5 core tests for portfolio showcase generation,
display, PDF data preparation, and integration.
"""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
import src.reporting.portfolio as portfolio_mod

from src.core.portfolio_service import (
    PortfolioData,
    display_portfolio_showcase,
    build_portfolio_showcase,
)

class TestPortfolioData:
    """Test suite for PortfolioData class."""

    def test_portfolio_data_initialization(self):
        """Test PortfolioData initializes with correct attributes."""
        portfolio_showcase = {
            'title': 'Test Project',
            'overview': 'This is a test project',
            'skills': ['Python', 'JavaScript'],
            'technical_highlights': ['Highlight 1', 'Highlight 2'],
            'design_quality': {
                'oop_comment': 'Well-structured code',
                'oop_rating': 'EXCELLENT'
            }
        }
        analysis = {
            'resume_item': {
                'frameworks': ['Django', 'React']
            }
        }

        portfolio_data = PortfolioData(portfolio_showcase, analysis)

        assert portfolio_data.project_title == 'Test Project'
        assert portfolio_data.one_sentence_summary == 'This is a test project'
        assert portfolio_data.detailed_summary == 'This is a test project'
        assert portfolio_data.key_skills_used == ['Python', 'JavaScript']
        assert portfolio_data.tech_stack == 'Django, React'
        assert portfolio_data.key_responsibilities == ['Highlight 1', 'Highlight 2']
        assert portfolio_data.impact == 'Well-structured code'

class TestDisplayPortfolioShowcase:
    """Test suite for display_portfolio_showcase function."""

    def test_display_portfolio_showcase_full(self, capsys):
        """Test full portfolio showcase display with all sections."""
        ps = {
            'title': 'Sample Project',
            'role': 'Lead Developer',
            'overview': 'An excellent sample project',
            'technical_highlights': ['Feature 1', 'Feature 2'],
            'design_quality': {
                'oop_rating': 'GOOD',
                'oop_comment': 'Well designed',
                'inheritance_classes': 15,
                'max_loop_depth': 3
            },
            'evidence': {
                'files_analyzed': 50,
                'total_functions': 200,
                'collection_literals': 150
            },
            'skills': ['Python', 'SQL'],
            'contributors': ['Alice', 'Bob']
        }

        display_portfolio_showcase(ps)
        captured = capsys.readouterr().out

        assert 'PORTFOLIO SHOWCASE' in captured
        assert 'Sample Project' in captured
        assert 'Lead Developer' in captured
        assert 'Overview:' in captured
        assert 'Technical Highlights:' in captured
        assert 'Feature 1' in captured
        assert 'Design Quality:' in captured
        assert 'Evidence:' in captured
        assert 'Skills:' in captured
        assert 'Contributors:' in captured

class TestBuildPortfolioShowcase:
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
        portfolio_yaml = {}

        result = build_portfolio_showcase(analysis, portfolio_yaml)

        assert result['title'] == 'Full Stack App'
        assert result['overview'] == 'A complete application'
        assert result['skills'] == ['Python', 'JavaScript']
        assert '50 classes across multiple languages' in result['technical_highlights'][0]
        assert result['design_quality']['oop_rating'] == 'GOOD'
        assert result['design_quality']['oop_comment'] == 'Well-structured'
        assert result['design_quality']['max_loop_depth'] == 3
        assert result['evidence']['files_analyzed'] == 75
        assert result['evidence']['total_functions'] == 200
        assert result['evidence']['collection_literals'] == 210
        assert 'Alice' in result['contributors']
        assert 'Bob' in result['contributors']

class TestPortfolioDisplay:
    """Test suite for portfolio display and PDF generation."""

    def test_display_portfolio_with_showcase_format(self, monkeypatch, tmp_path, capsys):
        """Test that new portfolio_showcase format is displayed correctly."""
        ctx = SimpleNamespace(legacy_save_dir=tmp_path / "User_config_files", external_consent=False)
        ctx.legacy_save_dir.mkdir(parents=True)
        
        data = {
            "project_root": "/tmp/demo",
            "resume_item": {
                "project_name": "Test Project",
                "frameworks": ["Django"],
                "skills": ["Python"],
            },
            "portfolio_showcase": {
                "title": "Showcase Project",
                "role": "Developer",
                "overview": "A well-designed project",
                "technical_highlights": ["Scalable architecture", "Clean code"],
                "design_quality": {
                    "oop_rating": "GOOD",
                    "oop_comment": "Well structured"
                },
                "evidence": {
                    "files_analyzed": 50,
                    "total_functions": 150
                },
                "skills": ["Python", "Django"],
                "contributors": ["Alice", "Bob"]
            }
        }
        file_path = tmp_path / "analysis.json"
        file_path.write_text(portfolio_mod.json.dumps(data))

        # Mock the input to answer "n" to PDF generation
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        portfolio_mod.display_portfolio_and_generate_pdf(file_path, ctx)
        out = capsys.readouterr().out

        assert "PORTFOLIO SHOWCASE" in out
        assert "Showcase Project" in out
        assert "Developer" in out
        assert "Overview:" in out
        assert "Technical Highlights:" in out
        assert "Design Quality:" in out

    def test_portfolio_data_creation_in_pdf_generation(self, monkeypatch, tmp_path, capsys):
        """Test that PortfolioData is created correctly for PDF generation."""
        ctx = SimpleNamespace(legacy_save_dir=tmp_path / "User_config_files", external_consent=False)
        ctx.legacy_save_dir.mkdir(parents=True)
        
        data = {
            "resume_item": {
                "frameworks": ["React", "Node.js"]
            },
            "portfolio_showcase": {
                "title": "Web App",
                "overview": "A web application",
                "skills": ["JavaScript", "CSS"],
                "technical_highlights": ["Responsive design"],
                "design_quality": {"oop_comment": "Good design"}
            }
        }
        file_path = tmp_path / "analysis.json"
        file_path.write_text(portfolio_mod.json.dumps(data))

        # Mock input to start PDF generation
        def mock_input(prompt):
            if "PDF?" in prompt:
                return "y"
            elif "folder" in prompt:
                return str(tmp_path)
            elif "name" in prompt:
                return "test"
            return ""
        
        monkeypatch.setattr('builtins.input', mock_input)
        
        # Mock SimpleResumeGenerator to capture the data
        captured_data = {}
        
        class MockGenerator:
            def __init__(self, folder, data, fileName):
                captured_data['data'] = data
            
            def display_and_run(self, portfolio_only=False):
                pass
        
        monkeypatch.setattr(portfolio_mod, 'SimpleResumeGenerator', MockGenerator)

        portfolio_mod.display_portfolio_and_generate_pdf(file_path, ctx)
        
        # Verify PortfolioData was created with correct attributes
        assert 'data' in captured_data
        assert captured_data['data'].project_title == "Web App"
        assert captured_data['data'].tech_stack == "React, Node.js"
        assert "JavaScript" in captured_data['data'].key_skills_used
