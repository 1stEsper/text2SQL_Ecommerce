import argparse
import sys
from typing import Any

from text_to_sql.executor import QueryResult, execute_sql
from text_to_sql.generator import generate_sql
from text_to_sql.validator import validate_sql


def _format_table(result: QueryResult, maximum_width: int = 40) -> str:
    if not result.rows:
        return "No rows returned."

    values = [result.columns, *result.rows]
    formatted = [
        [
            str(value)[:maximum_width] if value is not None else "NULL"
            for value in row
        ]
        for row in values
    ]
    widths = [
        max(len(row[index]) for row in formatted)
        for index in range(len(result.columns))
    ]

    def render(row: list[str]) -> str:
        return " | ".join(
            value.ljust(widths[index])
            for index, value in enumerate(row)
        )

    separator = "-+-".join("-" * width for width in widths)
    return "\n".join(
        [render(formatted[0]), separator]
        + [render(row) for row in formatted[1:]]
    )


def _question_from_arguments(arguments: list[str]) -> str:
    if arguments:
        return " ".join(arguments)
    return input("Question: ").strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate approved, read-only DuckDB SQL with Gemini."
    )
    parser.add_argument("question", nargs="*", help="Natural-language question")
    parsed = parser.parse_args(argv)

    try:
        question = _question_from_arguments(parsed.question)
        generated = generate_sql(question)
        sql = validate_sql(generated.sql)

        print("\nGenerated SQL:\n")
        print(sql)
        print("\nExplanation:\n")
        print(generated.explanation)

        if generated.assumptions:
            print("\nAssumptions:")
            for assumption in generated.assumptions:
                print(f"- {assumption}")

        approval = input("\nExecute this read-only query? [y/N]: ").strip().lower()
        if approval not in {"y", "yes"}:
            print("Query was not executed.")
            return 0

        result = execute_sql(sql)
        print("\nResults:\n")
        print(_format_table(result))
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

