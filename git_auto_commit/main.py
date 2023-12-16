import subprocess
import sys
import git
import re
import random

from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from langchain.llms import Bedrock
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

AWS_DEFAULT_PROFILE = "default"
AWS_DEFAULT_REGION_NAME = "us-east-1"
AWS_DEFAULT_MODEL_ID = "cohere.command-light-text-v14"
LINES_OF_CONTEXT = 3
FILE_PATTERN = r"^diff --git a/(.+?) b/.+?$"
CHANGE_PATTERN = r"^(\+|\-|\s)"
EMPTY = 10


class Message(BaseModel):
    message: str = Field(description="commit message")


parser = PydanticOutputParser(pydantic_object=Message)

template = """
Context: As an AI trained in the Conventional Commits specification, your role is to analyze code changes and craft commit messages. 
These messages should be succinct, clear, and adhere to the structured Conventional Commits format.

Input Git Diff: << EOF 
{git_diff}
EOF

Task: Examine the Git diff enclosed within the EOF markers to pinpoint significant modifications. Concentrate on:
1. File Status: Look for files that are either modified, added, or deleted. If applicable, mention the scope for additional context.
2. Nature of Changes: Identify the core changes in the code. This could include new features, bug fixes, refactoring, etc. 
   Specify the change type (e.g., feat, fix, docs, style, refactor, perf, test, chore).
3. Dependency and Structure Changes: Note any alterations in dependencies or overall structural changes.

Output: Craft a Commit Message following the template:
{{"message": "Your commit message here"}}

Note: The message should start without a capital letter and not end with a period.

Provide ONLY the message that describe the main purpose and impact of the changes.
"""

prompt = PromptTemplate(template=template, input_variables=["git_diff"])


def read_git_diff(lines_of_context=LINES_OF_CONTEXT):
    try:
        repo = git.Repo(search_parent_directories=True)
        diff = repo.git.diff("HEAD", unified=lines_of_context)
        return diff
    except git.InvalidGitRepositoryError:
        return "Error: Not a valid git repository."
    except Exception as e:
        return f"Unexpected error: {e}"


def parse_diff_output(diff_output, max_line_length=80, max_characters_length=1500):
    file_diffs = {}
    file_pattern = re.compile(FILE_PATTERN, re.MULTILINE)
    change_pattern = re.compile(CHANGE_PATTERN)
    current_file = None

    def truncate_line(line):
        return line[:max_line_length] + "..." if len(line) > max_line_length else line

    def sample_lines(diff_lines, max_length):
        sampled_lines = []
        available_lines = list(diff_lines)

        while available_lines and max_length > 0:
            line = random.choice(available_lines)
            line_length = len(line[1]) + 1
            if max_length - line_length >= 0:
                sampled_lines.append(line)
                max_length -= line_length
            available_lines.remove(line)

        return sampled_lines

    for index, line in enumerate(diff_output.split("\n")):
        file_match = file_pattern.match(line)
        if file_match:
            current_file = file_match.group(1)
            file_diffs[current_file] = []
        elif current_file:
            file_diffs[current_file].append((index, truncate_line(line)))

    for file, lines_with_indices in file_diffs.items():
        prioritized_lines = [
            (index, line)
            for index, line in lines_with_indices
            if change_pattern.match(line)
        ]
        other_lines = [
            (index, line)
            for index, line in lines_with_indices
            if not change_pattern.match(line)
        ]

        sampled_prioritized_lines = sample_lines(
            prioritized_lines, max_characters_length
        )
        remaining_length = max_characters_length - sum(
            len(line[1]) + 1 for line in sampled_prioritized_lines
        )

        if remaining_length > 0:
            sampled_other_lines = sample_lines(other_lines, remaining_length)
            all_sampled_lines = sampled_prioritized_lines + sampled_other_lines
        else:
            all_sampled_lines = sampled_prioritized_lines

        all_sampled_lines.sort(key=lambda x: x[0])
        file_diffs[file] = "\n".join(line[1] for line in all_sampled_lines)

    parse_diff_output = ""
    for file, diff in file_diffs.items():
        parse_diff_output += f"File: {file}\nChanges:\n{diff}\n\n"

    return parse_diff_output


def generate_commit_message(aws_profile_name, region_name, model_id):
    diff_output = read_git_diff()
    if len(diff_output) <= EMPTY:
        return ""

    llm = Bedrock(
        credentials_profile_name=aws_profile_name,
        region_name=region_name,
        model_id=model_id,
    )

    print(prompt.format(git_diff=diff_output))

    llm_chain = LLMChain(llm=llm, prompt=prompt)

    if isinstance(diff_output, str):
        diff_output = parse_diff_output(diff_output)

    output = llm_chain.run(diff_output)
    return parser.parse(output).message


def filter_commit_args(args):
    """Filter out '-m', '--message', '--profile', '--region', and '--model' parameters and throw an error if '-m' or '--message' are found."""
    args = list(args) if isinstance(args, tuple) else args
    profile_name = AWS_DEFAULT_PROFILE
    region_name = AWS_DEFAULT_REGION_NAME
    model_id = AWS_DEFAULT_MODEL_ID

    if "-m" in args or any(arg.startswith("--message") for arg in args):
        raise ValueError("The '-m/--message' parameter is not allowed.")

    if "--profile" in args:
        profile_index = args.index("--profile")
        if profile_index < len(args) - 1:
            profile_name = args[profile_index + 1]
            del args[profile_index : profile_index + 2]

    if "--region" in args:
        region_index = args.index("--region")
        if region_index < len(args) - 1:
            region_name = args[region_index + 1]
            del args[region_index : region_index + 2]

    if "--model" in args:
        model_index = args.index("--model")
        if model_index < len(args) - 1:
            model_id = args[model_index + 1]
            del args[model_index : model_index + 2]

    return list(args), profile_name, region_name, model_id


def color_text(text, color_code):
    """Add ANSI color code to each line of the text."""
    colored_lines = [f"\033[{color_code}m{line}\033[0m" for line in text.split("\n")]
    return "\n".join(colored_lines)


def auto_commit(*args):
    try:
        filtered_args, aws_profile_name, region_name, model_id = filter_commit_args(
            args
        )
        message = generate_commit_message(aws_profile_name, region_name, model_id)
        commit_command = ["git", "commit", *filtered_args, "-m", message]

        output = subprocess.run(
            commit_command, check=True, text=True, capture_output=True
        )
        print(color_text(output.stdout, 32))
        print(color_text(message, 32))
    except ValueError as e:
        print(color_text(f"Argument Error: {e}", 31))
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(color_text(f"{e.output}", 31))
        sys.exit(1)
    except Exception as e:
        print(color_text(f"Unexpected error: {e}", 31))
        sys.exit(1)


def main():
    auto_commit(*sys.argv[1:])


if __name__ == "__main__":
    main()
