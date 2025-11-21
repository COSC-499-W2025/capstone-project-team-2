
from src.Docker_finder import DockerFinder
import mysql.connector
from mysql.connector import Error
import unittest


class testDockerFinder(unittest.TestCase):

    def setUp(self):
        self.docker_finder=DockerFinder()
        self.portNumber,self.portHost=self.docker_finder.get_mysql_host_information()


    def test_connection_database_with_retrieved_info(self):
        try:
            conn = mysql.connector.connect(
                    host=self.portHost,
                    port=self.portNumber,
                    database="appdb",
                    user="appuser",
                    password="apppassword"
                )
            self.assertTrue(conn.is_connected())
        except Error:
            self.fail("Failed to connect to MySQL database or docker instance is not running")







