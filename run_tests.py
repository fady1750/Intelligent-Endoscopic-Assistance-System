from test_backend import *
import sys
failed = 0
for name, obj in list(globals().items()):
    if name.startswith('test_') and callable(obj):
        try:
            obj()
            print(name + ': OK')
        except Exception:
            print(name + ': FAILED')
            import traceback
            traceback.print_exc()
            failed += 1
sys.exit(failed)
