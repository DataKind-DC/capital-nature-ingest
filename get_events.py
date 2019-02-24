from events import montgomery, ans, arlington, casey_trees, fairfax, nps, vnps

def main():
    event_sources = [montgomery, ans, arlington, casey_trees, fairfax, nps, vnps]
    events = []
    for event_source in event_sources:
        event_source_events = event_source.main()
        events.extend(event_source_events)

    return events

if __name__ == '__main__':
    events = main()
    print(len(events))
