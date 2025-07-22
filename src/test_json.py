import json
from pydantic import BaseModel, Field, ConfigDict

# Your exact NPCData class
class NPCData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(description="A fantasy name appropriate for the given race")
    appearance: str = Field(description="A detailed physical description of the character, 3-5 sentences")
    personality: str = Field(description="Describe their traits, demeanor, and motivations, 2-3 sentences")
    backstory: str = Field(description="A brief history of the character, 2-3 sentences")
    plot_hooks: str = Field(
        description="A bulleted list of 2-3 specific, actionable plot hooks for a DM, using '*' for bullets")
    roleplaying_tips: str = Field(
        description="Provide tips on mannerisms, voice, and attitude for the DM, 2-3 sentences")

# Generate and print the schema
schema = NPCData.model_json_schema()

# Pretty-print the JSON so it's easy to read
print(json.dumps(schema, indent=2))