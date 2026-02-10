# Stage 6 — Profile screen (MVP fields)

## Scope
Implement MVP Profile UI fields required to start recommendation flow with a minimally usable profile.

## Implemented fields
- Country (MVP fixed option: `DE`)
- Time available per week
- Capital available (EUR)
- Language level
- Assets (comma-separated tags)
- Skills (comma-separated tags)
- Constraints (comma-separated text/tags)
- Objective preset (`fastest_money` / `max_net`)

## Behavior
- Profile page now initializes and persists all listed fields in `st.session_state["profile"]`.
- Loaded demo profile data is backfilled with safe defaults for missing fields.
- Assets/skills/constraints are parsed into normalized string lists and saved in profile payload.
- UI shows `Profile ready` when minimum required profile inputs are present, otherwise `Profile draft`.

## Notes
- Country remains DE-only for MVP scope.
- Objective preset is editable directly in Profile and continues to drive ranking in Recommendations.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.4 (core flow starts from Profile).
- `Money_Map_Spec_Packet.pdf` p.8 (Profile UI screen in MVP flow).
- `Money_Map_Spec_Packet.pdf` p.9-10 (UserProfile/runtime data for recommendations).
