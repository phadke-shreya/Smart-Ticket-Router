from ticket_router.demo import load_tickets, run_timed_demo, manual_estimate_seconds, MANUAL_SECONDS_PER_TICKET


def main():
    tickets = load_tickets()
    print(f"Routing {len(tickets)} tickets with AI...\n")

    per_ticket_results, ai_elapsed = run_timed_demo(tickets)

    for entry in per_ticket_results:
        if entry["error"]:
            print(f'#{entry["id"]:>2} -> ERROR: {entry["error"]}')
        else:
            r = entry["result"]
            print(f'#{entry["id"]:>2} -> {r["category"]:<20} {r["priority"]:<7} {r["team"]}')

    manual_seconds = manual_estimate_seconds(len(tickets))

    print("\n" + "=" * 60)
    print(f"AI routing time for {len(tickets)} tickets:      {ai_elapsed:.2f} seconds (measured)")
    print(f"Estimated manual routing time for {len(tickets)} tickets: "
          f"{manual_seconds / 60:.1f} minutes (assumption: {MANUAL_SECONDS_PER_TICKET}s/ticket)")
    print(f"Speedup: ~{manual_seconds / ai_elapsed:.0f}x faster")


if __name__ == "__main__":
    main()
