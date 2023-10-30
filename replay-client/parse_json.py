import sys
import json

if len(sys.argv) < 2:
    print("expected field name passed as argument", file=sys.stderr)
    exit(127)
print (json.load(sys.stdin)[sys.argv[1]])
