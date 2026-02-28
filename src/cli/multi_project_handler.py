from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tqdm import tqdm
from src.core.app_context import runtimeAppContext
from src.API.analysis_API import perform_analysis_API
import os

def single_project_run(args: tuple) -> dict:
    path, use_ai = args
    runtimeAppContext.currently_uploaded_file = Path(path)
    return perform_analysis_API(use_ai=use_ai)

class multi_project_handler:

    def multi_project_runner(paths: list, use_ai: bool = False) -> None:
        workers = min(len(paths), os.cpu_count())
        ordered_results = {str(p): None for p in paths}

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(single_project_run, (p, use_ai)): str(p) for p in paths}

            for future in as_completed(futures):
                path = futures[future]
                try:
                    ordered_results[path] = future.result()
                except Exception as e:
                    ordered_results[path] = {"error": str(e)}
                progress.update(1)
                progress.set_postfix_str(path.split("\\")[-1])

        for path, result in ordered_results.items():
            if result and "error" not in result:
                print(f"{path}: {result['status']}")
            else:
                print(f"[ERROR] {path}: {result.get('error')}")



