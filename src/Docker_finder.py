
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
        try:
            self.client=docker.from_env()
        except (DockerException, APIError):
            self.client=None
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
            for container in self.client.containers.list():

                if "database" in container.name:
                    con=self.client.containers.get(container.name)
            for key,value in con.ports.items():
                if value is not None:
                    self.port_number=value[0]['HostPort']
                    self.host_ip=value[0]['HostIp']

            if self.host_ip =="0.0.0.0":
                self.host_ip="127.0.0.1" or "localhost"

        except (DockerException,APIError,AttributeError):
            self.host_ip="app_database"
            self.port_number="3306"
            pass

        return self.port_number, self.host_ip


