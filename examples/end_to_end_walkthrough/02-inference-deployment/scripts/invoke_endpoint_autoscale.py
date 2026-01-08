import subprocess
import time
import shlex
import argparse
from concurrent.futures import ThreadPoolExecutor

def call_hyp(command_name, endpoint_name):
    command = [
        "hyp", "invoke", shlex.quote(command_name),
        "--endpoint-name", shlex.quote(endpoint_name),
        "--body", '{"messages":[{"role":"system","content":"You are a helpful AI assistant that can answer questions and provide information. You must include your reasoning activities."}, {"role": "user", "content": "What is the capital of USA?"}], "temperature": 0.1, "top_p": 0.95, "max_tokens": 512}'
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout


def run_parallel_calls(command_name, endpoint_name, executions_per_second=5, duration_seconds=10):
    interval = 1.0 / executions_per_second
    with ThreadPoolExecutor(max_workers=executions_per_second) as executor:
        futures = []
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            futures.append(executor.submit(call_hyp, command_name, endpoint_name))
            time.sleep(interval)
        for future in futures:
            print(future.result())


def main():
    parser = argparse.ArgumentParser(description="Parallel hyp invoke tester")
    parser.add_argument("--command", required=True, help="Command name passed to 'hyp invoke'")
    parser.add_argument("--endpoint", required=True, help="Endpoint name for --endpoint-name")
    parser.add_argument("--eps", type=int, default=5, help="Executions per second")
    parser.add_argument("--duration", type=int, default=20, help="Duration in seconds")
    args = parser.parse_args()

    run_parallel_calls(
        command_name=args.command,
        endpoint_name=args.endpoint,
        executions_per_second=args.eps,
        duration_seconds=args.duration
    )


if __name__ == "__main__":
    main()
