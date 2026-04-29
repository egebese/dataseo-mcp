"""Domain-specific exceptions for DataSEO MCP."""


class DataSEOError(Exception):
    """Base exception for expected DataSEO MCP failures."""


class ConfigurationError(DataSEOError):
    """Raised when required runtime configuration is missing."""


class ValidationError(DataSEOError):
    """Raised when a tool receives invalid input."""


class CaptchaError(DataSEOError):
    """Base exception for CAPTCHA provider failures."""


class CaptchaConfigurationError(CaptchaError):
    """Raised when no CAPTCHA provider is configured."""


class CaptchaSolvingError(CaptchaError):
    """Raised when configured providers cannot solve a CAPTCHA."""


class UpstreamError(DataSEOError):
    """Raised when an upstream SEO or AI provider cannot return usable data."""
