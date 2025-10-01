from logging import INFO, Filter
from loguru import logger
from fastapi import FastAPI, Query
import time

from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_tracer

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware


# ---- Configuração OpenTelemetry ----
resource = Resource(attributes={SERVICE_NAME: 'ops-application'})

# Logs
provider = LoggerProvider(resource=resource)
processor = BatchLogRecordProcessor(OTLPLogExporter(endpoint='localhost:4317', insecure=True))
provider.add_log_record_processor(processor)
set_logger_provider(provider)

# Traces
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)
span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint='localhost:4317', insecure=True))
trace_provider.add_span_processor(span_processor)

metric_exporter = OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True)
reader = PeriodicExportingMetricReader(metric_exporter)
metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
meter = metrics.get_meter("ops-meter")

class RemoveExtra(Filter):
    def filter(self, record):
        if 'extra' in record.__dict__:
            del record.__dict__['extra']
        return True

handler = LoggingHandler(level=INFO, logger_provider=provider)
handler.addFilter(RemoveExtra())
logger.add(handler, level='DEBUG', serialize=True)

# Tracer
tracer = get_tracer(__name__)

# Criando um contador de requisições por endpoint
request_counter = meter.create_counter(
    name="http_requests_total",
    description="Número total de requisições por endpoint",
    unit="1",
)

# ---- Aplicação FastAPI ----
app = FastAPI(title="Ops Application")
app.add_middleware(OpenTelemetryMiddleware)
FastAPIInstrumentor.instrument_app(app)

@app.get("/sum")
def sum_op():
    request_counter.add(1, {"endpoint": "/sum"})
    with tracer.start_as_current_span("sum-operation"):
        logger.info("Starting the sum operation")
        time.sleep(1)
        result = 1 + 1
        logger.info(f"Sum ok with result = {result}")
        return {"operation": "sum", "result": result}


@app.get("/multiply")
def multiply_op():
    request_counter.add(1, {"endpoint": "/multiply"})
    with tracer.start_as_current_span("multiply-operation"):
        logger.info("Starting the multiply operation")
        time.sleep(2)
        result = 2 * 2
        logger.info(f"Multiply ok with result = {result}")
        return {"operation": "multiply", "result": result}


@app.get("/substract")
def substract_op():
    request_counter.add(1, {"endpoint": "/substract"})
    with tracer.start_as_current_span("substract-operation"):
        logger.info("Starting the substract operation")
        time.sleep(3)
        result = 10 - 5
        logger.info(f"Substract ok with result = {result}")
        return {"operation": "substract", "result": result}


@app.get("/divide")
def divide_op():
    request_counter.add(1, {"endpoint": "/divide"})
    with tracer.start_as_current_span("divide-operation"):
        logger.info("Starting the divide operation")
        try:
            time.sleep(4)
            result = 1 / 0  # Simulando erro
            return {"operation": "divide", "result": result}
        except Exception as e:
            logger.error(f"Error in divide operation: {e}")
            return {"operation": "divide", "error": str(e)}
        
@app.get("/greet")
def greet_endpoint(name: str = Query(..., description="Nome da pessoa")):
    request_counter.add(1, {"endpoint": "/greet"})
    with tracer.start_as_current_span("greet-operation"):
        with tracer.start_as_current_span("greet"):
            greeting = f"Hello, {name}!"
            logger.info(f"Greeting generated for person: {name}")

        with tracer.start_as_current_span("sum-operation"):
            logger.info("Starting the sum operation")
            time.sleep(1)
            sumResult = 1 + 1
            logger.info(f"Sum ok with result = {sumResult}")

        with tracer.start_as_current_span("substract-operation"):
            logger.info("Starting the substract operation")
            time.sleep(3)
            subResult = 10 - 5
            logger.info(f"Substract ok with result = {subResult}")
        
        return {"greeting": greeting ,
                'sum result': sumResult,
                "sub result": subResult
                }
