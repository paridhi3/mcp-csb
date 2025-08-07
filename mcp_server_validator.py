# mcp_server_validator.py
from agents.mcp import MCPToolServer, tool
from pydantic import BaseModel, ValidationError, constr

class CaseStudySummary(BaseModel):
    file: str
    summary: constr(min_length=30)
    category_domain_tech: constr(min_length=10)
    full_text: constr(min_length=100)

class ValidatorMCPServer(MCPToolServer):
    @tool
    def validate(self, item: dict):
        try:
            CaseStudySummary(**item)
            return {"valid": True}
        except ValidationError as e:
            return {"valid": False, "errors": str(e)}

if __name__ == "__main__":
    ValidatorMCPServer().serve()
