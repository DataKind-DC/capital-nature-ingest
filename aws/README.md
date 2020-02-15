# Deploying on AWS

This scraper can be deployed in a cost-effective and operationally excellent way on all major Cloud infrastructure providers, or even on your own internal infrastructure as the only underlying requirements are python and retrieving API Tokens for the necessary calendar endpoints.

## EC2 Method

The simplest method to setup and maintain is utilizing a Elastic Cloud Compute (EC2) instance with an IAM role attached that will allow the EC2 instance to do a couple of things:
1. Prepare the EC2 to run the scraper
2. Run the scraper code
3. Upload the calendar csvs to S3 object storage

From here the .csv files can either be retrieved from the intended S3 bucket after their updated cadence ([WinSCP](https://winscp.net/eng/docs/guide_amazon_s3) makes this really simple), sent as a [presigned s3 url](https://docs.aws.amazon.com/cli/latest/reference/s3/presign.html) to an intended recipient for download (possible utilizing the [SES](https://aws.amazon.com/ses/) email service), or possibly even implemented directly into the intended calendar service.

### Setup

#### IAM

From your AWS IAM console, create a Role, this case we'll call it `ingester`.
![role_create](/aws/img/create_role.png)
- For `AWS service` select `EC2`
- Click `Next: Permissions`
- Search for `AmazonS3FullAccess` and select that policy to be attached.
    - You can and should use a more granular policy to write to only a particular bucket but for the purposes of this MVP we'll utilize a higher-permission policy.
- Select `Next: Tags`
- Select `Next: Review`
- Give the role a `Role name`, in this case we'll go for `ingester`.

#### Launch Template
From the AWS EC2 Console create a new Launch Template
![launch_template](/aws/img/launch_templates.png)
Fill out the following items:
- Launch template name - in this MCP we'll call it `ingester`
- AMI - Amazon Linux 2 AMI (HVM), SSD Volume Type
- Instance type - t2.nano
- Networking platform - EC2-Classic
- Availability Zonen - Pick from whatever is available
- Security Groups - default

Dropdown "Advanced details" and input:
- IAM Instance profile - The name of the role previously created, this case `ingester`
- Shutdown behavior - Terminate
- Termination protection - Disable
- User data - copy and paste the `/aws/ec.sh` file in this project here, ensuring that you modify the necessary parameters.

At this point you're pretty much done and you have options to run the EC2 instances on a scheduled cadence.

#### Auto Scaling Group

You can set up Scheduled Actions with an Auto Scaling Group in the EC2 console that will spin up a single instance and then destroy all instances after a specified timeline. With the startup scripts in place, this will ensure that the scraper runs on a cadence that is easily set with a cron job. 

In the below example, an autoscale group will change the desired capacity to 1 and then back to 0 at 12AM and 12:15AM respectively each Tuesday of the week.
![asg_schedule](/aws/img/asg.png)

## Lambda Function

In this approach, a scheduled Lambda function performs the scrapes and dumps the results to S3.

As with the EC2 approach, the `pandas` and `numpy` dependencies need special treatment, as Lambda and EC2 operate under [Amazon Linux 2](https://aws.amazon.com/amazon-linux-2/). Due to these libraries' C dependencies, versions compiled on Windows, Mac or some other Linux distros won't work in Amazon Linux 2. So, the solution is to build these depenedencies from source within a Docker container running the Amazon Linux 2 environment. Then you can zip those dependencies, export them out of Docker, and incorporate them into a build script for the Lambda/EC2 deployment. This [Medium post](https://medium.com/i-like-big-data-and-i-cannot-lie/how-to-create-an-aws-lambda-python-3-6-deployment-package-using-docker-d0e847207dd6) describes the process in greater detail. TL;DR: the `pandas` and `numpy` dependencies are in `layer/aws-lambda-py3.6-pandas-numpy.zip`.

### Cost

With 2 scrapes a month, total monthly cost comes to $.05. On a new AWS account the Free Tier will cover it.

#### Lambda Costs

With two executions per month using a Lambda allocated 1000 MB memory and a 5-minute (300000 ms) timeout, the cost comes to $.02. If you're using a new AWS account, the free-tier covers this entirely for the first year.

#### S3 Costs

For storage, the number of requests to the bucket will be so miniscule (12 per month if we run the scrapers twice per month) that storage is the only real cost, which comes out to about $.03 for one GB of data.

## ECS Method

### In Progress

Please refer to the [docker](/docker/) section of this deployment as a base reference for an Elastic Container Service (ECS) deployment.
