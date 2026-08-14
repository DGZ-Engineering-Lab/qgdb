# Changelog for plugin/browser_provider.py

## 2026-08-13
- Make `capabilities()` resilient to different PyQGIS enum/flag representations.
- Normalize legacy `dataCapabilities()` return values and construct the exact
  `DataItemProviderCapabilities` type when available to prevent TypeError on
  QGIS 3.44.5 (Python 3.12).
