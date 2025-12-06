
from src.Docker_finder import DockerFinder
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
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
        self.ollama_base_url=self.docker_finder.get_ollama_host_Information()

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


    def test_ollama_connection(self):
        """
        This test checks if the Ollama connection is successful and can generate
        a response given a prompt template. The test uses the Ollama model "qwen2.5-coder:1.5b"
        and the temperature is set to 0.1. The test then generates a response to the prompt
        "What is the capital of India?" and checks if the response is a string
        """
        
        ollama_model="qwen2.5-coder:1.5b"
        
        llm=ChatOllama(
                model=ollama_model,
                base_url=self.ollama_base_url,
                temperature=0.1
            )
        prompt=PromptTemplate(
                 
                input_variables=["country"],
                template="""

                        What is the captial of {country}? 

                        """
            )
        chain=prompt | llm
        result=chain.invoke(
                {"country":"India"}
               ).content
        print(result)
        self.assertIsInstance(result,str)

        
if __name__ == '__main__':
    unittest.main(verbosity=2)






