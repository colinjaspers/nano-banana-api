# Argolink image mapping

The repository's image examples map directly to `/v1/images/generations` and `/v1/images/edits`. Keep the model ID in configuration so a model page change does not require editing every example.

## Review checklist

- [ ] API key is read from `ARGOLINK_API_KEY`.
- [ ] Input images are validated before upload.
- [ ] Ratio and resolution are checked against the selected model.
- [ ] Base64 output is decoded only to a controlled file.
