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
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

def getLogExporter(otlp_endpoint, headers, protocol):
     print(f"Using: {otlp_endpoint}v1/logs")
     if protocol == 'HTTP':
        return HTTPOTLPLogExporter(endpoint=f"{otlp_endpoint}v1/logs",headers=headers)
     elif protocol == 'GRPC':
             return GRPCOTLPLogExporter(endpoint=f"{otlp_endpoint}v1/logs",headers=headers)
     else:
        return HTTPOTLPLogExporter(endpoint=f"{otlp_endpoint}v1/logs",headers=headers)

def getSpanExporter(otlp_endpoint, headers, protocol):
     print(f"Using: {otlp_endpoint}v1/traces")
     if protocol == 'HTTP':
        return HTTPOTLPSpanExporter(endpoint=f"{otlp_endpoint}v1/traces",headers=headers)
     elif protocol == 'GRPC':
        return GRPCOTLPSpanExporter(endpoint=f"{otlp_endpoint}v1/traces",headers=headers)
     else:
        return HTTPOTLPSpanExporter(endpoint=f"{otlp_endpoint}v1/traces",headers=headers)

def getMetricExporter(otlp_endpoint, headers, protocol):
     print(f"Using: {otlp_endpoint}v1/metrics")
     if protocol == 'HTTP':
        return HTTPOTLPMetricExporter(endpoint=f"{otlp_endpoint}v1/metrics",headers=headers)
     elif protocol == 'GRPC':
        return GRPCOTLPMetricExporter(endpoint=f"{otlp_endpoint}v1/metrics",headers=headers)
     else:
        return HTTPOTLPMetricExporter(endpoint=f"{otlp_endpoint}v1/metrics",headers=headers)

def create_otel_attributes(atts, GITHUB_SERVICE_NAME):
    attributes={SERVICE_NAME: GITHUB_SERVICE_NAME}
    for att in atts:
            attributes[att]=atts[att]
    return attributes

def otel_logger(otlp_endpoint, headers, resource, name, export_protocol):
    exporter = getLogExporter(endpoint=f"{otlp_endpoint}v1/logs",headers=headers, protocol=export_protocol )
    logger = logging.getLogger(str(name))
    logger.handlers.clear()
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logger.addHandler(handler)
    return logger


def otel_tracer(otlp_endpoint, headers, resource, tracer, export_protocol):
    processor = BatchSpanProcessor(getSpanExporter(endpoint=f"{otlp_endpoint}v1/traces",headers=headers, protocol=export_protocol ))
    tracer = TracerProvider(resource=resource)
    tracer.add_span_processor(processor)
    tracer = trace.get_tracer(__name__, tracer_provider=tracer)

    return tracer

def otel_meter(otlp_endpoint, headers, resource, meter, export_protocol):
    reader = PeriodicExportingMetricReader(getMetricExporter(endpoint=f"{otlp_endpoint}v1/metrics",headers=headers, protocol=export_protocol ))
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    meter = metrics.get_meter(__name__,meter_provider=provider)
    return meter