

resource "aws_iam_role" "iam_for_lambda" {
  name = "iam_for_lambda"

  assume_role_policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
      }   
    ]
  }
  EOF
}

resource "aws_iam_policy" "lambda_s3" {
  name = "lambda_s3"
  path = "/"
  description = "IAM policy for lambda S3 access"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:*"
      ],
      "Resource": "*",
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role = "${aws_iam_role.iam_for_lambda.name}"
  policy_arn = "${aws_iam_policy.lambda_s3.arn}"
}

module "ans_lambda" {
  source = "modules/lambda"
  lambda_name = "ans"
  role_arn = "${aws_iam_role.iam_for_lambda.arn}"
}

resource "aws_cloudwatch_event_rule" "ans_scraper-trigger" {
  name        = "ans_scraper-trigger"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "ans_lambda-target" {
  arn = "${module.ans_lambda.arn}"
  rule = "${aws_cloudwatch_event_rule.ans_scraper-trigger.name}"
  input = "{\"url\": \"https://anshome.org/events-calendar/\",\"source_name\": \"ans\"}"
}
