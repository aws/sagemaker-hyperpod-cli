import json
import re
import textwrap
import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer
from datasets import load_dataset, Dataset, DatasetDict

def extract_think_content(text):
    match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_tool_call_content(text):
    match = re.search(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_tool_call_response(text):
    match = re.search(r"<tool_response>(.*?)</tool_response>", text, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_content_parts(text):
    think_content = extract_think_content(text)
    tool_call_content = extract_tool_call_content(text)

    # Remove both tags and their content to get the rest
    rest_content = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    rest_content = re.sub(
        r"<tool_call>.*?</tool_call>", "", rest_content, flags=re.DOTALL
    )
    rest_content = rest_content.strip() if rest_content.strip() else None

    return think_content, tool_call_content, rest_content


def remove_empty_think_tags(text):
    return re.sub(r"<think>\s*</think>", "", text)


def validate_messages(conversations):
    has_tool_call = False
    for message in conversations:
        if message["from"] == "gpt":
            tool_call_content = extract_tool_call_content(message["value"])
            if tool_call_content:
                try:
                    for line in tool_call_content.strip().split("\n"):
                        if line.strip():
                            json.loads(line.strip())
                    has_tool_call = True
                except json.JSONDecodeError:
                    return False
            else:
                has_tool_call = False
        elif message["from"] == "tool":
            if not has_tool_call:
                return False
    return True

def prepare_dataset(sample, tokenizer):

    if not validate_messages(sample["conversations"]):
        return {"text": None}

    messages = []

    system_text = f"""
    You are a deep thinking AI, you may use extremely long chains of thought to deeply consider the problem and deliberate with yourself via systematic reasoning processes to help come to a correct solution prior to answering.
    You should enclose your thoughts and internal monologue inside <think> </think> tags, and then provide your solution or response to the problem.
    You are a function calling AI model. You are provided with function signatures within <tools> </tools> XML tags. You may call one or more functions to assist with the user query.
    If available tools are not relevant in assisting with user query, just respond in natural conversational language. Don't make assumptions about what values to plug into functions.
    After calling & executing the functions, you will be provided with function results within <tool_response> </tool_response> XML tags.
    <tools>"
    {json.loads(sample["tools"])},
    </tools>
    """

    system_text = textwrap.dedent(system_text).strip()

    messages.append({"role": "system", "content": system_text})

    for message in sample["conversations"]:
        if message["from"] == "human":
            messages.append({"role": "user", "content": message["value"]})
        elif message["from"] == "gpt":
            think_content, tool_call_content, rest_content = extract_content_parts(
                message["value"]
            )

            assistant_msg = {
                "role": "assistant",
                "content": "",  # Always provide content field
            }

            if think_content:
                assistant_msg["reasoning_content"] = think_content

            if tool_call_content:
                assistant_msg["tool_calls"] = [
                    {
                        "type": "function",
                        "function": json.loads(tool_call_content),
                    }
                ]

            if rest_content:
                assistant_msg["content"] = rest_content

            messages.append(assistant_msg)
        elif message["from"] == "tool":
            tool_response_text = extract_tool_call_response(message["value"])
            # Handle the case where it's a string representation of a dict
            if tool_response_text.startswith("{'") and tool_response_text.endswith(
                "'}"
            ):
                # Convert Python dict string to JSON
                tool_response_text = tool_response_text.replace("'", '"')

            try:
                tool = json.loads(tool_response_text)
                content = tool.get(
                    "result", tool_response_text
                )  # Use result if available, otherwise raw text
            except:
                content = tool_response_text  # Use raw text if JSON parsing fails

            messages.append({"role": "tool", "content": str(content)})

    if messages[-1]["role"] != "assistant":
        messages = messages[:-1]

    sample["text"] = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        enable_thinking=True,
    )

    return sample


if __name__ == "__main__":
    print("[INFO] Loading dataset…")
    model_id = "Qwen/Qwen3-4B-Thinking-2507"
    dataset_id = "interstellarninja/hermes_reasoning_tool_use"

    dataset = load_dataset(dataset_id, split="train")
    print(f"[INFO] Dataset loaded. Total samples: {len(dataset)}")

    print("[INFO] Converting to DataFrame…")
    df = pd.DataFrame(dataset)

    print("[INFO] Splitting into train/validation sets…")
    train, val = train_test_split(df, test_size=0.1, random_state=42)
    print(f"[INFO] Train samples: {len(train)}, Val samples: {len(val)}")

    print("[INFO] Creating HuggingFace Dataset objects…")
    train_dataset = Dataset.from_pandas(train)
    val_dataset = Dataset.from_pandas(val)

    print("[INFO] Loading tokenizer…")
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    dataset = DatasetDict({"train": train_dataset, "val": val_dataset})

    print("[INFO] Preparing train dataset…")
    prepared_train_dataset = (
        dataset["train"]
        .map(lambda x: prepare_dataset(x, tokenizer),
             remove_columns=list(train_dataset.features))
        .filter(lambda x: x["text"] is not None)
    )
    print(f"[INFO] Prepared train dataset size: {len(prepared_train_dataset)}")

    print("[INFO] Preparing validation dataset…")
    prepared_val_dataset = (
        dataset["val"]
        .map(lambda x: prepare_dataset(x, tokenizer),
             remove_columns=list(val_dataset.features))
        .filter(lambda x: x["text"] is not None)
    )
    print(f"[INFO] Prepared val dataset size: {len(prepared_val_dataset)}")

    print("[INFO] Saving datasets to JSON…")
    prepared_train_dataset.to_json("./data/train/dataset.json", orient="records")
    prepared_val_dataset.to_json("./data/val/dataset.json", orient="records")
    print("[INFO] All done!")