from rich.console import Console
from langchain_openai import ChatOpenAI
from smolagents import tool

@tool
def analyze_diff(diff: str, llm: ChatOpenAI) -> str:
    """
    Analyzes the diff and summarizes key findings.

    Args:
        diff: The diff text to analyze.
        llm: The ChatOpenAI instance to use.
    Returns:
        A summary of key findings as a string.
    """
    prompt = (
        "You are a code analysis assistant. Analyze the following diff and summarize your key findings:\n\n"
        f"{diff}"
    )
    Console().print("🤖 Starting analysis of the diff. This may take a moment...")
    result = llm.invoke(prompt)  # Pass prompt directly as a string.
    analysis = result.content if hasattr(result, "content") else result
    Console().print("✅ Analysis complete!")
    return analysis

@tool
def generate_report(diff: str, analysis: str, pr_link: str, target: str, llm: ChatOpenAI) -> str:
    """
    Generates the final PR report based on the diff and analysis.

    Args:
        diff: The full diff text.
        analysis: The analysis summary.
        pr_link: The GitHub PR link.
        target: The output format target ("github" or "slack").
        llm: The ChatOpenAI instance to use.
    Returns:
        The generated PR report as a string.
    """
    if target.lower() == "slack":
        report_template = (
            "Guys, please review the following PR.\n\n"
            "*PR Link:* <{pr_link}>\n\n"
            "*Description:*  \n"
            "[Summarize the changes and key updates.]\n\n"
            "*Why:*  \n"
            "[Explain the reasoning and motivation behind the changes.]\n\n"
            "*Risks:*  \n"
            "[List any potential risks or side effects.]\n\n"
            "*Code Snippets & Explanation:*  \n"
            "[Extract and explain relevant code snippet(s) from the diff; if including code, wrap it in triple backticks (```)]."
        )
    else:
        report_template = (
            "## Description 📝\n"
            "[Summarize the changes and key updates.]\n\n"
            "## Why? ✅\n"
            "[Explain the reasoning and motivation behind the changes.]\n\n"
            "## Risks? ⚠️\n"
            "[List any potential risks or side effects.]\n\n"
            "## Code Snippets & Explanation 📑\n"
            "[Extract and explain relevant code snippet(s) from the diff; if including code, wrap it in triple backticks (```)].\n\n"
            "PR Link: {pr_link}"
        )
    report_template = report_template.format(pr_link=pr_link)
    report_prompt = (
        "You are an assistant that summarizes code changes for a pull request. Based on the provided diff and analysis, "
        "generate a report using the following structure:\n\n"
        f"{report_template}\n\n"
        "Diff:\n"
        f"{diff}\n\n"
        "Analysis:\n"
        f"{analysis}"
    )
    Console().print("📝 Generating formatted PR report. Please wait...")
    result = llm.invoke(report_prompt)
    pr_report = result.content if hasattr(result, "content") else result
    Console().print("✅ PR report generation complete!")
    return pr_report
