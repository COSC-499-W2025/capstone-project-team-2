import os
import re
from pathlib import Path
import orjson
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser






class codeAnalysisAI():
    """
    This a code analysis engine which deploys the use of
    recursive to scan a project directory, and identify
    the supporting programming languages by file extension,
    which is later sent to an LLM(Ollama) using LangChain
    returning a structured analysis of the code to be used in
    the system

    :parameter
    - folderPath: Path
        project root folder
    - model: str (optional)
        Ollama model name (default: "qwen2.5-coder:1.5b")
    """

    def __init__(self, folderPath, model="qwen2.5-coder:1.5b"):
        """
        Here is the initiation function which creates a list of supported languages that
        the LLM supports for code review

        :param folderPath: Path to the project folder
        :param model: Ollama model to use (default: qwen2.5-coder:1.5b)
        """
        self.folderPath = Path(folderPath)


        # Map of languages to file extensions (e.g. ".py" for Python)
        self.qwen_languages_with_suffixes = {
            # -------------------------
            # GENERAL PURPOSE
            # -------------------------
            "Python": [".py"],
            "Java": [".java"],
            "C": [".c", ".h"],
            "C++": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
            "C#": [".cs"],
            "Go": [".go"],
            "Rust": [".rs"],
            "Kotlin": [".kt", ".kts"],
            "Swift": [".swift"],
            "Dart": [".dart"],
            "Ruby": [".rb"],
            "PHP": [".php"],
            "Zig": [".zig"],
            "Nim": [".nim"],
            "Haskell": [".hs"],
            "OCaml": [".ml", ".mli"],
            "F#": [".fs", ".fsi", ".fsx"],
            "Crystal": [".cr"],

            # -------------------------
            # WEB / FRONTEND
            # -------------------------
            "JavaScript": [".js", ".mjs", ".cjs"],
            "TypeScript": [".ts", ".tsx"],
            "HTML": [".html", ".htm"],
            "CSS": [".css"],
            "SCSS": [".scss"],
            "Less": [".less"],
            "Vue": [".vue"],
            "React JSX": [".jsx"],
            "React TSX": [".tsx"],
            "Svelte": [".svelte"],
            "Angular": [".ts", ".html"],

            # -------------------------
            # BACKEND FRAMEWORKS
            # -------------------------
            "Node.js": [".js"],
            "Express": [".js"],
            "Spring": [".java", ".kt"],
            "ASP.NET Core": [".cs"],
            "Rails": [".rb"],
            "Laravel": [".php"],

            # -------------------------
            # MOBILE
            # -------------------------
            "Kotlin (Android)": [".kt"],
            "Swift (iOS)": [".swift"],
            "Objective-C": [".m", ".h"],

            # -------------------------
            # SCRIPTING LANGUAGES
            # -------------------------
            "Bash": [".sh"],
            "Zsh": [".zsh"],
            "PowerShell": [".ps1"],
            "Batch": [".bat", ".cmd"],
            "Lua": [".lua"],
            "Perl": [".pl", ".pm"],

            # -------------------------
            # DATA / AI / SCIENTIFIC
            # -------------------------
            "R": [".r"],
            "Julia": [".jl"],
            "MATLAB": [".m"],
            "Octave": [".m"],

            # -------------------------
            # DATABASE / QUERY
            # -------------------------
            "SQL": [".sql"],
            "PostgreSQL": [".sql"],
            "MySQL": [".sql"],
            "SQLite": [".sql"],
            "MariaDB": [".sql"],
            "T-SQL": [".sql", ".tsql"],
            "PL/SQL": [".pls", ".pks", ".pkb", ".sql"],
            "GraphQL": [".graphql", ".gql"],
            "Cypher": [".cyp", ".cypher"],
            "CQL (Cassandra)": [".cql"],
            "HiveQL": [".hql"],
            "Pig Latin": [".pig"],

            # -------------------------
            # DEVOPS / CLOUD / INFRA
            # -------------------------
            "Dockerfile": ["Dockerfile"],
            "Makefile": ["Makefile"],
            "Terraform (HCL)": [".tf", ".tfvars"],
            "CloudFormation": [".yaml", ".yml", ".json"],
            "Kubernetes": [".yaml", ".yml"],
            "Ansible": [".yaml", ".yml"],

            # -------------------------
            # CONFIG / SERIALIZATION
            # -------------------------
            "JSON": [".json"],
            "YAML": [".yml", ".yaml"],
            "TOML": [".toml"],
            "INI": [".ini"],
            "XML": [".xml"],

            # -------------------------
            # GAME DEVELOPMENT
            # -------------------------
            "Unity C#": [".cs"],
            "Unreal C++": [".cpp", ".h"],
            "GDScript": [".gd"],
            "GLSL": [".glsl", ".vert", ".frag"],
            "HLSL": [".hlsl", ".fx"],
            "ShaderLab": [".shader"],

            # -------------------------
            # SYSTEMS / EMBEDDED / HPC
            # -------------------------
            "Assembly": [".asm", ".s"],
            "ARM Assembly": [".s"],
            "RISC-V Assembly": [".s"],
            "CUDA": [".cu", ".cuh"],
            "OpenCL": [".cl"],
            "Verilog": [".v"],
            "SystemVerilog": [".sv"],
            "VHDL": [".vhd"],
            "Arduino": [".ino"],

            # -------------------------
            # ROBOTICS & INDUSTRIAL
            # -------------------------
            "ROS C++": [".cpp", ".h"],
            "URScript": [".script"],
            "RAPID (ABB)": [".mod", ".sys"],
            "KRL (KUKA)": [".src", ".dat"],

            # -------------------------
            # BLOCKCHAIN / SMART CONTRACT
            # -------------------------
            "Solidity": [".sol"],
            "Vyper": [".vy"],
            "Move": [".move"],
            "Rust (Solana)": [".rs"]
        }

        self.suffix_to_languages = {}
        self.ignore_dirs = {
            "env", "venv", ".venv", "__pycache__",
            "Lib", "site-packages", "node_modules",
            "dist", "build", ".git", ".idea", ".vscode",
            ".pytest_cache", ".mypy_cache", "__pycache__",
        }

        for lang, suffixes in self.qwen_languages_with_suffixes.items():
            for suffix in suffixes:
                self.suffix_to_languages.setdefault(suffix, set()).add(lang)

        # Initialize Ollama model using LangChain
        # Make sure Ollama is running locally (ollama serve)
        # and the model is pulled (ollama pull qwen2.5-coder:7b)
        self.llm = ChatOllama(
            model=model,
            format="json",  # Request JSON output format
            temperature=0.1, # Low temperature for more consistent outputs
            base_url="http://localhost:11434",
        )

        print(f"✓ Initialized Ollama with model: {model}")
        print("  Make sure Ollama is running: ollama serve")
        print(f"  Make sure model is pulled: ollama pull {model}")

        # Initialize JSON output parser
        self.parser = JsonOutputParser()

        # Template for generating code review prompts for AI to follow
        self.prompt = PromptTemplate(
            input_variables=["language", "filepath", "code"],
            template="""You are a senior software architect and code reviewer with 15+ years of experience across multiple domains including system design, performance optimization, and software craftsmanship.

Your task is to conduct a comprehensive technical analysis of the provided code file and return ONLY a valid JSON object.

═══════════════════════════════════════════════════════════════════
🔴 CRITICAL OUTPUT FORMAT RULES - NON-NEGOTIABLE:
═══════════════════════════════════════════════════════════════════
1. Output MUST be pure JSON - no markdown, no code fences, no explanations
2. Do NOT wrap output in ```json or ``` or any other formatting
3. Do NOT include ANY comments (no //, /*, or #)
4. Do NOT add explanatory text before or after the JSON
5. ALL string fields must contain substantive content (never empty strings)
6. ALL array fields must contain items OR explicit explanations like ["No patterns detected in this simple script"]
7. Use proper JSON escaping for quotes and special characters

═══════════════════════════════════════════════════════════════════
📋 ANALYSIS REQUIREMENTS:
═══════════════════════════════════════════════════════════════════

FILE CONTEXT:
- File Path: {filepath}
- Language: {language}

PROVIDE DETAILED ANALYSIS IN THESE AREAS:

1. **SUMMARY**: Write 2-4 sentences explaining what this code does, its role in the system, and key responsibilities.

2. **DESIGN & ARCHITECTURE**:
   - Identify design patterns (e.g., Singleton, Factory, Observer, MVC, Repository)
   - Note architectural concepts (layered, modular, service-oriented, event-driven)
   - Evaluate separation of concerns and cohesion
   - Assess adherence to SOLID principles where applicable

3. **DATA STRUCTURES & ALGORITHMS**:
   - List ALL data structures used (arrays, dictionaries, trees, graphs, queues, stacks, sets, custom classes)
   - Analyze algorithmic approaches (sorting, searching, traversal, recursion, dynamic programming)
   - Calculate time complexity for key operations using Big-O notation:
     * best_case: Most efficient scenario (e.g., "O(1)" for finding first element)
     * average_case: Typical performance (e.g., "O(n log n)" for merge sort)
     * worst_case: Least efficient scenario (e.g., "O(n²)" for nested loops)
   - Calculate space complexity: Memory usage in Big-O (e.g., "O(n)" for array of n elements)
   - Provide reasoning in complexity_comments explaining your calculations

4. **CONTROL FLOW & ERROR HANDLING**:
   - Identify control flow patterns (loops, conditionals, recursion, callbacks, promises, async/await)
   - Evaluate error handling strategy (try-catch blocks, error propagation, validation, defensive programming)
   - Note any edge cases handled or missing
   - Assess robustness and fault tolerance

5. **LIBRARIES & FRAMEWORKS**:
   - List ALL imported libraries, frameworks, and dependencies
   - Assess usage quality: Are they used idiomatically? Are they the right tools?
   - Infer developer experience level based on library choices and usage patterns
   - Note any missing libraries that could improve the code

6. **CODE QUALITY & MAINTAINABILITY**:
   - Readability: Variable naming, code organization, comments, documentation
   - Testability: How easy is it to write unit tests? Is the code modular enough?
   - Technical Debt: Identify code smells, redundancy, overly complex sections, deprecated patterns

7. **STRENGTHS** (Top-level key):
   - List 3-5 specific positive qualities you observe
   - Examples: "Excellent error handling with specific exception types", "Clean separation of concerns", "Efficient algorithm choice for the problem domain"

8. **GROWTH AREAS** (Top-level key):
   - List 3-5 constructive improvement suggestions
   - Examples: "Add input validation", "Extract magic numbers into constants", "Improve naming conventions"

9. **RECOMMENDED REFACTORINGS** (Top-level key):
   - Provide 3-5 specific, actionable refactoring recommendations
   - Examples: "Extract the data processing logic from lines 45-78 into a separate method", "Replace conditional chain with polymorphism or strategy pattern", "Add type hints for better IDE support"

═══════════════════════════════════════════════════════════════════
📐 REQUIRED JSON STRUCTURE:
═══════════════════════════════════════════════════════════════════

Return this exact structure with all fields filled with meaningful analysis:

{{
  "file": "{filepath}",
  "language": "{language}",
  "summary": "2-4 sentence overview of the code's purpose and functionality",
  "design_and_architecture": {{
    "concepts_observed": ["List of design patterns and architectural concepts"],
    "analysis": "Detailed paragraph explaining the architecture, design decisions, and how well the code follows best practices"
  }},
  "data_structures_and_algorithms": {{
    "structures_used": ["List ALL data structures: arrays, dicts, classes, etc."],
    "algorithmic_insights": "Explanation of the algorithmic approach and efficiency considerations",
    "time_complexity": {{
      "best_case": "O(?) with brief explanation",
      "average_case": "O(?) with brief explanation",
      "worst_case": "O(?) with brief explanation"
    }},
    "space_complexity": "O(?) with brief explanation",
    "complexity_comments": "Detailed reasoning for the complexity analysis including key operations analyzed"
  }},
  "control_flow_and_error_handling": {{
    "patterns": ["List of control flow patterns used"],
    "error_handling_quality": "Assessment of error handling: what's done well, what's missing, suggestions"
  }},
  "library_and_framework_usage": {{
    "libraries_detected": ["Complete list of all imports and dependencies"],
    "experience_inference": "Analysis of the developer's experience level based on library usage, coding patterns, and best practices"
  }},
  "code_quality_and_maintainability": {{
    "readability": "Assessment of code readability including naming, structure, and documentation",
    "testability": "Evaluation of how testable the code is and suggestions for improvement",
    "technical_debt": "Identification of code smells, potential issues, and areas needing refactoring"
  }},
  "inferred_strengths": [
    "Specific strength #1 with context",
    "Specific strength #2 with context",
    "Specific strength #3 with context"
  ],
  "growth_areas": [
    "Constructive improvement area #1",
    "Constructive improvement area #2",
    "Constructive improvement area #3"
  ],
  "recommended_refactorings": [
    "Specific refactoring recommendation #1 with line numbers or context",
    "Specific refactoring recommendation #2 with line numbers or context",
    "Specific refactoring recommendation #3 with line numbers or context"
  ]
}}

═══════════════════════════════════════════════════════════════════
📄 CODE TO ANALYZE:
═══════════════════════════════════════════════════════════════════

{code}

═══════════════════════════════════════════════════════════════════
Begin your analysis now. Return ONLY the JSON object, nothing else.
═══════════════════════════════════════════════════════════════════"""
        )

        # Create LangChain chain: prompt -> LLM -> parser
        self.chain = self.prompt | self.llm | self.parser

        self.max_chars_per_file = 40_000

    def _normalize_top_level_fields(self, data: dict) -> dict:
        """
        Ensures inferred_strengths, growth_areas, and recommended_refactorings
        exist at the top level. If the model incorrectly placed them inside
        code_quality_and_maintainability, extract and move them.
        """
        nested = data.get("code_quality_and_maintainability", {})

        # Fields that must be top-level
        required_fields = [
            "inferred_strengths",
            "growth_areas",
            "recommended_refactorings",
        ]

        # Move misplaced fields from nested to top-level
        for field in required_fields:
            # If nested contains the field, move it
            if field in nested and field not in data:
                data[field] = nested.pop(field)

            # If missing entirely, create empty fallback
            if field not in data:
                data[field] = []

        return data

    def _get_suffix_key(self, path: Path) -> str:
        """
        Returns a key based on the suffix of the given path.

        If the filename is "Dockerfile" or "Makefile", returns the filename.
        Otherwise, returns the file suffix (e.g. ".txt", ".py", etc.).
        """
        if path.name in ("Dockerfile", "Makefile"):
            return path.name

        return path.suffix

    def _is_ignored(self, path: Path) -> bool:
        """
        Returns True if the given path is in the ignore_dirs list, False otherwise.
        """
        return any(part in self.ignore_dirs for part in path.parts)

    def _clean_model_output(self, text: str) -> str:
        """
        Clean the raw LLM output so it becomes valid JSON:

        - Strip ```json / ```python / ``` fences
        - Keep only the main JSON object (from first '{' to last '}')
        - Remove all // line comments
        - Remove /* ... */ block comments
        - Merge duplicated recommended_refactorings arrays
        - Fix backslashes in the "file" path so they're valid JSON escapes
        - Remove trailing commas before } or ]
        """
        if not text:
            return text

        cleaned = text.strip()

        # 1. Strip ```json / ```python / ``` fences if present
        fence_pattern = re.compile(r"```(?:json|python)?\s*([\s\S]*?)```", re.IGNORECASE)
        match = fence_pattern.search(cleaned)
        if match:
            cleaned = match.group(1).strip()
        else:
            # Fallback: naked ``` ... ```
            if cleaned.startswith("```") and cleaned.endswith("```"):
                cleaned = cleaned[3:-3].strip()

        # 2. Extract the main JSON-looking object (first '{' to last '}')
        first = cleaned.find("{")
        last = cleaned.rfind("}")
        if first != -1 and last != -1 and last > first:
            cleaned = cleaned[first:last + 1]

        # 3. Remove ALL JS-style // comments aggressively
        cleaned = re.sub(r"//.*", "", cleaned)

        # 4. Remove block comments: /* ... */
        cleaned = re.sub(r"/\*[\s\S]*?\*/", "", cleaned)

        # 5. Merge duplicated array literals for recommended_refactorings
        cleaned = re.sub(
            r'"recommended_refactorings"\s*:\s*\[([^\]]*)\]\s*,\s*\[([^\]]*)\]',
            r'"recommended_refactorings": [\1,\2]',
            cleaned,
            flags=re.DOTALL,
        )

        # 6. Fix invalid backslashes in "file" value
        file_match = re.search(r'"file"\s*:\s*"([^"]*)"', cleaned)
        if file_match:
            original_path = file_match.group(1)
            safe_path = original_path.replace("\\", "\\\\")
            cleaned = (
                    cleaned[: file_match.start(1)]
                    + safe_path
                    + cleaned[file_match.end(1):]
            )

        # 7. Remove trailing commas before } or ]
        cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)

        return cleaned.strip()

    def save_all_results(self, results: dict):
        """
        Saves the analysis results to a JSON file in the 'results' directory.

        Parameters
        ----------
        results : dict
            The analysis results to be saved.

        Returns
        -------
        None
        """
        root_folder = Path(__file__).resolve().parent / "results"
        os.makedirs(root_folder, exist_ok=True)
        with open(root_folder / "analysis_result.json", "wb") as f:
            f.write(
                orjson.dumps(
                    results,
                    option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
                )
            )
        print(f'Analysis result saved to {root_folder}/analysis_result.json')

    def run_analysis(self, save_json=False):
        """
        Run deep Gemini-based analysis on all supported source files.

        Parameters
        ----------
        save_json : bool
            If True, save the analysis results to a JSON file in the 'results' directory.

        Returns
        -------
        dict
            A dictionary mapping file paths to the full AI-generated analysis for each file.
        """
        results = {}

        # Iterate over all files in the folderPath and its subdirectories
        for file_path in self.folderPath.rglob("*"):
            if not file_path.is_file():
                continue

            if self._is_ignored(file_path):
                continue

            suffix_key = self._get_suffix_key(file_path)
            if suffix_key not in self.suffix_to_languages:
                continue

            languages = sorted(self.suffix_to_languages[suffix_key])
            language_label = "/".join(languages)

            try:
                code = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                print(f"Skipping {file_path} (could not read: {e})")
                continue

            if not code.strip():
                continue

            if len(code) > self.max_chars_per_file:
                code = code[: self.max_chars_per_file] + "\n\n# [Truncated for analysis]\n"

            print(f"\n\n==================== Analyzing: {file_path} ({language_label}) ====================\n")

            try:
                # Invoke the LangChain chain (prompt -> LLM -> parser)
                # The chain automatically: formats prompt -> sends to LLM -> parses JSON response
                parsed = self.chain.invoke({
                    "language": language_label,
                    "filepath": str(file_path),
                    "code": code
                })

                # Normalize fields to ensure correct structure
                parsed = self._normalize_top_level_fields(parsed)

                # Store the parsed analysis result
                results[str(file_path)] = parsed

                print(f"✓ Successfully analyzed {file_path}")

            except Exception as e:
                print(f"❌ Error analyzing {file_path}: {e}")
                # Print more detailed error info for debugging
                import traceback
                print(traceback.format_exc())
                continue

            print("\n" + "=" * 100 + "\n")

        if save_json:
            self.save_all_results(results)

        return results


# Example usage
if __name__ == "__main__":
    # Option 1: Use default model (qwen2.5-coder:1.5b)
    analyzer = codeAnalysisAI(r"D:\UBCO\capstone-project-team-2\test\tiny_scripts")

    # Option 2: Specify a different Ollama model
    # analyzer = codeAnalysisAI("path/to/your/project", model="qwen2.5-coder:14b")
    # analyzer = codeAnalysisAI("path/to/your/project", model="codellama:13b")
    # analyzer = codeAnalysisAI("path/to/your/project", model="deepseek-coder:6.7b")

    # Run analysis and save results
    results = analyzer.run_analysis(save_json=True)