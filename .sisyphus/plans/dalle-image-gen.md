# Azure DALL-E 3 Image Generation Plan

## Context

### Original Request
Implement outfit ("Codify") image generation using Azure DALL-E 3 model.

### Interview Summary
**Key Discussions**:
- **Input**: Structured outfit data (Top/Bottom items + Style) based on recommendations.
- **Output**: Generated image saved to Azure Blob Storage, returning the URL.
- **Environment**: Specific Azure endpoints and keys provided.
- **Infrastructure**: Existing FastAPI application with DDD structure.

**Research Findings**:
- **Endpoints**: Azure DALL-E 3 uses `images.generate` endpoint, which differs from the Chat Completion endpoint used by existing `AzureOpenAIClient`. A new client is needed.
- **Schema**: `WardrobeItemSchema` contains rich attributes (color, pattern, material) suitable for prompt engineering.
- **Storage**: `AZURE_STORAGE_CONTAINER_NAME` ("images") is already configured in `Config`.

---

## Work Objectives

### Core Objective
Enable the system to generate realistic outfit images from structured recommendation data using Azure DALL-E 3.

### Concrete Deliverables
- `app/ai/clients/azure_dalle_client.py`: Client for Azure DALL-E 3.
- `app/domains/generation/`: New domain for generation logic.
- `POST /api/generation/outfit`: Endpoint to trigger generation.
- `scripts/test_generation_manual.py`: Script for verification.

### Definition of Done
- [ ] Endpoint accepts outfit data and returns a valid Blob Storage URL.
- [ ] Image reflects the described items (color, category).
- [ ] All environment variables are correctly mapped.

### Must Have
- Use the specific `AZURE_DALLE_ENDPOINT` and `AZURE_DALLE_API_KEY`.
- Save images to Azure Blob Storage (do not return raw DALL-E URLs).
- Construct prompts dynamically from item attributes.

### Must NOT Have (Guardrails)
- Do not modify existing `recommendation` or `wardrobe` domains significantly (keep logic isolated).
- Do not expose raw DALL-E keys or endpoints to the client.

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest)
- **User wants tests**: Manual verification preferred for this feature (due to AI cost).
- **Strategy**: 
    1.  **Unit Tests**: Mock DALL-E client to test prompt construction and flow logic.
    2.  **Manual Verification**: Use a script to call the actual API once to verify integration.

---

## Task Flow

```
Config Update → Dalle Client → Generation Service → Generation Router → Main Integration
```

---

## TODOs

- [ ] 1. Update Config with DALL-E Variables
    **What to do**:
    - Add `AZURE_DALLE_API_KEY`, `AZURE_DALLE_ENDPOINT`, `AZURE_DALLE_DEPLOYMENT_NAME` to `app/core/config.py`.
    - Ensure validation in `check_api_key`.
    
    **References**:
    - `app/core/config.py`: Add new fields here.

    **Acceptance Criteria**:
    - [ ] `Config.AZURE_DALLE_API_KEY` is accessible.
    - [ ] `Config.check_api_key()` warns if missing.

- [ ] 2. Create Azure DALL-E Client
    **What to do**:
    - Create `app/ai/clients/azure_dalle_client.py`.
    - Implement `AzureDalleClient` class using `openai.AzureOpenAI`.
    - Note: Use `api_version="2024-02-01"` as per example.
    - Implement `generate_image(prompt, size="1024x1024", style="vivid") -> str (url)`.
    
    **References**:
    - `app/ai/clients/azure_openai_client.py`: Reference pattern for singleton and logging.
    - Official Azure OpenAI Python SDK docs for `client.images.generate`.

    **Acceptance Criteria**:
    - [ ] Client initializes with correct env vars.
    - [ ] `generate_image` method exists and handles exceptions.

- [ ] 3. Create Generation Domain Schema
    **What to do**:
    - Create `app/domains/generation/schema.py`.
    - Define `OutfitGenerationRequest` (accepts `top`, `bottom`, `style_description`).
    - Define `OutfitGenerationResponse` (returns `image_url`).
    
    **References**:
    - `app/domains/recommendation/schema.py`: Reuse `OutfitRecommendationSchema` structure if possible, or define similar inputs.

    **Acceptance Criteria**:
    - [ ] Pydantic models defined.

- [ ] 4. Create Generation Service
    **What to do**:
    - Create `app/domains/generation/service.py`.
    - Implement `GenerationService` class.
    - Method: `create_outfit_image(request: OutfitGenerationRequest) -> str`.
    - Logic:
        1. Construct prompt from `request.top` and `request.bottom` attributes (Color, Pattern, Category).
        2. Call `AzureDalleClient.generate_image`.
        3. Download image content (using `httpx` or `requests`).
        4. Upload to Blob Storage using `app.services.blob_storage.upload_bytes` (or similar).
        5. Return Blob URL.
    
    **References**:
    - `app/schemas/common.py`: For accessing `AttributesSchema` fields.
    - `app/services/blob_storage.py`: For upload logic.

    **Acceptance Criteria**:
    - [ ] Prompt includes key attributes (Color, Category).
    - [ ] Image is uploaded to blob storage.

- [ ] 5. Create Generation Router
    **What to do**:
    - Create `app/domains/generation/router.py`.
    - Define `POST /api/generation/outfit`.
    - Inject `GenerationService`.
    
    **References**:
    - `app/domains/recommendation/router.py`: Reference for router structure.

    **Acceptance Criteria**:
    - [ ] Endpoint is defined with correct response model.

- [ ] 6. Register Router in Main
    **What to do**:
    - Edit `app/main.py`.
    - Include `generation_router`.
    
    **References**:
    - `app/main.py`: Add `app.include_router(...)`.

    **Acceptance Criteria**:
    - [ ] Server starts without errors.
    - [ ] `/api/generation/outfit` is listed in Swagger UI.

- [ ] 7. Create Verification Script
    **What to do**:
    - Create `scripts/test_generation_manual.py`.
    - Hardcode a sample outfit request.
    - Send request to `http://localhost:8000/api/generation/outfit`.
    - Print the result URL.
    
    **References**:
    - `scripts/seed_regions.py`: Reference for script setup.

    **Acceptance Criteria**:
    - [ ] Script runs and outputs a URL.

---

## Success Criteria

### Verification Commands
```bash
# Start server
python -m app.main

# Run verification script (in another terminal)
python scripts/test_generation_manual.py
```

### Final Checklist
- [ ] DALL-E 3 API is called correctly.
- [ ] Image is saved to "images" container in Blob Storage.
- [ ] URL is returned to client.
