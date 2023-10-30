"""Module parses json and returns a single field."""
import sys
import json

if len(sys.argv) < 2:
    print("expected field name passed as argument", file=sys.stderr)
    sys.exit(127)
print (json.load(sys.stdin)[sys.argv[1]])
