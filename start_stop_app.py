import subprocess
import os
from pathlib import Path
import sys
class StartDockerApp:
    def __init__(self):
        self.docker_compose_file_path = Path(__file__).resolve().parent 
        #getting the location of where the docker-compose file is and which folder it's

    def run_app(self):
        print(f"Working directory: {self.docker_compose_file_path}")

        # Step 1: Stop containers
        print("\nStep 1: Stopping containers...")
        subprocess.run(['docker', 'compose', 'down', '-v'],
                       cwd=self.docker_compose_file_path)

        # Step 2: Build images
        print("\nStep 2: Building images...")
        subprocess.run(['docker', 'compose', 'build', '--no-cache'],
                       cwd=self.docker_compose_file_path)

        # Step 3: Start database
        print("\nStep 3: Starting database...")
        subprocess.run(['docker', 'compose', 'up', '-d', 'app_database'],
                       cwd=self.docker_compose_file_path)

        # Step 4: Run tests
        print("\nStep 4: Running tests...")
        subprocess.run(['docker', 'compose', 'run', '--rm', 'test'],
                       cwd=self.docker_compose_file_path)

        # Step 5: Start main app
        print("\nStep 5: Starting services...")
        step_5_process = subprocess.run(
            ['docker', 'compose', 'run', '--rm', '--service-ports', 'app'],
            cwd=self.docker_compose_file_path
        )

        if step_5_process.returncode == 0:
            print("\n✓ All services completed successfully")
        else:
            print("\n✗ Some services failed")


    def stop_app(self):
        print("HIT")
        stopped=subprocess.run(['docker', 'compose','stop'], cwd=self.docker_compose_file_path)
        if stopped.returncode == 0:
            print("All services stopped")


if __name__ == "__main__":
    """
    Here we are running the docker-compose file
    through the command line where the following commands
    do the following
    - start_stop_app start: Start the docker instance process
    - start_stop_app stop: Stop the docker instance process
    """
    app=StartDockerApp()
    if len(sys.argv)>1:
        if sys.argv[1]=="start":
            app.run_app()
        if sys.argv[1]=="stop":
            app.stop_app()
    else:
        app.run_app()


