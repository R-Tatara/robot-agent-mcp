import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

load_dotenv()

MCP_SCRIPT = Path(__file__).parent / "robot_controller.py"


async def run_agent(
    user_prompt: str, history: list | None = None
) -> tuple[str, list]:
    """Connect to MCP server, run ReAct loop."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    mcp_params = StdioServerParameters(
        command="uv", args=["run", "python", str(MCP_SCRIPT)]
    )

    async with stdio_client(mcp_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await _get_langchain_tools(session)
            llm_with_tools = llm.bind_tools(tools)
            messages = (history or []) + [HumanMessage(content=user_prompt)]

            return await _execute_react_loop(session, llm_with_tools, messages)


async def _execute_react_loop(
    session: ClientSession, llm_with_tools, messages: list
) -> tuple[str, list]:
    """Run the ReAct loop until agent produces final response."""
    while True:
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return _extract_response_text(response), messages

        for call in response.tool_calls:
            await _process_tool_call(session, call, messages)


async def _get_langchain_tools(session: ClientSession) -> list:
    """Fetch tools from the MCP server and convert to LangChain format."""
    tools_list = await session.list_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,
        }
        for tool in tools_list.tools
    ]


def _extract_response_text(response) -> str:
    """Extract text content from LLM response."""
    content = response.content
    if isinstance(content, list):
        content = "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return content


async def _process_tool_call(session: ClientSession, call: dict, messages: list) -> None:
    """Execute a single tool call and append result to messages."""
    result = await session.call_tool(call["name"], call["args"])
    text = result.content[0].text if result.content else str(result)
    print(f"[tool] {call['name']} -> {text}")
    text = await _investigate_on_failure(session, text)
    messages.append(ToolMessage(content=text, tool_call_id=call["id"]))


async def _investigate_on_failure(session: ClientSession, text: str) -> str:
    """If tool result indicates failure, append error investigation result."""
    if "Failed" not in text and "Error" not in text:
        return text
    error_match = re.search(r'\d{4}', text)
    error_code = int(error_match.group()) if error_match else 0
    error_result = await session.call_tool("investigate_robot_error", {"error_code": error_code})
    error_explanation = error_result.content[0].text if error_result.content else str(error_result)
    print(f"[error_investigation] {error_explanation}")
    return f"{text}\n\n原因: {error_explanation}"
