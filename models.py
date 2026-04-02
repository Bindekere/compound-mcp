from pydantic import BaseModel, Field


class CanonicalState(BaseModel):
    session_id: str
    goal: str
    constraints: list[str] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_action: str
