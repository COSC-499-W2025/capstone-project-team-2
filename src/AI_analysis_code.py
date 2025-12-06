import os
import re
from pathlib import Path
import orjson
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.Docker_finder import DockerFinder



base_url=DockerFinder().get_ollama_host_Information()

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
        # and the model is pulled (ollama pull qwen2.5-coder:1.5b)
        self.llm = ChatOllama(
            model=model,
            format="json",  # Request JSON output format
            temperature=0.1, # Low temperature for more consistent outputs
            base_url=base_url,
        )

        print(f"✓ Initialized Ollama with model: {model}")
        print("  Make sure Ollama is running: ollama serve")
        print(f"  Make sure model is pulled: ollama pull {model}")

        # Initialize JSON output parser
        self.parser = JsonOutputParser()

        # Template for generating code review prompts for AI to follow
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


""""
if __name__ == "__main__":
    root_folder = Path(__file__).resolve().parent

    instance = codeAnalysisAI(root_folder)
    print(instance.run_analysis())


test=codeAnalysisAI(Path(r""))
test.run_analysis(save_json=True)
"""
