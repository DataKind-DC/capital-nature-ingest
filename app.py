import os

from aws_cdk import (
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_s3 as s3,
    core
)


class CapitalNatureStack(core.Stack):
    def __init__(self, app: core.App, id: str) -> None:
        super().__init__(app, id)

        EVENTBRITE_TOKEN = os.environ.get('EVENTBRITE_TOKEN')
        NPS_KEY = os.environ.get('NPS_KEY')
        
        # create s3 bucket to put results
        bucket = s3.Bucket(
            self, 'results-bucket',
            versioned=False,
            removal_policy=core.RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                ignore_public_acls=False,
                block_public_policy=True,
                restrict_public_buckets=True
            )
        )

        # create lambda to gather domains
        lambda_scrapers = lambda_.Function(
            self, "scrapers",
            code=lambda_.Code.from_asset('lambda-releases/scrapers.zip'),
            handler="get_events.main",
            timeout=core.Duration.seconds(900),
            runtime=lambda_.Runtime.PYTHON_3_7,
            memory_size=1000
        )
        
        # set env vars
        lambda_scrapers.add_environment('NPS_KEY', NPS_KEY)
        lambda_scrapers.add_environment('EVENTBRITE_TOKEN', EVENTBRITE_TOKEN)
        lambda_scrapers.add_environment('BUCKET_NAME', bucket.bucket_name)
        
        # create rule to run the lambda every Friday at 18:00 UTC (1pm EST)
        rule = events.Rule(
            self, "Rule",
            schedule=events.Schedule.cron(
                minute='0',
                hour='18',
                month='*',
                week_day='FRI',
                year='*'),
        )
        rule.add_target(targets.LambdaFunction(lambda_scrapers))

        # grant permissions to lambda to use bucket
        bucket.grant_read_write(lambda_scrapers)
        

app = core.App()
CapitalNatureStack(app, "CapitalNatureStack")
app.synth()