import os
import agentops
from dotenv import load_dotenv
from autogen import GroupChat, GroupChatManager, ConversableAgent
from autogen.agentchat import gather_usage_summary
from tools.executor_toolkit import run_code_executor_agent
from tools.file_toolkit import manipulate_file
from tools.github_toolkit import get_issue_analysis, clone_repository, checkout_commit
from prompts.autogen_prompts import GITHUB_PROMPT, PROMPT_FILE_MANIPULATOR, PROMPT_CODE_GEN, CODE_PREP, SELECTION_PROMPT

#agentops.init(api_key="f80d1679-0f59-48c6-9b76-6db99cdcaee2", default_tags=["autogen"])
load_dotenv()

gpt4_config = {
    "config_list": [
        {
            "model": "gpt-4o-mini", 
            "temperature": 0.7, 
            "api_key": os.environ["OPENAI_API_KEY"],
            "cache_seed": None
        }
    ]
}

issue_analyzer_agent = ConversableAgent(
    "IssueAnalyzer",
    system_message=GITHUB_PROMPT,
    llm_config=gpt4_config,
    human_input_mode="NEVER",  # Never ask for human input.
)

coder_agent = ConversableAgent(
    "Programmer",
    system_message=PROMPT_CODE_GEN,
    llm_config=gpt4_config,
    human_input_mode="NEVER",  # Never ask for human input.
)

file_agent = ConversableAgent(
    "FileManager",
    system_message=PROMPT_FILE_MANIPULATOR,
    llm_config=gpt4_config,
    human_input_mode="NEVER",  # Never ask for human input.
)

tester_agent = ConversableAgent(
    "Tester",
    system_message=CODE_PREP,
    llm_config=gpt4_config,
    human_input_mode="TERMINATE",  # Never ask for human input.
)

router_agent = ConversableAgent(
    "Router",
    system_message="""You are the Manager of a group of the following agents:
        -Agent for Code Generation (Programmer). This agent is used for fixing the bugs.
        -Agent for File Manipulation (File Manager). This agent is used for implementing the changes.
        
        When prompted you have to decide which of the agents has to work.
        In your first initiation this will alway be the code agent. The other times decide based on the message history.
        When the File Agent claims TERMINATE you transfer to the tester agent. When the tester agent responds with "SUCCESSFUL TERMINATEEXEC" you also have to respond with "SUCCESSFUL TERMINATEEXEC"
    """,
    is_termination_msg=lambda msg: "successful terminateexec" in msg["content"].lower(),
)

tool_executor = ConversableAgent(
    name="ToolExecutor",
    llm_config=gpt4_config,
    system_message="Always hand back the ToolResponse to the agent that invoked the tool.",
    human_input_mode="NEVER",
)

issue_analyzer_agent.register_for_llm(name="get_issue_analysis", description="Analyze a GitHub Issue.")(get_issue_analysis)
tool_executor.register_for_execution(name="get_issue_analysis")(get_issue_analysis)

issue_analyzer_agent.register_for_llm(
    name="clone_repository", description="Clone a Github Repository."
    )(clone_repository)
tool_executor.register_for_execution(name="clone_repository")(clone_repository)

issue_analyzer_agent.register_for_llm(
    name="checkout_commit", description="Checkout to a specific commit in an already cloned GitHub repository. The repository must be cloned and located in './coding/'."
    )(checkout_commit)
tool_executor.register_for_execution(name="checkout_commit")(checkout_commit)

file_agent.register_for_llm(name="manipulate_file", description="Manipulate a local File.")(manipulate_file)
tool_executor.register_for_execution(name="manipulate_file")(manipulate_file)

tester_agent.register_for_llm(name="manipulate_file", description="Create a Test File.")(manipulate_file)

tester_agent.register_for_llm(
    name="run_code_executor_agent",
    description="Run the Code Execution."
    )(run_code_executor_agent)
tool_executor.register_for_execution(name="run_code_executor_agent")(run_code_executor_agent)

allowed_transitions = {
    issue_analyzer_agent: [router_agent, tool_executor],
    router_agent: [file_agent, coder_agent, tester_agent],
    coder_agent: [router_agent],
    file_agent: [router_agent, tool_executor],
    tester_agent: [router_agent, tool_executor],
    tool_executor: [file_agent, tester_agent, issue_analyzer_agent, router_agent, coder_agent]
}

disallowed_transitions = {
    issue_analyzer_agent: [],
    router_agent: [],
    coder_agent: [],
    file_agent: [],
    tester_agent: [],  
}

constrained_graph_chat = GroupChat(
    agents=[
        issue_analyzer_agent, router_agent, coder_agent, file_agent, tester_agent, tool_executor
        ],
    allowed_or_disallowed_speaker_transitions=disallowed_transitions,
    speaker_transitions_type="disallowed",
    messages=[],
    max_round=30,
    send_introductions=True,
)

constrained_group_chat_manager = GroupChatManager(
    groupchat=constrained_graph_chat,
    llm_config=gpt4_config,
    system_message=SELECTION_PROMPT,
)

chat_result = constrained_group_chat_manager.initiate_chat(
    issue_analyzer_agent,
    message="""
    astropy/astropy/12906 Checkout to commit d16bfe05a744909de4b27f5875fe0d4ed41ce607 Analyze it, Clone the Repository, FIX It, Test the fix.
    """,
    summary_method="reflection_with_llm",
)

all_agents = list([
    issue_analyzer_agent, router_agent, coder_agent, file_agent, tester_agent, tool_executor
    ])

for agent in all_agents:
    print(agent.name + ":\n")
    print(gather_usage_summary(agents=[agent]))
print("ALL:\n")
print(gather_usage_summary(agents=all_agents))
#agentops.end_session('Success')
