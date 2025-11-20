
import docker

class DockerFinder:
    def __init__(self):
        self.client = docker.from_env()


    def get_mysql_host_port(self):
        try:
            con=None
            port_number=None
            for container in self.client.containers.list():

                if "database" in container.name:
                    con=self.client.containers.get(container.name)
            for key,value in con.ports.items():
                if value is not None:
                    port_number=value[0]['HostPort']


            return port_number
        except Exception as e:
            print(e)



