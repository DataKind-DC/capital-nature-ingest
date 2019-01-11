variable "lambda_name" {
  type = "string"
}

variable "role_arn" {
  type = "string"
}

resource "aws_lambda_function" "lambda" {
  filename         = "../${var.lambda_name}/lambda.zip"
  function_name    = "capital-nature_${var.lambda_name}-scraper"
  role             = "${var.role_arn}"
  handler          = "lambda_function.handler"
  source_code_hash = "${base64sha256(file("../${var.lambda_name}/lambda.zip"))}"
  runtime          = "python2.7"
  timeout          = 300

  environment {
    variables = {
      foo = "bar"
    }
  }
}

output "arn" {
  value = "${aws_lambda_function.lambda.arn}"
}