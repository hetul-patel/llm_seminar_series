"""Updates the public leaderboard after evaluating given submission.

Sample command:
python -m scripts.leaderboard \
    --github_user=your_github_user \
    --prompt_file=baseline
"""

import logging
import re
from collections.abc import Sequence

import pandas as pd
from absl import app, flags
from scripts import dataset, evaluate_lib

_PROMPT = flags.DEFINE_string(
    "prompt", None, "Name of the submitted prompt to evaluate."
)

_GITHUB_USER = flags.DEFINE_string(
    "github_user", None, "Github username to add an entry in leaderboard."
)


_LEADERBORAD = "leaderboard.md"  # current leaderboard


def generate_leaderboard(prompt_name: str, accuracy: float, github_user: str):
    """Generates leaderboard."""
    # Read the markdown table into a DataFrame
    with open(_LEADERBORAD, "r") as file:
        content = file.read()

    start_marker = "<!-- leader-board-begins -->\n"
    start_index = content.find(start_marker)
    end_index = content.find("\n<!-- leader-board-ends -->")
    table_content = content[start_index:end_index]

    # Extract rows using regex
    rows = re.findall(
        r"\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|", table_content
    )[2:]

    # Create a DataFrame from the extracted rows
    df = pd.DataFrame(
        rows,
        columns=[
            "Rank",
            "Profile Image",
            "GitHub Username",
            "Solution",
            "Accuracy %",
        ],
    )

    # Strip extra spaces before and after text in each cell
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Convert "Rank" column to integer and "Accuracy %" column to float
    df["Rank"] = df["Rank"].astype(int)
    df["Accuracy %"] = df["Accuracy %"].astype(float)

    # Add a new entry to the DataFrame
    repo_url = "https://github.com/infocusp/llm_seminar_series/blob/main/session_2/challenge/submissions"
    new_entry = {
        "Rank": len(df) + 1,
        "Profile Image": f'<img src="https://github.com/{github_user}.png" '
        + 'width="50px" height="50px" class="profile-image">',
        "GitHub Username": f"[{github_user}](https://github.com/{github_user})",
        "Solution": f"[{prompt_name}]({repo_url}/{prompt_name}.py)",
        "Accuracy %": accuracy,
    }

    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)

    # Keep only the highest submission for each user
    highest_indices = df.groupby("GitHub Username")["Accuracy %"].idxmax()
    df_highest = df.loc[highest_indices]

    # Sort the DataFrame by "Accuracy %" column in descending order
    df_sorted = df_highest.sort_values(
        by="Accuracy %", ascending=False
    ).reset_index(drop=True)

    # Update the "Rank" column after sorting
    df_sorted["Rank"] = df_sorted.index + 1

    # Convert the DataFrame back to markdown format
    markdown_table = df_sorted.to_markdown(index=False)

    # Replace the existing table in the markdown file with the sorted table
    new_content = (
        content[: start_index + len(start_marker)]
        + markdown_table
        + content[end_index:]
    )

    # Write the updated content back to the markdown file
    with open(_LEADERBORAD, "w") as file:
        file.write(new_content)

    logging.info(
        "Submission by %s with prompt %s updated in the leaderboard.",
        github_user,
        prompt_name,
    )


def update_leaderboard(prompt_name: str, github_user: str):
    """Generates a public leaderboard by evaluating given submission."""
    sample_dataset = dataset.load_sample_test_set(samples_dir="sample_inputs")
    acc = evaluate_lib.evaluate(
        dataset=sample_dataset, prompt_name=prompt_name
    )
    generate_leaderboard(
        prompt_name=prompt_name, accuracy=acc, github_user=github_user
    )


def main(argv: Sequence[str]) -> None:
    """Entrypoint."""
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")
    logging.getLogger().setLevel(logging.INFO)
    update_leaderboard(
        prompt_name=_PROMPT.value, github_user=_GITHUB_USER.value
    )


if __name__ == "__main__":
    flags.mark_flag_as_required("prompt")
    flags.mark_flag_as_required("github_user")
    app.run(main)