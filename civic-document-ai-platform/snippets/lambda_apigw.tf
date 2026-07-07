###############################################################################
# Lambda + API Gateway モジュール骨子（技術デモ用の匿名サンプル）
#
# このファイルはポートフォリオ用に書き起こした簡略版であり、実運用コードではない。
# 実在するアカウントID・エンドポイント・ARN等は含めず、すべて変数/プレースホルダ。
# FastAPI を arm64 Lambda で実行し、API Gateway(HTTP API) から公開する構成を示す。
###############################################################################

variable "aws_region" {
  type        = string
  description = "デプロイ先リージョン"
  default     = "ap-northeast-1"
}

variable "function_name" {
  type        = string
  description = "Lambda関数名"
  default     = "rag-chat-api"
}

variable "image_uri" {
  type        = string
  description = "ECRのコンテナイメージURI（例: <account-id>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag>）"
}

variable "environment" {
  type        = map(string)
  description = "Lambdaへ注入する環境変数（機密値はSSM/Secretsから解決し、ここには生値を置かない）"
  default     = {}
}

locals {
  # DRY化のための共通タグ
  common_tags = {
    Project = "civic-document-ai-platform"
    Managed = "terraform"
  }
}

# --- 実行ロール（最小権限） -------------------------------------------------
resource "aws_iam_role" "lambda_exec" {
  name = "${var.function_name}-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Lambda 関数（コンテナ / arm64） ----------------------------------------
resource "aws_lambda_function" "api" {
  function_name = var.function_name
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = var.image_uri
  architectures = ["arm64"] # Gravitonでコスト最適化
  timeout       = 30
  memory_size   = 1024

  environment {
    variables = var.environment
  }

  tracing_config {
    mode = "Active" # X-Rayで分散トレース
  }

  tags = local.common_tags
}

# --- API Gateway (HTTP API) -------------------------------------------------
resource "aws_apigatewayv2_api" "http" {
  name          = "${var.function_name}-http"
  protocol_type = "HTTP"
  tags          = local.common_tags
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "generate" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "POST /generate"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

output "api_endpoint" {
  description = "公開されるAPIエンドポイント"
  value       = aws_apigatewayv2_stage.default.invoke_url
}
