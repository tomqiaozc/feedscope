import logging
import os

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_telemetry(app: FastAPI) -> None:
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.trace import TracerProvider
    except ImportError:
        logger.warning("OpenTelemetry packages not installed — skipping telemetry setup")
        return

    provider = TracerProvider()

    if connection_string:
        try:
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            exporter = AzureMonitorTraceExporter(connection_string=connection_string)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("Azure Monitor exporter configured")
        except ImportError:
            logger.warning(
                "azure-monitor-opentelemetry-exporter not installed — skipping Azure export"
            )
    else:
        logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not set — telemetry export disabled")

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)

    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        from app.db.engine import engine

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    except ImportError:
        logger.warning("opentelemetry-instrumentation-sqlalchemy not installed — skipping")

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except ImportError:
        logger.warning("opentelemetry-instrumentation-httpx not installed — skipping")
