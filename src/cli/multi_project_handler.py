from concurrent.futures import ProcessPoolExecutor
from src.core.app_context import runtimeAppContext
from src.API.analysis_API import perform_analysis_API


class multi_project_handler:

    def multi_project_runner(paths: list, use_ai: bool = False) -> None:
        """
        paths: list of Path objects or strings — zip or directory, the API handles the distinction.
        """

        workers = min(len(paths))
        ordered_results = {str(p): None for p in paths}

        with ProcessPoolExecutor(max_workers=workers) as executor:
                    futures = {}
        for p in paths:
            runtimeAppContext.currently_uploaded_file = p
            futures[executor.submit(perform_analysis_API, use_ai=use_ai)] = str(p)



