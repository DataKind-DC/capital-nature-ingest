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

#### Lambda Function
A Lambda function can be given the appropriate roles to now launch your template against a given Cloudwatch timer trigger. 

AWS has provided a one-click [Cloudformation solution](https://aws.amazon.com/answers/infrastructure-management/ec2-scheduler/) and a tutorial related to an effort like this is available [here](https://medium.com/@kagemusha_/scraping-on-a-schedule-with-aws-lambda-and-cloudwatch-caf65bc38848) to provide mroe context.

### Cost
One of the most impressive features of this deployment patter is the cost.

On the intended `t2.nano` instance from the above instructions On-Demand Price/hr is at [$0.0058](https://aws.amazon.com/ec2/instance-types/t2/). Assuming Amazon Linux is used as the underlying Operating System, this is actually billed per second. The DataKind Capital Nature team has clocked an average EC2 scrape "job" at approximately 5 minutes from instance start to termination with no other resources utilized or remaining. Under this model, any scrape is looking at approximately $0.0005 per job.

## ECS Method
### In Progress
Please refer to the [docker](/docker/) section of this deployment as a base reference for an Elastic Container Service (ECS) deployment.

## Lambda Method
### In Progress
The whole scraper application can likely be contained and shipped as a Lambda serverless application which provides for incredible flexibility and availability. Anyone willing to take on this effort should consider that Lambda does have a timeout of 15 minutes and doesn't have as much compute available as even some of the smaller EC2 instances. As the number of websites to be scraped grows, this could exceed the capabilities of the Lambda service.

Another way to approach utilizing Lambda is to build a serverless framework to encapsulate each individual source scraper. This would allow each scraper to run asynchronously on an event trigger, which could speed up scraping significantly.