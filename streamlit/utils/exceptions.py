"""
Custom exceptions for the SicherGleis Railway Dashboard application.
"""
class DataLoadError(Exception):
    """Raised when data loading fails."""
    pass


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


class SimulationError(Exception):
    """Raised when SaaS simulation encounters an error."""
    pass


class ReportGenerationError(Exception):
    """Raised when PDF report generation fails."""
    pass


class InvalidInputError(Exception):
    """Raised when user input is invalid."""
    pass
