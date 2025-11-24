
import docker
from docker.errors import DockerException,APIError
class DockerFinder:
    def __init__(self):
        """
        Initialize a DockerFinder instance.

        Creates a Docker client using `from_env` method and sets the
        `port_number` and `host_ip` attributes to None.

        :return: None
        """
        # Create a Docker client
        try:
            # Create a Docker client from environment variables
            self.client=docker.from_env()
        except (DockerException, APIError):
            # Set client to None if an error occurs
            self.client=None
        # Initialize port_number and host_ip to None
        self.port_number=None
        self.host_ip=None

    def get_mysql_host_information(self):
        """
        Attempts to find the host IP and port number associated with the MySQL database container.

        Iterates over all running containers and checks if the container's name contains "database".
        If such a container is found, it retrieves the HostPort and HostIp from the container's ports.

        If the retrieved HostIp is "0.0.0.0", it replaces it with "127.0.0.1" or "localhost".

        Returns a tuple containing the port number and host IP, or raises an exception if it fails to do so.

        :return: tuple containing port number and host IP
        :rtype: tuple
        """
        try:
            con=None
            # Iterate over all running containers
            for container in self.client.containers.list():

                # Check if the container's name contains "database"
                if "database" in container.name: 
                    # get the container
                    con=self.client.containers.get(container.name)
            # Iterate over the container's ports
            # key is the container's port, value is a list of dictionaries containing the host's IP and port
            for key,value in con.ports.items():
                if value is not None:
                    # retrieves the HostPort and HostIp from the container's ports
                    self.port_number=value[0]['HostPort']
                    self.host_ip=value[0]['HostIp']
            
            # Check if the retrieved HostIp is "0.0.0.0" if so set hostip to 127.0.0.1 or localhost
            if self.host_ip =="0.0.0.0":
                self.host_ip="127.0.0.1" or "localhost"
        #Fallback if docker is running but through the container
        except AttributeError:
            # Set host_ip to "app_database" and port_number to "3306" as a fallback
            self.host_ip="app_database"  # name of the MySQL database container
            self.port_number="3306"  # port number of the MySQL database container
            pass

        return self.port_number, self.host_ip