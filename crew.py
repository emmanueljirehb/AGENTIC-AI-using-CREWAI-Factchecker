from crewai import Agent, Task, Crew, Process
from pathlib import Path
import yaml

from tools.custom_tool import search_tool

def load_agents():
    agents_file = Path(__file__).parent / "config" / "agents.yaml"
    with open(agents_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_tasks():
    tasks_file = Path(__file__).parent / "config" / "tasks.yaml"
    with open(tasks_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_agents(agent_configs):
    built_agents = {}
    for name, config in agent_configs.items():
        built_agents[name] = Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=[search_tool] if "serper_tool" in config.get("tools", []) else [],
            verbose=True,
            memory=True
        )
    return built_agents


def build_tasks(task_configs, agents, claim=None, url=None, topic=None):
    built_tasks = []

    for name, config in task_configs.items():
        # Skip task if required input is missing
        if "claim" in name and not claim:
            continue
        if "url" in name and not url:
            continue
        if "summary" in name and not (url or topic):
            continue

        # Safely substitute placeholders
        description = config["description"]
        expected_output = config["expected_output"]

        description = description.replace("{claim}", claim or "")
        description = description.replace("{url}", url or "")
        description = description.replace("{topic}", topic or "")

        # Assign correct agent
        if "fact_check" in name:
            agent = agents.get("fact_checker")
        elif "url_summary" in name:
            agent = agents.get("url_summarizer")
        else:
            agent = list(agents.values())[0]  # fallback

        task = Task(
            description=description,
            expected_output=expected_output,
            agent=agent
        )
        built_tasks.append(task)

    return built_tasks


def build_crew(claim=None, url=None, topic=None):
    agents_yaml = load_agents()
    tasks_yaml = load_tasks()

    agents = build_agents(agents_yaml)
    tasks = build_tasks(tasks_yaml, agents, claim=claim, url=url, topic=topic)

    return Crew(
        agents=list(set([task.agent for task in tasks])),
        tasks=tasks,
        process=Process.sequential
    )


# For claim or URL input from Streamlit
def get_url_crew(claim=None, url=None):
    return build_crew(claim=claim, url=url)


# For uploaded file with general topic
def crew_from_topic(topic: str):
    return build_crew(topic=topic)