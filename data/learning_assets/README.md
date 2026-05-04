# Learning Assets (Local Test Storage)

This folder is for local testing of Learn Hub media before moving to cloud storage.

## Structure

- `videos/`: video lessons (`mp4`, `webm`, `mov`, `m4v`, `avi`, `mkv`, ...)
- `audios/`: audio lessons/podcasts (`mp3`, `wav`, `m4a`, `aac`, `ogg`, `flac`, ...)
- `books/`: reading assets (`pdf`, `epub`, `mobi`, `txt`, `docx`)
- `images/`: thumbnails/covers (optional)

## Public URL mapping

Files here are served by backend at:

- `/learning-assets/videos/<filename>`
- `/learning-assets/audios/<filename>`
- `/learning-assets/books/<filename>`
- `/learning-assets/images/<filename>`

Example:

- local file: `data/learning_assets/videos/cashflow-101.mp4`
- URL in app: `/learning-assets/videos/cashflow-101.mp4`

## Migration note (later)

When moving to cloud storage (S3/R2/GCS), keep the same resource schema in lesson payload and switch URL base from local `/learning-assets/...` to cloud CDN URL.
