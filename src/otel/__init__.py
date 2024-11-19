import logging

from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPOTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter as HTTPOTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter as HTTPOTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCOTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter as GRPCOTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GRPCOTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import (
    Counter,
    Histogram,
    MeterProvider,
    ObservableCounter,
    ObservableGauge,
    ObservableUpDownCounter,
    UpDownCounter,
)
from opentelemetry.sdk.metrics.export import (
    AggregationTemporality,
    PeriodicExportingMetricReader,
)


deltaTemporality = {
    Counter: AggregationTemporality.DELTA,
    UpDownCounter: AggregationTemporality.CUMULATIVE,
    Histogram: AggregationTemporality.DELTA,
    ObservableCounter: AggregationTemporality.DELTA,
    ObservableUpDownCounter: AggregationTemporality.CUMULATIVE,
    ObservableGauge: AggregationTemporality.CUMULATIVE,
}


def getLogExporter(endpoint, headers, protocol):
     match protocol:
        case "HTTP":
             return HTTPOTLPLogExporter(endpoint=endpoint, headers=headers)
        case "GRPC":
             return GRPCOTLPLogExporter(endpoint=endpoint, headers=headers)
        case _:
             return HTTPOTLPLogExporter(endpoint=endpoint, headers=headers)

def getSpanExporter(endpoint, headers, protocol):
     match protocol:
        case "HTTP":
             return HTTPOTLPSpanExporter(endpoint=endpoint, headers=headers)
        case "GRPC":
             return GRPCOTLPSpanExporter(endpoint=endpoint, headers=headers)
        case _:
             return HTTPOTLPSpanExporter(endpoint=endpoint, headers=headers)

def getMetricExporter(endpoint, headers, protocol):
     match protocol:
        case "HTTP":
             return HTTPOTLPMetricExporter(endpoint=endpoint, headers=headers, preferred_temporality=deltaTemporality)
        case "GRPC":
             return GRPCOTLPMetricExporter(endpoint=endpoint, headers=headers, preferred_temporality=deltaTemporality)
        case _:
             return HTTPOTLPMetricExporter(endpoint=endpoint, headers=headers, preferred_temporality=deltaTemporality)

def create_otel_attributes(atts, GITHUB_SERVICE_NAME):
    attributes={SERVICE_NAME: GITHUB_SERVICE_NAME}
    for att in atts:
            attributes[att]=atts[att]
    return attributes

def otel_logger(endpoint, headers, resource, name, export_protocol):
    exporter = getLogExporter(endpoint=f"{endpoint}v1/logs",headers=headers, protocol=export_protocol )
    logger = logging.getLogger(str(name))
    logger.handlers.clear()
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logger.addHandler(handler)
    return logger


def otel_tracer(endpoint, headers, resource, tracer, export_protocol):
    processor = BatchSpanProcessor(getSpanExporter(endpoint=f"{endpoint}v1/traces",headers=headers, protocol=export_protocol ))
    tracer = TracerProvider(resource=resource)
    tracer.add_span_processor(processor)
    tracer = trace.get_tracer(__name__, tracer_provider=tracer)

    return tracer

def otel_meter(endpoint, headers, resource, meter, export_protocol):
    reader = PeriodicExportingMetricReader(getMetricExporter(endpoint=f"{endpoint}v1/metrics",headers=headers, protocol=export_protocol ))
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    meter = metrics.get_meter(__name__,meter_provider=provider)
    return meter