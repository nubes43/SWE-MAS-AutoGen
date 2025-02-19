import os
import agentops
from dotenv import load_dotenv
from autogen import GroupChat, GroupChatManager, ConversableAgent
from autogen.agentchat import gather_usage_summary
from tools.executor_toolkit import run_code_executor_agent
from tools.file_toolkit import write_file, read_file, modify_function, modify_function_args, convert_function_to_method, extract_function, find_and_replace, list_files_in_repository, list_functions, modify_return_type, remove_function
from tools.github_toolkit import get_issue_analysis, clone_repository, checkout_commit
from prompts.autogen_prompts import GITHUB_PROMPT, PROMPT_FILE_MANIPULATOR, PROMPT_CODE_GEN, CODE_PREP, SELECTION_PROMPT
import pyarrow.parquet as pq
import random
import re

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

# issue_analyzer_agent.register_for_llm(name="get_issue_analysis", description="Analyze a GitHub Issue.")(get_issue_analysis)
# tool_executor.register_for_execution(name="get_issue_analysis")(get_issue_analysis)

issue_analyzer_agent.register_for_llm(
    name="clone_repository", description="Clone a Github Repository."
    )(clone_repository)
tool_executor.register_for_execution(name="clone_repository")(clone_repository)

issue_analyzer_agent.register_for_llm(
    name="checkout_commit", description="Checkout to a specific commit in an already cloned GitHub repository. The repository must be cloned and located in './coding/'."
    )(checkout_commit)
tool_executor.register_for_execution(name="checkout_commit")(checkout_commit)

file_agent.register_for_llm(name="write_file", description="Create or Overwrite a Python Code File.")(write_file)
tool_executor.register_for_execution(name="write_file")(write_file)
file_agent.register_for_llm(name="read_file", description="Read the Content of a python file")(read_file)
tool_executor.register_for_execution(name="read_file")(read_file)
file_agent.register_for_llm(name="modify_function", description="Modify a specific python function in the file.")(modify_function)
tool_executor.register_for_execution(name="modify_function")(modify_function)
file_agent.register_for_llm(name="find_and_replace", description="Use RegEx Find and Replace to edit python code.")(find_and_replace)
tool_executor.register_for_execution(name="find_and_replace")(find_and_replace)
file_agent.register_for_llm(name="modify_function_args", description="Change Parameters of a python function within the file.")(modify_function_args)
tool_executor.register_for_execution(name="modify_function_args")(modify_function_args)
file_agent.register_for_llm(name="modify_return_type", description="Change Return Type of a python function within the file.")(modify_return_type)
tool_executor.register_for_execution(name="modify_return_type")(modify_return_type)
file_agent.register_for_llm(name="extract_function", description="Extracts the code of a python function within a file.")(extract_function)
tool_executor.register_for_execution(name="extract_function")(extract_function)
file_agent.register_for_llm(name="list_functions", description="Lists all python functions of a file.")(list_functions)
tool_executor.register_for_execution(name="list_functions")(list_functions)
file_agent.register_for_llm(name="list_files_in_repository", description="Lists all Files in a local repository.")(list_files_in_repository)
tool_executor.register_for_execution(name="list_files_in_repository")(list_files_in_repository)

tester_agent.register_for_llm(name="write_file", description="Create a Test File.")(write_file)

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

constrained_graph_chat = GroupChat(
    agents=[
        issue_analyzer_agent, router_agent, coder_agent, file_agent, tester_agent, tool_executor
        ],
    allowed_or_disallowed_speaker_transitions=allowed_transitions,
    speaker_transitions_type="allowed",
    messages=[],
    max_round=30,
    send_introductions=True,
)

constrained_group_chat_manager = GroupChatManager(
    groupchat=constrained_graph_chat,
    llm_config=gpt4_config,
    system_message=SELECTION_PROMPT,
)

table = pq.read_table('.\\swebench\\test-00000-of-00001.parquet')

data_dict = table.to_pydict()
columns = data_dict.keys()


rows = [{col: data_dict[col][i] for col in columns} for i in range(len(next(iter(data_dict.values()))))]

random.seed(30)
random.shuffle(rows)
for row in rows[41:50]:
    agentops.init(api_key="f80d1679-0f59-48c6-9b76-6db99cdcaee2", default_tags=["autogen"])
    repo = row["repo"]
    print(repo)
    issue = int(re.search(r'\d+', row["instance_id"]).group())
    print(issue)
    commit = row["base_commit"]
    issue_detail = row["problem_statement"]
    print(commit)
    chat_result = constrained_group_chat_manager.initiate_chat(
        issue_analyzer_agent,
        message=f"{repo}/{issue} with base commit {commit} \n ISSUE Description:\n {issue_detail}",
        summary_method="reflection_with_llm",
    )
    agentops.end_session('Success')

