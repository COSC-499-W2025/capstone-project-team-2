
from src.Docker_finder import DockerFinder
import mysql.connector
from mysql.connector import Error
import unittest


class testDockerFinder(unittest.TestCase):
    """
    This is a test class for DockerFinder class

    This class tests the DockerFinder class which is used to find
    the host IP and port number associated with the MySQL database container.
    """

    def setUp(self):
        """
        This method is called before each test method is run.
        It creates an instance of the DockerFinder class and retrieves
        the host IP and port number associated with the MySQL database container.
        """
        self.docker_finder=DockerFinder()
        self.portNumber,self.portHost=self.docker_finder.get_mysql_host_information()


    def test_connection_database_with_retrieved_info(self):
        """
        This test checks if the connection to the MySQL database is successful
        using the host IP and port number retrieved from the DockerFinder class.
        """
        conn=None

        try:
            conn = mysql.connector.connect(
                    host=self.portHost,
                    port=self.portNumber,
                    database="appdb",
                    user="appuser",
                    password="apppassword"
                )
            self.assertTrue(conn.is_connected())
        except mysql.connector.Error as err:
            self.fail("Failed to connect to MySQL database or docker instance is not running")

        finally:
            if conn is not None and conn.is_connected():
                conn.close()







