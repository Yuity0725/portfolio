###############################################################################
# 自動返却パイプライン用 Step Functions モジュール骨子（技術デモ用の匿名サンプル）
#
# 技術デモ用に書き起こした匿名サンプルであり、実運用コードではない
# (illustrative demo authored for this portfolio; not production source).
#
# 実在するアカウントID・ARN・関数名は含めず、すべて変数/プレースホルダ。
# state machine 定義は共通ファイルとし、環境依存値(Lambda名など)だけを
# templatefile で注入して dev/stg/prod を同一構成で再現する。
###############################################################################

variable "env" {
  type        = string
  description = "デプロイ環境 (dev / stg / prod)"
}

variable "name" {
  type        = string
  description = "state machine の論理名"
  default     = "auto-return"
}

variable "definition_path" {
  type        = string
  description = "state machine 定義(JSON)テンプレートのパス"
}

# 環境ごとに差し込む Lambda 関数名。定義本体は共通、可変部だけを注入する。
variable "lambda_function_names" {
  type = object({
    parse_triggers        = string
    run_search_jobs       = string
    get_search_job_status = string
    run_return_jobs       = string
    get_return_job_status = string
    handle_errors         = string
    finalize_state        = string
  })
  description = "state machine から invoke する各 Lambda の関数名"
}

variable "lambda_function_arns" {
  type        = list(string)
  description = "state machine の実行ロールに invoke を許可する Lambda ARN 群"
}

variable "schedule_expression" {
  type        = string
  description = "EventBridge Scheduler の起動スケジュール(cron/rate)"
  default     = "cron(0 18 * * ? *)"
}

locals {
  common_tags = {
    Project = "lime-platform"
    Service = var.name
    Env     = var.env
    Managed = "terraform"
  }
}

# --- 実行ロール(最小権限) ----------------------------------------------------
resource "aws_iam_role" "sfn_exec" {
  name = "${var.name}-sfn-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "sfn_invoke_lambda" {
  name = "${var.name}-invoke-lambda-${var.env}"
  role = aws_iam_role.sfn_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["lambda:InvokeFunction"]
      Resource = var.lambda_function_arns
    }]
  })
}

# --- state machine 本体 ------------------------------------------------------
resource "aws_sfn_state_machine" "auto_return" {
  name     = "${var.name}_${var.env}"
  role_arn = aws_iam_role.sfn_exec.arn

  # 定義は共通テンプレート。関数名は環境ごとに templatefile で注入する。
  definition = templatefile(var.definition_path, {
    auto_return_sf_parse_triggers_func_name        = var.lambda_function_names.parse_triggers
    auto_return_sf_run_search_jobs_func_name       = var.lambda_function_names.run_search_jobs
    auto_return_sf_get_search_job_status_func_name = var.lambda_function_names.get_search_job_status
    auto_return_sf_run_return_jobs_func_name       = var.lambda_function_names.run_return_jobs
    auto_return_sf_get_return_job_status_func_name = var.lambda_function_names.get_return_job_status
    auto_return_sf_handle_errors_func_name         = var.lambda_function_names.handle_errors
    auto_return_sf_finalize_state_func_name        = var.lambda_function_names.finalize_state
  })

  tags = local.common_tags
}

# --- 定期起動(EventBridge Scheduler) ----------------------------------------
resource "aws_scheduler_schedule" "trigger" {
  name = "${var.name}-schedule-${var.env}"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = var.schedule_expression
  schedule_expression_timezone = "Asia/Tokyo"

  target {
    arn      = aws_sfn_state_machine.auto_return.arn
    role_arn = aws_iam_role.scheduler_exec.arn
  }
}

resource "aws_iam_role" "scheduler_exec" {
  name = "${var.name}-scheduler-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "scheduler_start_execution" {
  name = "${var.name}-start-execution-${var.env}"
  role = aws_iam_role.scheduler_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["states:StartExecution"]
      Resource = [aws_sfn_state_machine.auto_return.arn]
    }]
  })
}

output "state_machine_arn" {
  description = "作成された state machine の ARN"
  value       = aws_sfn_state_machine.auto_return.arn
}
