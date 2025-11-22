import os
import re
from pathlib import Path
import orjson
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM


class codeAnalysisAI():
    """
    This a code analysis engine which deploys the use of
    recursive to scan a project directory, and identify
    the supporting programming languages by file extension,
    which is later send to an LLM(Qwen) using the Ollama system
    returning a structured analysis of the code to be used in
    the system

    :parameter
    - folderPath: Path
        project root folder


    """

    def __init__(self, folderPath):
        """
        Here is the initiation function which creates a list of supported languages that
        the LLM supports for code review
        :param folderPath:
        """
        self.folderPath = Path(folderPath)
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
            "Rust (Solana)": [".rs"]}
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

        self.model = OllamaLLM(model="qwen2.5-coder:1.5b")  # Here we are defining what ollama model to use
        self.prompt = PromptTemplate(
            input_variables=["language", "filepath", "code"],
            template="""
                You are a professional software engineer and code reviewer. 
                You have been given a code file to review in depth, and you MUST respond with ONLY valid strict JSON.

                ❗ ABSOLUTE RULES:
                - Do NOT include ```json or ```python or ``` in your answer.
                - Do NOT include any markdown.
                - Do NOT include explanations outside the JSON.
                - Do NOT include comments of ANY kind.
                - Do NOT use sequences like //, /*, or */ anywhere in the output.
                - Do NOT explain values after commas or in parentheses.
                - Every line MUST be valid strict JSON.
                - Output MUST be PURE JSON only.
                - Violating these rules will break the parser.

                You MUST determine and report algorithmic time and space complexity for the code (based on loops, recursion, data structures, etc.). 
                Use Big-O notation (e.g., "O(n)", "O(n log n)"). If needed, infer reasonable complexity from the structure of the code; otherwise 
                say that the time or space complexity cannot be determined and give the reasons in the "complexity_comments" field.

                Any explanation, note, assumption, or clarification that you might normally write as a comment (for example:
                "Assuming the input file is not empty") MUST be written as plain text INSIDE the "complexity_comments" field.
                You MUST NOT use comment syntax anywhere.

                All fields in the JSON MUST contain meaningful, descriptive content:
                - Do NOT leave any string field as an empty string; if you have little to say, write a short descriptive sentence.
                - Do NOT leave any list field empty; if nothing is present, explain that explicitly
                  (e.g., ["No significant data structures used in this file."]).
                - If a concept does not apply, say so explicitly in that field instead of leaving it blank.

                The JSON output MUST contain EXACTLY the following top-level keys and NO others:
                - "file"
                - "language"
                - "summary"
                - "design_and_architecture"
                - "data_structures_and_algorithms"
                - "control_flow_and_error_handling"
                - "library_and_framework_usage"
                - "code_quality_and_maintainability"
                - "inferred_strengths"
                - "growth_areas"
                - "recommended_refactorings"

                The keys "inferred_strengths", "growth_areas", and "recommended_refactorings" MUST be TOP-LEVEL keys.
                They MUST NOT be placed inside "code_quality_and_maintainability" or any other nested object.

                Here is the required JSON structure (you MUST follow this structure exactly, only changing the empty values):

                {{
                  "file": "{filepath}",
                  "language": "{language}",
                  "summary": "",
                  "design_and_architecture": {{
                    "concepts_observed": [],
                    "analysis": ""
                  }},
                  "data_structures_and_algorithms": {{
                    "structures_used": [],
                    "algorithmic_insights": "",
                    "time_complexity": {{
                      "best_case": "",
                      "average_case": "",
                      "worst_case": ""
                    }},
                    "space_complexity": "",
                    "complexity_comments": ""
                  }},
                  "control_flow_and_error_handling": {{
                    "patterns": [],
                    "error_handling_quality": ""
                  }},
                  "library_and_framework_usage": {{
                    "libraries_detected": [],
                    "experience_inference": ""
                  }},
                  "code_quality_and_maintainability": {{
                    "readability": "",
                    "testability": "",
                    "technical_debt": ""
                  }},
                  "inferred_strengths": [],
                  "growth_areas": [],
                  "recommended_refactorings": []
                }}

                Notes on content:
                - "inferred_strengths" MUST be an array of strings describing strengths you infer from the code.
                - "growth_areas" MUST be an array of strings describing potential improvement areas.
                - "recommended_refactorings" MUST be an array of strings, each describing a concrete refactoring or improvement.

                Now analyze this file deeply and return ONLY the JSON with all fields filled with meaningful content:

                Code:
                {code}
                """
        )

        self.max_chars_per_file = 40_000

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
        return any(part in self.ignore_dirs for part in path.parts)

    def _clean_model_output(self, text: str) -> str:
        """
        Cleans the output of the model by:
        - removing code block fences,
        - extracting the JSON object,
        - stripping JS-style comments (// and /* */),
        - removing trailing commas before } or ] so that json.loads() can parse it.
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
            if cleaned.startswith("```") and cleaned.endswith("```"):
                cleaned = cleaned[3:-3].strip()

        # 2. Extract the first JSON-looking object if wrapped in extra text
        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if json_match:
            cleaned = json_match.group(0).strip()

        # 3. Remove single-line comments: // ...
        cleaned = re.sub(r"//.*?$", "", cleaned, flags=re.MULTILINE)

        # 4. Remove block comments: /* ... */
        cleaned = re.sub(r"/\*[\s\S]*?\*/", "", cleaned)

        # 5. Remove trailing commas before } or ]
        #    e.g.  "foo": "bar", }  ->  "foo": "bar" }
        #          [1, 2, 3, ]      ->  [1, 2, 3 ]
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
        Run deep Qwen-based analysis on all supported source files.

        Parameters
        ----------
        save_json : bool
            If True, save the analysis results to a JSON file in the 'results' directory.

       Returns
       -------
       dict
       A dictionary mapping file paths to the full AI-generated analysis for each file.

       The dictionary has the structure:

      {
        "path/to/file.py": {
            "file": "<absolute file path>",
            "language": "<Detected programming language>",
            "summary": "<Short summary of the file>",

            "design_and_architecture": {
                "concepts_observed": [ ... ],
                "analysis": "<Explanation of design patterns, structure, and architecture>"
            },

            "data_structures_and_algorithms": {
                "structures_used": [ ... ],
                "algorithmic_insights": "<Description of algorithmic behaviour>",
                "time_complexity": {
                    "best_case": "O(?)",
                    "average_case": "O(?)",
                    "worst_case": "O(?)"
                },
                "space_complexity": "O(?)",
                "complexity_comments": "<Reasoning for complexity values>"
            },

            "control_flow_and_error_handling": {
                "patterns": [ ... ],
                "error_handling_quality": "<Quality of try/except or lack thereof>"
            },

            "code_quality_and_maintainability": {
                "readability": "<Readability score/comment>",
                "technical_debt": "<Refactoring opportunities>",
                "testability": "<How easily this code can be tested>"
            },

            "library_and_framework_usage": {
                "libraries_detected": [ ... ],
                "experience_inference": "<Inference of experience based on library use>"
            },

            "inferred_strengths": [ ... ],
            "growth_areas": [ ... ],
            "recommended_refactorings": [ ... ]
        },

        ...

    }
        """
        results = {}
        """Run deep Qwen-based analysis on all supported source files."""
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

            final_prompt = self.prompt.format(
                language=language_label,
                filepath=str(file_path),
                code=code,
            )

            print(f"\n\n==================== Analyzing: {file_path} ({language_label}) ====================\n")

            try:
                response = self.model.invoke(final_prompt)
                cleaned_response = self._clean_model_output(response)
            except Exception as e:
                print(f"Error calling model on {file_path}: {e}")
                continue

            print(response)
            try:
                parsed = orjson.loads(cleaned_response)
                results[str(file_path)] = parsed


            except Exception as e:
                print(f"❌ JSON parsing failed for {file_path}: {e}")
                print("Model Output:")
                print(response)
                continue

            print("\n" + "=" * 100 + "\n")

        if save_json:
            self.save_all_results(results)

        return results




