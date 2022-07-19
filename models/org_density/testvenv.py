# Check virtual env and confirm activate venv
# import sys
# sys.prefix == sys.base_prefix

import os
absolute_path = os.path.abspath(__file__)
print(absolute_path)