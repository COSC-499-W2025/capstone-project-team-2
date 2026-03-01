import subprocess
import os
from pathlib import Path
import sys
class StartDockerApp:
    def __init__(self):
        self.docker_compose_file_path = Path(__file__).resolve().parent 
        #getting the location of where the docker-compose file is and which folder it's





    def run_app(self):
        print(self.docker_compose_file_path)
        # step 1 we run   docker compose down -v
        print("\nStep 1: Stopping containers...")
        subprocess.run(['docker', 'compose', 'down', '-v'], cwd=self.docker_compose_file_path,
                                           capture_output=True)

        print("\nStep 2: Building images...")
        #Here we are building the Docker containers
        subprocess.run(['docker', 'compose', 'build', '--no-cache'],
                                           cwd=self.docker_compose_file_path, capture_output=True)

        print("\nStep 3: Starting services...")
        #Here we run the initialization and run the Docker containers
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


