from concurrent.futures import ProcessPoolExecutor


class multi_project_handler:

    def multi_project_runner(paths: list, use_ai: bool = False) -> None:

        workers = min(len(paths))
