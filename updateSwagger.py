
import subprocess
import shutil
import os

if os.path.isdir('swagger_client'):
    shutil.rmtree('swagger_client')

#generate swagger_client
command = ('java -jar swagger-codegen-cli.jar generate '
           '-i https://esi.tech.ccp.is/latest/swagger.json '
           '-l python '
           '-o swagger_client')
codeGen = subprocess.run(command, shell = True)
print(codeGen.stdout)

#install the interface
command = ('python swagger_client/setup.py install --user')
install = subprocess.run(command, shell = True)
print(install.stdout)


