# ADR-020: S3 for File Storage with Presigned URLs

- Status: Accepted
- Date: 05-18-2026
- Tags: storage, aws, security

## Context

The platform needs to store uploaded files (course materials, images, generated certificates as PDFs) securely and serve them to authorized users. Files must not be publicly accessible by default; access must be tied to enrollment status and role permissions.

## Decision

AWS S3 will be used for all file storage. Files are never uploaded through the API server directly; clients upload to S3 using presigned URLs.

Access pattern:
1. Client requests an upload URL from the API (`POST /upload-url`).
2. API validates authorization (enrollment check for materials, role check for admin uploads), generates a presigned PUT URL (short TTL, e.g., 5 minutes), and returns it.
3. Client uploads the file directly to S3 using the presigned URL.
4. API receives a confirmation from the client (or via S3 event notification) and records the file metadata in PostgreSQL.
5. To access a file, the API generates a presigned GET URL (e.g., 1-hour TTL) after verifying authorization. The file URL is never stored permanently in the database; the S3 key is stored and a presigned URL is generated on each access.

Bucket configuration:
- All buckets are private (no public ACLs).
- Server-side encryption enabled (SSE-S3 or SSE-KMS).
- Versioning enabled for the materials bucket.
- Lifecycle policies to transition old/unused files to cheaper storage tiers.

## Consequences

**Positive:**
- Presigned URLs offload file transfer bandwidth and latency from the API server; large files do not pass through the application.
- S3's durability (99.999999999%) and availability are significantly higher than self-hosted storage.
- Access control is enforced at the API layer (authorization check before generating the presigned URL), not at the S3 level, keeping IAM policies simple.
- `boto3` provides a mature, well-tested S3 client.

**Negative:**
- Presigned URLs have a TTL; if a user shares a URL, it will expire. This is intentional behavior for access control but may confuse users.
- Direct S3 uploads bypass the API, meaning server-side virus scanning or content validation must happen post-upload (via S3 event + Lambda or a Celery task).

**Neutral:**
- In local development, MinIO (S3-compatible) runs in Docker Compose as an S3 replacement, allowing local testing without AWS credentials.

## Alternatives Considered

**Storing files on the API server's filesystem:** No scalability, no redundancy, breaks in a multi-pod deployment. Rejected.

**CloudFront + S3:** CloudFront adds a CDN layer and signed cookie-based access control. A valid future enhancement for public assets (course thumbnails) but over-engineered for the initial private materials use case.

## Links

- Related: ADR-018 (SES/AWS ecosystem), ADR-022 (observability)