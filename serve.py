"""
PLE Harness Server Entrypoint
==============================
Launched inside the evaluator container to serve the agent WebSocket protocol.
"""

import taskbridge
from harness import solve_task

if __name__ == "__main__":
    print("=" * 60)
    print("  PLE AUTONOMOUS ENGINEERING AGENT SERVER STARTING")
    print("=" * 60)
    taskbridge.run(solve_task)
