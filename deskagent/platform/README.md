# Platform services

`base/` defines the interfaces consumed by actions. `macos/` owns native
processes, AppleScript, Accessibility (AX), screen capture, OCR and image tools.
`common/` implements operations that do not require a particular OS:

- Browser models, URL/path security policy and the CDP transport.
- Accessibility models, semantic tree queries, locators and observation.
- Guarded project/source access, Git commands and private pytest reports.
- Text/PDF document access and bounded output writes.
- Persisted session/workflow queries and plan helpers.
- Bounded PCM WAV decoding and output writes.

`ServicesFactory` wires the native adapters and portable services into
`context.services`. Actions retain schemas, risk/confirmation metadata, input
validation, result formatting and domain transformations. Their shared IO
helpers delegate to the configured services. Contexts without these new fields
retain the portable default implementations for compatibility.

Extended OCR actions use the configured vision service for both capture and
recognition, and delete temporary captures even if recognition fails. The
native fallback remains available for older contexts without a vision service.

The old browser backend and `perception/accessibility` module paths are
compatibility aliases, so existing imports and patches resolve to the same
implementation objects. New adapters should import contracts/models from
`platform`, without depending on the action or perception packages.

This separation does not add Windows/Linux native adapters. Portable services
can be used on either OS, while the application service factory still supports
macOS only.
