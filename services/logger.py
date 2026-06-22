from loguru import logger
import sys
import json

# Configure logger to output JSON lines to stdout
logger.remove()
logger.add(sys.stdout, format='{"time": "{time}", "level": "{level}", "message": "{message}", "extra": {extra}}', serialize=True)
