from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class IndividualParticipantToAddSchema(BaseModel):
    type: Literal["individual"]
    name: str = Field(
        description="Name of the individual to add. Generate a creative name that fits the role and mission. You can "
        "use play on words, stereotypes, or any other way you want to be original."
    )
    role: str = Field(description='Role of the participant to add. Title like "CEO" or "CTO", for example.')
    mission: str = Field(
        description="Personal mission of the individual to add. Should be a detailed mission statement."
    )
    symbol: str = Field(
        description="A unicode symbol of the individual to add (for presentation in chat). This "
        "needs to reflect the role."
    )
    tools: Optional[List[str]] = Field(
        description="List of useful tools that an individual should have access to in order to achieve their goal. "
        "Must be one of the available tools given as input. Do not give tools if you think the individual "
        "should not have access to any tools or non of the available tools are useful for the goal."
    )

    def __str__(self):
        return f"{self.symbol} {self.name} ({self.role})"


class CreateTeamCompositionForGoalOutputSchema(BaseModel):
    team_composition: List[IndividualParticipantToAddSchema] = Field(
        description="List of members that make up the team. Must include the fixed members."
    )
    interaction_schema: str = Field(
        description="A member interaction schema that includes the phases, "
        "how members should interact with each other to achieve the goal, etc."
    )


__all__ = ["IndividualParticipantToAddSchema", "CreateTeamCompositionForGoalOutputSchema"]
