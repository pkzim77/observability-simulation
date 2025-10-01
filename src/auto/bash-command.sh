# Script para configurar variáveis de ambiente do OpenTelemetry e executar a aplicação Python

$env:OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true"
$env:OTEL_EXPORTER_OTLP_ENDPOINT="0.0.0.0:4317"
$env:OTEL_EXPORTER_OTLP_INSECURE="true"
$env:OTEL_LOGS_EXPORTER="otlp"
$env:OTEL_SERVICE_NAME="instru-log"

opentelemetry-instrument python auto-log.py


