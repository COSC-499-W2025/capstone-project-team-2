from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from docx import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.output_parsers import JsonOutputParser


class GenerateProjectResume:
    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}

    TEXT_EXTS = {".txt", ".md", ".rst", ".log"}

    CODE_EXTS = {
        ".py", ".ipynb",
        ".php",
        ".js", ".jsx", ".ts", ".tsx",
        ".java",
        ".c", ".h", ".cpp", ".hpp",
        ".cs", ".go", ".rb",
        ".rs", ".swift",
        ".kt", ".kts",
        ".html", ".htm", ".css", ".scss",
        ".xml",
        ".json", ".yml", ".yaml", ".toml", ".ini",
        ".sh", ".bash", ".ps1", ".bat",
        ".lua", ".pl", ".R", ".sql", ".m",
    }



    def __init__(self,folder):
        load_dotenv()
        self.google_model="gemini-2.5-flash"
        self.folder=folder

        self.max_chars: int = 20_000
        self.project_root=Path(self.folder)
        if not self.project_root.exists():
            raise FileNotFoundError(f"No such folder {self.project_root}")

        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if not self.google_api_key:
            raise RuntimeError("Missing GOOGLE_API_KEY in .env file")

        self.llm = ChatGoogleGenerativeAI(
            model=self.google_model,
            google_api_key=self.google_api_key
        )
        self.parser = JsonOutputParser()

        self.langChain_prompt = PromptTemplate.from_template(
            """
        You are an expert technical résumé writer.

        You are given a snapshot of a software project including:
        - file structure
        - code snippets (any language including PHP)
        - documentation (PDF/DOCX/TXT)
        - configuration files

        Return a single JSON object summarizing the entire project:

        {{
          "project_title": "...",
          "one_sentence_summary": "...",
          "detailed_summary": "...",
          "key_responsibilities": [
            "bullet point...",
            "bullet point..."
          ],
          "key_skills_used": [
            "skill...",
            "technology..."
          ],
          "tech_stack": "short paragraph of main technologies",
          "impact": "optional short impact statement"
        }}

        Do NOT output anything except valid JSON.

        PROJECT CONTEXT:
        \"\"\"{project_context}\"\"\"
        """
        )

        self.chain=self.langChain_prompt | self.llm | self.parser


    def _is_text_file(self, path: Path) -> bool:
        try:
            with path.open("rb") as f:
                f.read(2048).decode("utf-8")
            return True
        except Exception:
            return False


    def _classify_file(self, path: Path) -> str:
        file_extension=path.suffix.lower()



        if file_extension in self.IMAGE_EXTS:
            return "ignore"

        if file_extension == ".pdf":
            return "pdf"

        if file_extension == ".docx" or file_extension == '.doc':
            return "docx"

        if file_extension in self.TEXT_EXTS:
            return "text"

        if file_extension in self.CODE_EXTS:
            return "code"

        if self._is_text_file(path):
            return "code"




        return "ignore"


    def _read_file(self,path:Path)->str:
        ftype=self._classify_file(path)
        try:
            if ftype=="pdf":
                pdf_to_read = PyPDFLoader(str(path)).load()
                pdf_content = "\n".join(p.page_content for p in pdf_to_read)
                content=pdf_content
            elif ftype=="docx":
                docx_to_read = Document(str(path))
                doc_content="\n".join(d.text for d in docx_to_read.paragraphs)
                content=doc_content
            elif ftype in {"text", "code"}:
                content=path.read_text(errors="ignore")

            else:
                return ""

            return content
        except Exception:
            return ""

    def _build_context(self):
        pieces: List[str] = [f"ROOT: {self.project_root.resolve()}\n", "FILES:\n"]
        total_length=0
        file_infos=[]

        for f in sorted(self.project_root.glob("**/*")):
            if f.is_file() and self._classify_file(f)!='ignore':
                ftype=self._classify_file(f)
                save_dict={"path":f,"type":ftype}
                file_infos.append(save_dict)
                pieces.append(f"- {f.relative_to(self.project_root)} [{ftype}]\n")
        pieces.append("\nSNIPPETS:\n")


        for info in file_infos:
            path=info.get("path")
            ftype=info.get("type")
            rel=path.relative_to(self.project_root)

            raw=self._read_file(path)
            if not raw.strip():
                continue
            snippet=raw.strip()[:1200]
            block = f"\n=== {rel} [{ftype}] ===\n{snippet}\n"
            if total_length+len(block)>self.max_chars:
                pieces.append("\n[TRUNCATED]\n")
                break

            pieces.append(block)
            total_length+=len(block)

        return "".join(pieces)


    def generate(self)->dict:
        context=self._build_context()
        result=self.chain.invoke({"project_context":context})
        return result


