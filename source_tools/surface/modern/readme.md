# Optional modern native extraction

`run_modern_surface.py` preserves the strict DQF-0 pilot; `run_modern_recommended.py` runs the separately specified DQF0–1 tier. Both retain the complete selected sample and original ground rules. Set `LST_MODERN_SURFACE_WORKSPACE` to a writable empty/cache workspace and optionally `LST_PROVIDER_CACHE` to existing provider bytes. Package-local chronology and corrected extraction manifests supply the study design/key inventory.

These native drivers require the raw-format dependencies documented in `source_tools/readme.md`, plus h5netcdf and zoneinfo support. They access NOAA providers. Their portable path configuration was syntax checked; a new native download run in the clean release environment is not claimed. The actual native/radiometry audit already executed before packaging is in `evidence/surface/modern/modern_verification_summary.json`. For a tested offline reconstruction use `scripts/reproduce_modern_surface.py` with packaged paired data.
