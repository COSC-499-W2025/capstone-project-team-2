import subprocess
import os
from pathlib import Path
import sys
class StartDockerApp:
    def __init__(self):
        self.docker_compose_file_path = Path(__file__).resolve().parent

    def run_app(self):
        print(self.docker_compose_file_path)
        # step 1 we run   docker compose down -v
        print("\nStep 1: Stopping containers...")
        subprocess.run(['docker', 'compose', 'down', '-v'], cwd=self.docker_compose_file_path,
                                           capture_output=True)

        print("\nStep 2: Building images...")
        subprocess.run(['docker', 'compose', 'build', '--no-cache'],
                                           cwd=self.docker_compose_file_path, capture_output=True)

        print("\nStep 3: Starting services...")
        step_3_process = subprocess.run(['docker', 'compose', 'up', '-d'], cwd=self.docker_compose_file_path,
                                            capture_output=True)


        if step_3_process.returncode == 0:
            print("All services up and running")
        else:
            print("Some services failed to start")


    def stop_app(self):
        print("HIT")
        stopped=subprocess.run(['docker', 'compose','stop'], cwd=self.docker_compose_file_path)
        if stopped.returncode == 0:
            print("All services stopped")


if __name__ == "__main__":
    app=StartDockerApp()
    if len(sys.argv)>1:
        if sys.argv[1]=="start":
            app.run_app()
        if sys.argv[1]=="stop":
            app.stop_app()
    else:
        app.run_app()


