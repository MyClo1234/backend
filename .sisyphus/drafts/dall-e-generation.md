# Draft: DALL-E 3 Coordi Image Generation

## Requirements (Confirmed)
- **Goal**: Implement "Coordi Image" generation using DALL-E 3 on Azure.
- **Infrastructure**: Azure Functions (Python), Azure Blob Storage, PostgreSQL.
- **Existing Codebase**:
  - DDD structure (`app/domains/`).
  - `AzureOpenAIClient` exists but supports only Chat Completions (`gpt-4o-mini`).
  - `BlobStorageService` exists for saving images.

## Technical Decisions
- **Client Extension**: Need to extend `AzureOpenAIClient` (or create `AzureDalleClient`) to support `images.generate`.
- **Storage**: Use `BlobStorageService` to save generated images.
- **Endpoint**: Verify if DALL-E 3 uses `AZURE_OPENAI_ENDPOINT` or `AZURE_EXISTING_AIPROJECT_ENDPOINT`.

## Open Questions
1.  **Deployment Name**: What is the Azure OpenAI Deployment Name for DALL-E 3? (Env var `AZURE_OPENAI_DEPLOYMENT_NAME` is `gpt-4o-mini`).
2.  **Input Data**: What input triggers the generation?
    - A text prompt?
    - A selected combination of clothes (Item IDs)?
    - A user profile + weather?
3.  **Location**: Should this feature go into:
    - `app/domains/recommendation` (as part of outfit recommendation)?
    - `app/domains/wardrobe`?
    - A new domain `app/domains/generation`?
4.  **Endpoint Config**: The env vars show `AZURE_EXISTING_AIPROJECT_ENDPOINT`. Is this the DALL-E endpoint?

## Scope Boundaries
- **IN**: DALL-E 3 integration, Image Storage, API Endpoint.
- **OUT**: Frontend implementation (API only).
