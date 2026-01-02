from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

class JavaScriptAnalysisResult:
    """
    Holds aggregated JavaScript analysis metrics for a project.
   
    """

    def __init__(self):
        self.files_analyzed: int = 0
        self.metrics: Dict[str, int] = defaultdict(int)
        self.max_loop_depth: int = 0

class JavaScriptAnalyzer:
    """
    Static analyzer for JavaScript projects.

    """

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.js_files: List[Path] = []
        self.result = JavaScriptAnalysisResult()
   
    def discover_js_files(self) -> None:
        """Discover all JavaScript source files under project root."""
        self.js_files = [
            p for p in self.root.rglob("*.js")
            if "node_modules" not in p.parts
        ]

    def analyze_file(self, path: Path) -> None:
        """
        Analyze a single JavaScript file and update metrics.
        """
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        self.result.files_analyzed += 1

        self._count_constructs(source)
        self._estimate_loop_depth(source)

    def _count_constructs(self, source: str) -> None:
        """Count high-level JavaScript constructs."""
        self.result.metrics["functions"] += source.count("function ")
        self.result.metrics["arrow_functions"] += source.count("=>")
        self.result.metrics["classes"] += source.count("class ")
        self.result.metrics["async_functions"] += source.count("async ")
        self.result.metrics["loops"] += (
            source.count("for ")
            + source.count("while ")
        )

    def _estimate_loop_depth(self, source: str) -> None:
        """
        Approximate max loop nesting depth using brace tracking.
        """
        depth = 0
        max_depth = 0
        for line in source.splitlines():
            if "for " in line or "while " in line:
                depth += 1
                max_depth = max(max_depth, depth)
            if "}" in line and depth > 0:
                depth -= 1

        self.result.max_loop_depth = max(
            self.result.max_loop_depth, max_depth
        )


    def analyze(self) -> Dict[str, Any]:
        """
        Run JavaScript analysis across the project.
        """
        self.discover_js_files()

        for js_file in self.js_files:
            self.analyze_file(js_file)

        return self.to_canonical_report()

    def to_canonical_report(self) -> Dict[str, Any]:
        """
        Convert internal result into canonical analyzer output.
        """
        return {
            "language": "JavaScript",
            "files_analyzed": self.result.files_analyzed,
            "metrics": dict(self.result.metrics),
            "complexity": {
                "max_loop_depth": self.result.max_loop_depth
            },
        }
