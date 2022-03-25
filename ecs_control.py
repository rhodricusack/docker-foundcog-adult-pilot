import boto3
import os
import time

def register_task(client):

    response = client.register_task_definition(
        executionRoleArn='arn:aws:iam::807820536621:role/ecsTaskExecutionRole',
        family='fmriprep-cusacklab',
        taskRoleArn='arn:aws:iam::807820536621:role/cusacklab_elasticcontainer_service_task',
        networkMode='awsvpc',
        containerDefinitions=[
            {
                'name': 'fmriprep-cusacklab',
                'image': "807820536621.dkr.ecr.eu-west-1.amazonaws.com/fmriprep-cusacklab:latest",
                'essential': True,
                'command': [
                    'echo testing',
                ],
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        "awslogs-group": "/ecs/fmriprep-cusacklab",
                        "awslogs-region": "eu-west-1",
                        "awslogs-stream-prefix": "ecs"
                    },
                },
                # 'secrets': [
                #     {
                #         "valueFrom": "arn:aws:secretsmanager:eu-west-1:807820536621:secret:aws/hcp-B9P9EV",
                #         "name": "HCP_KEYS"
                #     }
                # ]
            },
        ],
        requiresCompatibilities=[
            'FARGATE',
        ],
        
        cpu='4096',
        memory='30GB',
        
        tags=[
            {
                'key': 'PrimaryUser',
                'value': 'clionaodoherty' # put your username in here!
            },
            {
                'key': 'SystemComponent',
                'value': 'cusacklab'
            },
        ],
    )

    return response

def run_task(client=None, command=None):
    response = client.run_task(
        cluster='cusacklab-fargate-cluster',
        count=1,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [ "subnet-0e1d25cdf492ff98b", "subnet-06311e579ae22eae0"],
                'securityGroups': ['sg-01743b5e88320d81a'],
                'assignPublicIp': 'ENABLED'
            }
        },
        overrides={
            'containerOverrides': [
                {
                    'name': 'fmriprep-cusacklab',
                    'command': command,
                },
            ],
            'executionRoleArn': 'arn:aws:iam::807820536621:role/ecsTaskExecutionRole',
            'taskRoleArn': 'arn:aws:iam::807820536621:role/cusacklab_elasticcontainer_service_task',
            'ephemeralStorage': {'sizeInGiB': 128},
        },
        platformVersion='LATEST',
        startedBy='neurana-python',
        tags=[
            {
                'key': 'PrimaryUser',
                'value': 'clionaodoherty' # put your username in here!
            },
            {
                'key': 'SystemComponent',
                'value': 'cusacklab'
            },
        ],
        taskDefinition='fmriprep-cusacklab'
    )
    return response

def wait_for_completion(client=None, taskresponses=None, waitfor = 3600, delay=6.0):

    stages = ['PROVISIONING', 'PENDING', 'RUNNING', 'DEPROVISIONING', 'STOPPED']

    for attempt in range(int(waitfor/delay)):  # Twelve hours max
        all_status=[]
        
        for taskresponse in taskresponses:
            if  taskresponse['tasks']:
                cluster = taskresponse['tasks'][0]['clusterArn']
                tasks =[x['taskArn'] for x in taskresponse['tasks']]
                status = client.describe_tasks(cluster = cluster, tasks=tasks)
                for task in status['tasks']:
                    
                    for container in task['containers']:
                        all_status.append({x:container[x] for x in ('lastStatus', 'exitCode', 'reason') if x in container})
                    all_status[-1]['task_lastStatus']=task['lastStatus']

        njobs = len(all_status)
        stage_count = {x:0 for x in stages}

        for task in all_status:
            stage_count[task['lastStatus']] +=1

        exit0 = sum([x['exitCode']==0 for x in all_status if 'exitCode' in x])

        for stage in stages:
            print(f'{stage}:{stage_count[stage]} ', end = ' ')

        print(f'{exit0}/{njobs} completed successfully')
        
        if njobs == stage_count['STOPPED']:
            print(f'All jobs have stopped, {exit0} successfully and {len(all_status)-exit0} with errors')
            return
        time.sleep(delay)
