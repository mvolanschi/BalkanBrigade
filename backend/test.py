#!/usr/bin/env python3
"""Quick harness to probe the default system prompt with sample CV scenarios.

Run it to:
- generate an automated CV evaluation for canned samples
- optionally jump into an interactive interview loop in the terminal
"""

from __future__ import annotations

import asyncio
import os
from textwrap import dedent

from fastapi import HTTPException

from backend.src import prompt_store
from backend.src.main import evaluate_cv
from backend.src.prompt_store import get_prompt
from backend.src.sessions import create_session, set_assets, append_message
from backend.src.greenpt import get_client

SAMPLES = (
    {
        "name": "Senior Backend Engineer",
        "cv_text": dedent(
            """
            Jane Doe
            Email: jane@example.com | GitHub: github.com/janedoe | 8 years experience

            Experience:
            - Lead Backend Engineer at CloudScale (2021-2024)
              Designed event-driven microservices on AWS using Python, FastAPI, and PostgreSQL.
              Reduced API latency by 38% and rolled out observability via OpenTelemetry.
            - Backend Engineer at DataForge (2017-2021)
              Built ETL pipelines in Python and Spark, maintained CI/CD with GitHub Actions.

            Skills: Python, FastAPI, PostgreSQL, Docker, AWS, Redis, Terraform
            Education: BSc Computer Science, MIT
            """
        ).strip(),
        "job_description": dedent(
            """
            We are hiring a Senior Backend Engineer to lead API development for our analytics platform.
            Must be fluent in Python, FastAPI, relational databases, and cloud infrastructure.
            Bonus points for experience with observability tooling and CI/CD automation.
            """
        ).strip(),
        "company_info": dedent(
            """
            Nimbus Analytics builds data insights tooling for enterprise finance teams.
            We value pragmatic engineering, strong documentation habits, and customer empathy.
            """
        ).strip(),
    },
    {
        "name": "Junior Frontend Developer",
        "cv_text": dedent(
            """
            John Smith
            john.smith@email.com | Portfolio: johnsmith.dev | 2 years experience

            Experience:
            - Frontend Developer at PixelWorks (2023-Present)
              Maintained React components, collaborated with designers, and improved Lighthouse scores by 20%.
            - Frontend Intern at WebNest (2022)
              Built UI prototypes, wrote Cypress tests, and contributed to component documentation.

            Skills: JavaScript, TypeScript, React, Next.js, Tailwind, Cypress
            Education: BA Interactive Media, UCLA
            """
        ).strip(),
        "job_description": dedent(
            """
            Looking for a Junior Frontend Developer comfortable with React and Next.js to ship polished user interfaces.
            Familiarity with automated testing (Cypress) and design systems is preferred.
            """
        ).strip(),
        "company_info": dedent(
            """
            BrightLeaf is a seed-stage startup helping small retailers run data-driven marketing campaigns.
            Team works remotely across US time zones and iterates quickly based on user feedback.
            """
        ).strip(),
    },
)


async def run_sample(sample: dict[str, str]) -> None:
    print(f"\n=== {sample['name']} ===")
    try:
        result = await evaluate_cv(
            cv_text=sample["cv_text"],
            job_description=sample["job_description"],
            company_info=sample["company_info"],
        )
    except HTTPException as exc:
        print(f"Evaluation failed [{exc.status_code}]: {exc.detail}")
        return
    except Exception as exc:  # pragma: no cover - ensure unexpected errors surface clearly
        print(f"Evaluation failed: {exc}")
        return

    reply = result.get("reply", "(no reply)")
    print(reply)

    if prompt_continue():
        await run_interactive_interview(sample)


def prompt_continue() -> bool:
    """Ask the user if they want to enter the live interview loop."""

    choice = input("Start interactive interview? [y/N]: ").strip().lower()
    return choice in {"y", "yes"}


async def run_interactive_interview(sample: dict[str, str]) -> None:
    """Spin up an interview session in the terminal using the current system prompt."""

    base_prompt = prompt_store.DEFAULT_PROMPT
    session = create_session(system_prompt=base_prompt)
    session = set_assets(
        session.id,
        cv=sample["cv_text"],
        job_description=sample["job_description"],
        company_info=sample["company_info"],
        base_prompt=base_prompt,
    )

    # Kick off the chat by asking the assistant to begin the interview.
    append_message(
        session.id,
        role="user",
        content="Please begin the interview based on the provided materials.",
    )

    try:
        first_reply = await send_chat(session)
    except HTTPException as exc:
        print(f"Interview start failed [{exc.status_code}]: {exc.detail}")
        return
    except Exception as exc:  # pragma: no cover - keep unexpected errors visible
        print(f"Interview start failed: {exc}")
        return

    print(f"Interviewer: {first_reply}")

    while True:
        user_text = input("You: ").strip()
        if user_text.lower() in {"", "quit", "exit"}:
            print("Conversation ended.\n")
            break

        append_message(session.id, role="user", content=user_text)

        try:
            reply = await send_chat(session)
        except HTTPException as exc:
            print(f"Assistant error [{exc.status_code}]: {exc.detail}")
            break
        except Exception as exc:  # pragma: no cover
            print(f"Assistant error: {exc}")
            break

        print(f"Interviewer: {reply}")


async def send_chat(session) -> str:
    """Send the current session history to GreenPT and capture the assistant reply."""

    client = get_client()
    resp = await client.chat([m.dict() for m in session.messages])

    assistant_text = extract_assistant_text(resp)
    append_message(session.id, role="assistant", content=assistant_text)
    return assistant_text


def extract_assistant_text(resp) -> str:
    """Mirror backend parsing logic to recover assistant text from GreenPT."""

    assistant_text = ""
    if isinstance(resp, dict):
        choices = resp.get("choices") or []
        if choices:
            first = choices[0]
            if isinstance(first, dict) and "message" in first and isinstance(first["message"], dict):
                assistant_text = first["message"].get("content", "")
            else:
                assistant_text = first.get("text", "")

    if not assistant_text and isinstance(resp, dict):
        assistant_text = resp.get("text", "") or resp.get("response", "")

    if not assistant_text:
        raise HTTPException(status_code=502, detail="GreenPT returned an empty interview reply.")

    return assistant_text.strip()


def ensure_api_key() -> None:
    if not os.getenv("GREENPT_API_KEY"):
        raise SystemExit(
            "GREENPT_API_KEY not configured. Export the key before running this test harness."
        )


async def main() -> None:
    ensure_api_key()
    for sample in SAMPLES:
        await run_sample(sample)


if __name__ == "__main__":
    asyncio.run(main())
