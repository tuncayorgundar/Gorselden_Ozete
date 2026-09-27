# Tuncay Bayır - 21.08.2026
EXIT_COMMANDS = {"q", "quit", "exit"}
REPORT_TITLE = "DETECTION REPORT"
REPORT_WIDTH = 60


def repl(run_pipeline):
    print("Type 'q', 'quit', or 'exit' at any time to leave.")

    while True:
        user_input = input("\nImage source (URL or file path): ").strip().strip("\"'")

        if user_input.lower() in EXIT_COMMANDS:
            print("Exiting...")
            break

        if not user_input:
            continue

        print()

        try:
            result = run_pipeline(user_input, on_stage=_print_stage, choose_object=_choose_object)
            _print_results(result)
        except Exception as error:
            print(f"Error: {error}")


def _print_stage(message, kind="stage"):
    icon = "✔" if kind == "result" else "→"
    print(f"  {icon} {message}")


def _choose_object(candidates):
    print("\nMultiple prominent objects were detected in the image:")
    for index, candidate in enumerate(candidates, start=1):
        print(f"  [{index}] {candidate['class_name']} (score: {candidate['score']:.2f})")

    choice = input("Which one would you like to inspect? [1]: ").strip()
    if not choice:
        return candidates[0]

    try:
        selected_index = int(choice) - 1
        if 0 <= selected_index < len(candidates):
            return candidates[selected_index]
    except ValueError:
        pass

    return candidates[0]


def _print_results(result):
    print()
    print("=" * REPORT_WIDTH)
    print(REPORT_TITLE.center(REPORT_WIDTH))
    print("=" * REPORT_WIDTH)

    if not result["confident"]:
        _print_uncertain(result["detections"])
        return

    primary = result["primary"]

    label = "Selected Object" if result["was_selected"] else "Detected Object"
    _print_primary(primary, label)


def _print_uncertain(guesses):
    if not guesses:
        print("\nNo object was detected.")
        return

    print("\nNot confident, closest guesses:")
    for index, guess in enumerate(guesses, start=1):
        print(f"  [{index}] {guess['class_name']} ({_as_percent(guess['confidence'])} confidence)")


def _print_primary(detection, label):
    print(f"\n{label}: {detection['class_name']} ({_as_percent(detection['confidence'])} confidence)")

    print(f"\nKeywords: {', '.join(detection['keywords'])}")

    if detection.get("context_terms"):
        print(f"Context from earlier: {', '.join(detection['context_terms'])}")

    print(f"\nSummary: {detection['summary']}")


def _as_percent(confidence):
    return f"{round(confidence * 100)}%"
