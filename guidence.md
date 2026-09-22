---

# Title: **Simulated Strategy-Based Task Scheduling and Resource Limitation System (AI-Assisted Refactoring)**

- Estimated time to complete with AI assistance: 30 minutes
- You are free to use any **AI tools** (such as ChatGPT, Claude, Cursor, etc.) during the task.

---

### Description:

- You are going to develop a backend service responsible for receiving user-submitted **task strategies**, executing them daily, and limiting each user’s resource quota.
- Below is an initial version of code left by a previous engineer.
- Although it works, the structure is messy and difficult to extend.

```python
import datetime

users = {
 'alice': {'quota': 3, 'executed': 0},
 'bob': {'quota': 5, 'executed': 0}
}

tasks = [
 {'user': 'alice', 'time': '12:00', 'action': 'sync', 'target': '/data/x'},
 {'user': 'bob', 'time': '12:00', 'action': 'backup', 'target': '/srv/y'},
 {'user': 'alice', 'time': '12:00', 'action': 'delete', 'target': '/tmp/z'},
]

def run():
 now = datetime.datetime.now().strftime('%H:%M')
 for task in tasks:
     if task['time'] == now:
         user = task['user']
         if users[user]['executed'] >= users[user]['quota']:
             print(f"{user} has exceeded quota.")
             continue
         print(f"Executing {task['action']} on {task['target']} for {user}")
         users[user]['executed'] += 1
```

---

### Refactoring Goals:

#### 1. Refactor into class-based / modular design, including:

- User management & quota control module
- Task data model
- Task executor (extensible)
- Scheduling system (simple implementation is fine)

#### 2. Support the following requirements:

- A single user can have multiple tasks simultaneously
- Task parameters should be configurable (e.g., via dictionary input)
- Task execution must include logging (use logging module)

#### 3. Optional extensions (if time allows):

- Support different action strategies (OOP design)
- Rewrite as an async execution version (optional)

---

### Constraints:

- The goal of refactoring is to demonstrate your **AI-assisted system design and refactoring ability**
- You may refer to AI suggestions, but must carefully evaluate and verify correctness

---

### Possible Follow-up Questions (Interview Guidance):

- How did you design your prompts to guide AI for refactoring?
- Did you reject any AI-generated suggestions? Why?
- If this system needs to handle tens of thousands of tasks daily, how would you scale the architecture?
- Which parts would you extract into reusable modules for other teams?

---

### Evaluation Criteria:

| Category | Evaluation Focus |
| --- | --- |
| Module & Logic Design | Proper separation of logic and responsibilities |
| Maintainability | Easy to extend, clear naming, structured flow |
| AI Tool Usage | Effectively guides AI instead of blindly relying on it |
| Error Handling & Logging | Uses logging, clear and traceable error messages |

---

### Additional Evaluation Notes:

- Ability to integrate AI-generated code into an existing system
- Prompt accuracy and whether it solves real problems

---

### Expected Performance:

- **Senior level**:
    - 10 minutes → architecture design
    - 20 minutes → modular implementation + testing
- **Junior level**:
    - ~30 minutes → may only complete Refactoring Goal 1