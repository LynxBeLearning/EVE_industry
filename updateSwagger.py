
import subprocess
import shutil
import os
import time

if os.path.isdir('swagger_client'):
    shutil.rmtree('swagger_client')


#generate swagger_client
command = ('java -jar swagger-codegen-cli.jar generate '
           '-i https://esi.tech.ccp.is/latest/swagger.json '
           '-l python '
           '-o swagger_client')
print(f"executing command: {command}")
codeGen = subprocess.run(command, shell = True)
print(codeGen.stdout)

#install the interface
time.sleep(2)
os.chdir("swagger_client")
command = ('python setup.py install --user')
print(f"executing command: {command}")
install = subprocess.run(command, shell = True)
print(install.stdout)


