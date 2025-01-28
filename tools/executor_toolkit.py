from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_agentchat.agents import CodeExecutorAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken


async def run_code_executor_agent(code: str, repo_name: str) -> str:
    """
    Executes the provided code in the given Repo. Can be used to run created pytest files.
    
    Args:
        code (str): The commands to run in the container
        repo_name (str): the name of the repository

    Returns:
        str: The result of the execution
    """
    code = code.replace("\n```", "```")
    docker_executor = DockerCommandLineCodeExecutor(work_dir=f"coding/{repo_name}", auto_remove=True)
    # Create a code executor agent that uses a Docker container to execute code.
    await docker_executor.start()
    code_executor_agent = CodeExecutorAgent("code_executor", code_executor=docker_executor)
    # Run the agent with a given code snippet.
    task = TextMessage(
        content=code,
        source="user",
    )
    response = await code_executor_agent.on_messages([task], CancellationToken())

    # Stop the code executor.
    await docker_executor.stop()
    return response.chat_message.content