# Kashoo Connector — Ideal Onboarding Flow

1. User opens Kashoo sidebar in Imperal OS.
2. Form prompts for Auth Token and Business ID.
3. Clicking "How do I connect Kashoo?" opens a modal with instructions to locate credentials in Kashoo.
4. Submission executes `connect_kashoo`, verifying access via `GET /api/v1/businesses/{businessId}`.
5. Connection is saved and activated.
