# CloudDeploy
Filipe Borba - 6º Semestre  
Engenharia da Computação Insper  
Computação em Nuvem  

## Sumário

- [Programa](#programa)
- [Como executar](#como-executar)
- [Como utilizar](#como-utilizar)

## Programa

O programa deste repositório criará um load balancer e instâncias (padrão: 3) para servir uma aplicação de armazenamento de tarefas. As tarefas podem ser listadas, adicionadas, deletadas ou atualizadas. É uma demonstração simples de serviço distribuído.

## Como executar

Obs: todo o desenvolvimento e testes foram realizados no Ubuntu 18.04

Para executar o programa, primeiro, faça um clone do repositório e instale o [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#installation). Após isso, adicione no ```aws.json``` o AwsAccessKeyId e AwsSecretAccessKey para que o programa consiga se comunicar com o AWS EC2.

Para iniciar tudo, use o seguinte comando, com argumentos opcionais:

`python3 setup.py OWNER_NAME KEY_PAIR_NAME SEC_GROUP_NAME INSTANCE_COUNT`

* OWNER_NAME: Nome do dono das instâncias para diferenciar no AWS EC2. Padrão: Tarefas_Demo
* KEY_PAIR_NAME: Nome do key pair para entrar nas instâncias. As chaves são salvas automaticamente na pasta do projeto em um arquivo .pem. Padrão: "Tarefa_Demo_Keypair"
* SEC_GROUP_NAME: Nome do Security Group relacionado às instâncias. Padrão: Tarefas_Demo_Secgroup
* INSTANCE_COUNT: Número de instâncias que devem ficar ativas para servir o serviço. Padrão: 3

Aguarde um pouco até todas as instâncias começarem para utilizar.

## Como utilizar

Depois de tudo subindo e rodando, é possível utilizar o script ```tarefa``` para mandar requisições ao serviço. Para tanto, precisamos do IP do Load Balancer (recebido quando o ```setup.py``` termina) e adicionar a pasta ao PATH do Ubuntu.
  
Para adicionar a pasta do projeto ao PATH, utilize o comando ```pwd``` para ver o caminho do diretório, copie o resultado e depois use o comando ```export PATH=$PATH:ResultadoCopiadoCtrl+V```.
  
Depois, copie o IP do Load Balancer e no terminal rode o comando ```export APP_URL=IpDoLoadBalancer:5000```.
Pronto! Agora você pode usar o serviço pelo terminal. Use o comando ```tarefa -h``` para saber como usar o script!

