import sys
import json

print (json.load(sys.stdin)['status_code'])
