"""
Tests for the GenerateLocalResume class which generates resumes
from local OOP analysis data without external AI.
"""

import unittest
from src.Generate_AI_Resume import GenerateLocalResume, ResumeItem, OOPPrinciple


class TestGenerateLocalResume(unittest.TestCase):
    """Test class for GenerateLocalResume."""

    def test_output_is_resume_item(self):
        """Verify generate() returns a ResumeItem object."""
        analysis_data = {
            "resume_item": {
                "languages": ["Python"],
                "frameworks": ["Flask"],
                "skills": ["Web Development"],
                "summary": "A web application project."
            },
            "oop_analysis": {
                "classes": {"count": 5, "avg_methods_per_class": 3.0, "with_inheritance": 2, "with_init": 3},
                "encapsulation": {"classes_with_private_attrs": 1},
                "polymorphism": {"classes_overriding_base_methods": 1, "override_method_count": 2},
                "complexity": {"total_functions": 15, "max_loop_depth": 2},
                "score": {"oop_score": 0.45, "rating": "medium"},
                "narrative": {
                    "oop": "The project shows moderate OOP usage.",
                    "data_structures": "Uses lists and dicts."
                }
            }
        }

        result = GenerateLocalResume(analysis_data, "TestProject").generate()

        self.assertIsInstance(result, ResumeItem)
        self.assertEqual(result.project_title, "TestProject")

    def test_oop_principles_are_oop_principle_objects(self):
        """Verify oop_principles_detected contains OOPPrinciple objects."""
        analysis_data = {
            "resume_item": {"languages": ["Java"], "frameworks": [], "skills": []},
            "oop_analysis": {
                "classes": {"count": 3, "avg_methods_per_class": 2.0, "with_inheritance": 1, "with_init": 2},
                "encapsulation": {"classes_with_private_attrs": 2},
                "polymorphism": {"classes_overriding_base_methods": 1, "override_method_count": 1},
                "complexity": {"total_functions": 10, "max_loop_depth": 1},
                "score": {"oop_score": 0.5, "rating": "medium"},
                "narrative": {}
            }
        }

        result = GenerateLocalResume(analysis_data, "JavaProject").generate()

        self.assertIsInstance(result.oop_principles_detected, dict)
        for name, principle in result.oop_principles_detected.items():
            self.assertIsInstance(principle, OOPPrinciple)
            self.assertIsInstance(principle.present, bool)
            self.assertIsInstance(principle.description, str)
            self.assertIsInstance(principle.code_snippets, list)

    def test_tech_stack_combines_languages_and_frameworks(self):
        """Verify tech_stack includes both languages and frameworks."""
        analysis_data = {
            "resume_item": {
                "languages": ["Python", "JavaScript"],
                "frameworks": ["Django", "React"],
                "skills": []
            },
            "oop_analysis": {
                "classes": {"count": 0},
                "encapsulation": {},
                "polymorphism": {},
                "complexity": {},
                "score": {"oop_score": 0, "rating": "low"},
                "narrative": {}
            }
        }

        result = GenerateLocalResume(analysis_data, "FullStackApp").generate()

        self.assertIn("Python", result.tech_stack)
        self.assertIn("JavaScript", result.tech_stack)
        self.assertIn("Django", result.tech_stack)
        self.assertIn("React", result.tech_stack)

    def test_responsibilities_generated_from_class_count(self):
        """Verify responsibilities include class design info when classes exist."""
        analysis_data = {
            "resume_item": {"languages": ["C"], "frameworks": [], "skills": []},
            "oop_analysis": {
                "classes": {"count": 4, "avg_methods_per_class": 2.5, "with_inheritance": 0, "with_init": 2},
                "encapsulation": {"classes_with_private_attrs": 0},
                "polymorphism": {"classes_overriding_base_methods": 0, "override_method_count": 0},
                "complexity": {"total_functions": 8, "max_loop_depth": 1},
                "score": {"oop_score": 0.1, "rating": "low"},
                "narrative": {}
            }
        }

        result = GenerateLocalResume(analysis_data, "CProject").generate()

        self.assertTrue(len(result.key_responsibilities) > 0)
        # Should mention the 4 classes
        responsibilities_text = " ".join(result.key_responsibilities)
        self.assertIn("4", responsibilities_text)

    def test_inheritance_detected_sets_principle_present(self):
        """Verify inheritance principle is marked present when classes inherit."""
        analysis_data = {
            "resume_item": {"languages": ["Python"], "frameworks": [], "skills": []},
            "oop_analysis": {
                "classes": {"count": 2, "avg_methods_per_class": 2.0, "with_inheritance": 1, "with_init": 1},
                "encapsulation": {"classes_with_private_attrs": 0},
                "polymorphism": {"classes_overriding_base_methods": 0, "override_method_count": 0},
                "complexity": {"total_functions": 4, "max_loop_depth": 0},
                "score": {"oop_score": 0.2, "rating": "low"},
                "narrative": {}
            }
        }

        result = GenerateLocalResume(analysis_data, "InheritanceProject").generate()

        self.assertTrue(result.oop_principles_detected["inheritance"].present)
        self.assertIn("1", result.oop_principles_detected["inheritance"].description)

    def test_encapsulation_detected_sets_principle_present(self):
        """Verify encapsulation principle is marked present when private attrs exist."""
        analysis_data = {
            "resume_item": {"languages": ["Python"], "frameworks": [], "skills": []},
            "oop_analysis": {
                "classes": {"count": 1, "avg_methods_per_class": 3.0, "with_inheritance": 0, "with_init": 1},
                "encapsulation": {"classes_with_private_attrs": 1},
                "polymorphism": {"classes_overriding_base_methods": 0, "override_method_count": 0},
                "complexity": {"total_functions": 3, "max_loop_depth": 0},
                "score": {"oop_score": 0.25, "rating": "low"},
                "narrative": {}
            }
        }

        result = GenerateLocalResume(analysis_data, "EncapsulatedProject").generate()

        self.assertTrue(result.oop_principles_detected["encapsulation"].present)

    def test_polymorphism_detected_sets_principle_present(self):
        """Verify polymorphism principle is marked present when methods are overridden."""
        analysis_data = {
            "resume_item": {"languages": ["Java"], "frameworks": [], "skills": []},
            "oop_analysis": {
                "classes": {"count": 2, "avg_methods_per_class": 2.0, "with_inheritance": 1, "with_init": 2},
                "encapsulation": {"classes_with_private_attrs": 0},
                "polymorphism": {"classes_overriding_base_methods": 1, "override_method_count": 2},
                "complexity": {"total_functions": 4, "max_loop_depth": 0},
                "score": {"oop_score": 0.3, "rating": "medium"},
                "narrative": {}
            }
        }

        result = GenerateLocalResume(analysis_data, "PolymorphicProject").generate()

        self.assertTrue(result.oop_principles_detected["polymorphism"].present)
        self.assertIn("2", result.oop_principles_detected["polymorphism"].description)

    def test_high_oop_score_adds_design_skills(self):
        """Verify high OOP score adds Object-Oriented Design to skills."""
        analysis_data = {
            "resume_item": {"languages": ["Python"], "frameworks": [], "skills": ["Python"]},
            "oop_analysis": {
                "classes": {"count": 10, "avg_methods_per_class": 5.0, "with_inheritance": 5, "with_init": 8},
                "encapsulation": {"classes_with_private_attrs": 6},
                "polymorphism": {"classes_overriding_base_methods": 4, "override_method_count": 8},
                "complexity": {"total_functions": 50, "max_loop_depth": 2},
                "score": {"oop_score": 0.75, "rating": "high"},
                "narrative": {}
            }
        }

        result = GenerateLocalResume(analysis_data, "WellDesignedProject").generate()

        self.assertIn("Object-Oriented Design", result.key_skills_used)
        self.assertIn("Software Architecture", result.key_skills_used)

    def test_empty_oop_analysis_handles_gracefully(self):
        """Verify empty/minimal OOP analysis doesn't crash."""
        analysis_data = {
            "resume_item": {"languages": [], "frameworks": [], "skills": []},
            "oop_analysis": {
                "classes": {},
                "encapsulation": {},
                "polymorphism": {},
                "complexity": {},
                "score": {},
                "narrative": {}
            }
        }

        result = GenerateLocalResume(analysis_data, "EmptyProject").generate()

        self.assertIsInstance(result, ResumeItem)
        self.assertEqual(result.project_title, "EmptyProject")
        self.assertTrue(len(result.key_responsibilities) > 0)  # Should have fallback

    def test_summary_used_as_one_sentence_summary(self):
        """Verify resume_item summary is used as one_sentence_summary."""
        analysis_data = {
            "resume_item": {
                "languages": ["Python"],
                "frameworks": [],
                "skills": [],
                "summary": "Built a CLI tool for data analysis."
            },
            "oop_analysis": {
                "classes": {"count": 1},
                "encapsulation": {},
                "polymorphism": {},
                "complexity": {},
                "score": {"oop_score": 0.1, "rating": "low"},
                "narrative": {}
            }
        }

        result = GenerateLocalResume(analysis_data, "CLITool").generate()

        self.assertEqual(result.one_sentence_summary, "Built a CLI tool for data analysis.")


if __name__ == "__main__":
    unittest.main()
