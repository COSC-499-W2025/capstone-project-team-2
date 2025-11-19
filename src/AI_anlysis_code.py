from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
import os
from pathlib import Path





class code_anlysis_AI():
    def __init__(self,folderPath):
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
            "dist", "build",".git",".idea",".vscode",
            ".pytest_cache",".mypy_cache","__pycache__",
        }
        for lang, suffixes in self.qwen_languages_with_suffixes.items():
            for suffix in suffixes:
                self.suffix_to_languages.setdefault(suffix, set()).add(lang)


        self.model=OllamaLLM(model="qwen2.5-coder:7b")
        self.prompt = PromptTemplate(
            input_variables=["language", "filepath", "code"],
            template="""
        You MUST respond with ONLY valid JSON.

        ❗ ABSOLUTE RULES:
        - Do NOT include ```json or ``` in your answer.
        - Do NOT include markdown.
        - Do NOT include explanations.
        - Do NOT include comments.
        - Output MUST be PURE JSON.
        - Violating these rules will break the parser.

        Here is the required JSON structure:

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

        Now analyze this file deeply and return ONLY the JSON:

        Code:
        {code}
        """
        )

        self.max_chars_per_file=40_000




    def _get_suffix_key(self,path:Path)->str:
        if path.name in ("Dockerfile","Makefile"):
            return path.name



        return path.suffix

    def _is_ignored(self, path: Path) -> bool:
        return any(part in self.ignore_dirs for part in path.parts)

    def read_code_file(self):
        for file_path in self.folderPath.rglob("*"):
            if not file_path.is_file():
                continue

            if any(ignored in file_path.parts for ignored in self.ignore_dirs):
                continue

            suffix_key=self._get_suffix_key(file_path)
            if suffix_key in self.suffix_to_languages:
                languages = self.suffix_to_languages[suffix_key]
                print(f"{file_path} -> {', '.join(sorted(languages))}")




    def run_analysis(self):
        results={}
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
            except Exception as e:
                print(f"Error calling model on {file_path}: {e}")
                continue

            print(response)
            results[str(file_path)] = response
            print("\n" + "=" * 100 + "\n")
        return results




test=code_anlysis_AI(r"D:\UBCO\COSC_344")
data=test.run_analysis()
print(data)

for info in data:
    print(info)
