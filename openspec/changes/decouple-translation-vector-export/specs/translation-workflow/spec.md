## MODIFIED Requirements

### Requirement: Translation Task Completion
The system SHALL complete video translation and save output files locally, and MAY optionally export to vector database based on user preference.

#### Scenario: Translation completes with auto-export disabled
- **WHEN** translation task completes successfully
- **AND** user has not enabled "Auto-export to vector database"
- **THEN** save translated video and SRT locally
- **AND** show notification: "Translation complete. Upload to vector database anytime via Summary Library → Vector Export Manager."
- **AND** do NOT automatically export to vector database

#### Scenario: Translation completes with auto-export enabled
- **WHEN** translation task completes successfully
- **AND** user has enabled "Auto-export to vector database" checkbox
- **THEN** save translated video and SRT locally
- **AND** automatically trigger vector database export in background
- **AND** show notification: "Translation complete. Exporting to vector database..."

#### Scenario: Auto-export fails (non-fatal)
- **WHEN** translation completes and auto-export is enabled
- **AND** vector database export fails (network error, config error, etc.)
- **THEN** translation is still marked as successful
- **AND** show error notification: "Translation succeeded, but vector export failed: [error]. Upload manually via Vector Export Manager."
- **AND** do NOT fail the entire translation task

## ADDED Requirements

### Requirement: Auto-Export Configuration
The system SHALL provide a user preference to enable/disable automatic vector database export after translation.

#### Scenario: User enables auto-export
- **WHEN** user checks "Auto-export to vector database after translation" checkbox in translation UI
- **THEN** store preference in `config.params['qdrant_auto_export'] = True`
- **AND** future translations will automatically export to vector database

#### Scenario: User disables auto-export (default)
- **WHEN** user unchecks "Auto-export to vector database after translation" checkbox
- **OR** user has not configured the setting (new install)
- **THEN** store preference in `config.params['qdrant_auto_export'] = False`
- **AND** future translations will NOT automatically export to vector database

### Requirement: Config Migration from Legacy Setting
The system SHALL migrate legacy `qdrant_enabled` config to new `qdrant_auto_export` config on first load.

#### Scenario: Migrate legacy config
- **WHEN** config is loaded
- **AND** `qdrant_enabled` exists in config
- **AND** `qdrant_auto_export` does NOT exist in config
- **THEN** set `qdrant_auto_export = qdrant_enabled`
- **AND** log migration: "Migrated qdrant_enabled to qdrant_auto_export"
- **AND** keep `qdrant_enabled` for backward compatibility (read-only)
