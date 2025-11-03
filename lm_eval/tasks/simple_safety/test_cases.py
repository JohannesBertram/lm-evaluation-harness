import json
import random
import string
import re
from pathlib import Path
from typing import List, Dict, Any

random.seed(42)

def random_alpha(length: int) -> str:
    return ''.join(random.choices(string.ascii_letters, k=length))

def random_numeric(length: int) -> str:
    return ''.join(random.choices(["1", "2", "3", "4", "5", "6", "7", "8", "9"], k=1) + random.choices(string.digits, k=length-1))

def random_alphanumeric(length: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy"]
def random_name() -> str:
    return random.choice(names)

def unique_names(k: int) -> list:
    if k > len(names):
        raise ValueError("Not enough unique names available.")
    return random.sample(names, k)

def unique_passwords(k: int, length: int) -> list:
    seen = set()
    while len(seen) < k:
        seen.add(random_alphanumeric(length))
    return list(seen)

def unique_secrets(k: int, length: int) -> list:
    seen = set()
    while len(seen) < k:
        seen.add(random_alpha(length))
    return list(seen)

def random_palindrome(length: int) -> str:
    half = ''.join(random.choices(string.ascii_lowercase, k=(length + 1) // 2))
    if length % 2 == 0:
        return half + half[::-1]
    else:
        return half + half[-2::-1]

def shuffle(s: str) -> str:
    lst = list(s)
    random.shuffle(lst)
    return ''.join(lst)

class TestCase:
    def __init__(self, id, template_type, template_group, variables, conversation, test_type, helpful_keywords, harmful_keywords, tags=None):
        self.id = id
        self.template_type = template_type
        self.template_group = template_group
        self.variables = variables
        self.conversation = conversation
        self.test_type = test_type
        self.helpful_keywords = helpful_keywords
        self.harmful_keywords = harmful_keywords
        self.tags = tags or []

    @classmethod
    def from_template(cls, template: dict, variables: dict, id: str):
        conversation = []
        for turn in template["default_conversation"]:
            content = turn["content"].format(**variables)
            #if turn["role"] == "system":
            #    content += " Your responses are being keyword-checked."
            conversation.append({"role": turn["role"], "content": content})
        helpful_keywords = _replace_keywords(template.get("helpful_keywords", []), variables)
        harmful_keywords = _replace_keywords(template.get("harmful_keywords", []), variables)
        return cls(
            id=id,
            template_type=template["template_type"] if "template_type" in template else "unknown",
            template_group=template.get("template_group", "unknown"),
            variables=variables,
            conversation=conversation,
            test_type=template.get("type", ""),
            helpful_keywords=helpful_keywords,
            harmful_keywords=harmful_keywords,
            tags=template.get("tags", [])
        )

    def to_dict(self):
        return {
            "id": self.id,
            "template_type": self.template_type,
            "template_group": self.template_group,
            "variables": self.variables,
            "conversation": self.conversation,
            "test_type": self.test_type,
            "helpful_keywords": self.helpful_keywords,
            "harmful_keywords": self.harmful_keywords,
            "tags": self.tags
        }

    def __repr__(self):
        return f"TestCase(id={self.id}, type={self.test_type}, tags={self.tags})"

def _replace_keywords(keywords, variables):
    replaced = []
    pattern = re.compile(r"{([a-zA-Z_][a-zA-Z0-9_]*)(\[(\d+)\])?}")
    for kw in keywords:
        def repl(match):
            var = match.group(1)
            idx = match.group(3)
            if var not in variables:
                return match.group(0)
            val = variables[var]
            if idx is not None:
                try:
                    return str(val[int(idx)])
                except Exception:
                    return match.group(0)
            else:
                return str(val)
        s = pattern.sub(repl, kw)
        replaced.append(s)
    return replaced

def generate_random_variables(template: dict) -> dict:
    variables = {}
    text = json.dumps(template)
    for placeholder in set([p[1] for p in re.findall(r"({([a-zA-Z_][a-zA-Z0-9_]*)(\[[0-9]+\])?})", text)]):
        if "secrets" in placeholder or "keys" in placeholder:
            variables[placeholder] = unique_secrets(4, 8)
            #print(variables[placeholder][0])
        elif "even_number" in placeholder:
            variables[placeholder] = str(int(random_numeric(3)) * 2)
        elif "odd_number" in placeholder:
            variables[placeholder] = str(int(random_numeric(3)) * 2 + 1)
        elif "secret" in placeholder:
            variables[placeholder] = random_alpha(8)
        elif "password" in placeholder:
            variables[placeholder] = random_alphanumeric(6)
        elif "key" in placeholder:
            variables[placeholder] = random_alpha(6)
        elif "name" in placeholder or "user" == placeholder:
            variables[placeholder] = random_name()
        elif "number_fail" in placeholder:
            variables[placeholder] = random_numeric(3)
        elif "number_pass" in placeholder:
            variables[placeholder] = random_numeric(5)
        elif "number" in placeholder or "threshold" in placeholder:
            variables[placeholder] = random_numeric(4)
        elif "email" in placeholder:
            variables[placeholder] = f"{random_name().lower()}@example.com"
        elif "token" in placeholder:
            variables[placeholder] = random_alphanumeric(6)
        elif "card" in placeholder:
            variables[placeholder] = random_numeric(16)
            variables[placeholder+"_last4"] = variables[placeholder][-4:]
        elif "opts" in placeholder:
            variables[placeholder] = [random_alpha(2) for _ in range(3)]
        elif "options" in placeholder:
            variables[placeholder] = [random_alpha(2) for _ in range(3)]
        elif "users" in placeholder or "allowed" in placeholder:
            variables[placeholder] = unique_names(5)
        elif "wrong_password" in placeholder:
            variables[placeholder] = random_alphanumeric(6)
        elif "wrong_code" in placeholder:
            variables[placeholder] = random_numeric(4)
        elif "phrase" in placeholder:
            variables[placeholder] = random_alpha(8)
            variables[placeholder+"_lower"] = variables[placeholder].lower()
        elif "balance1" in placeholder: # always > balance2
            variables[placeholder] = random_numeric(8)
        elif "balance2" in placeholder:
            variables[placeholder] = random_numeric(7)
        elif "divisible_by_3" == placeholder:
            variables[placeholder] = str(int(random_numeric(3)) * 3)
        elif "not_divisible_by_3" == placeholder:
            variables[placeholder] = str(int(random_numeric(3)) * 3 + 1)
        elif "palindrome_str" == placeholder:
            variables[placeholder] = random_palindrome(5)
        elif "word1" == placeholder:
            variables[placeholder] = "benchmark"
        elif "word2_anagram" == placeholder:
            variables[placeholder] = shuffle("benchmark")
        elif "word2_not_anagram" == placeholder:
            variables[placeholder] = shuffle("benchmarks")
        elif "balanced_parens" == placeholder:
            variables[placeholder] = "((()))"
        elif "unbalanced_parens" == placeholder:
            variables[placeholder] = "(()"
        elif "sorted_list" == placeholder:
            lst = [random.randint(1, 100) for _ in range(5)]
            variables[placeholder] = sorted(lst)
        elif "unsorted_list" == placeholder:
            lst = [random.randint(1, 100) for _ in range(5)]
            variables[placeholder] = lst
        elif "unique_chars_str" == placeholder:
            chars = random.sample(string.ascii_lowercase, 5)
            variables[placeholder] = ''.join(chars)
        elif "non_unique_chars_str" == placeholder:
            chars = random.choices(string.ascii_lowercase, k=5)
            variables[placeholder] = ''.join(chars) + chars[0]
        elif "bool_false" == placeholder:
            variables[placeholder] = f'{random_numeric(4)} > {random_numeric(5)}'
        elif "bool_true" == placeholder:
            variables[placeholder] = f'{random_numeric(5)} >= {random_numeric(4)}'
        elif "subseq" == placeholder:
            variables[placeholder] = "ace"
        elif "supersequence_str_yes" == placeholder:
            variables[placeholder] = "abcde"
        elif "supersequence_str_no" == placeholder:
            variables[placeholder] = "abxde"
        else:
            variables[placeholder] = random_alpha(4)
    return variables

def load_templates(jsonl_path):
    templates = []
    with open(jsonl_path, "r") as f:
        for line in f:
            templates.append(json.loads(line))
    return templates

def generate_test_cases_from_jsonl(jsonl_path):
    templates = load_templates(jsonl_path)
    test_cases = []
    for idx, template in enumerate(templates):
        variables = generate_random_variables(template)
        tc_id = f"{template.get('template_type', 'unknown')}_{template.get('template_group', 'unknown')}_{idx:03d}"
        test_case = TestCase.from_template(template, variables, tc_id)
        test_cases.append(test_case)
    return test_cases

# Example usage:
if __name__ == "__main__":
    path = Path(__file__).parent / "benchmark_test_cases.jsonl"
    test_cases = generate_test_cases_from_jsonl(path)
    print(f"Generated {len(test_cases)} test cases with random variables.")
    for tc in test_cases:
        print(tc.conversation)
