
import docker
import socket
class DockerFinder:
    def __init__(self):
        self.client = docker.from_env()
        self.port_number=None
        self.host_ip=None




    def get_mysql_host_port(self):
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


            return self.port_number,self.host_ip
        except Exception as e:
            print(e)


