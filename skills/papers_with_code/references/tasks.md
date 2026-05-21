# Tasks & Benchmarks Functions

Detailed argument specifications, output schemas, and usage for
`search_tasks`, `get_task`, and `get_task_leaderboard`.

## 1. `search_tasks` — Search ML tasks

Searches the Papers With Code task taxonomy for tasks matching a query. Tasks
represent ML problem areas like "Image Classification", "Machine Translation",
or "Object Detection".

```bash
uv run scripts/pwc_api.py ./tasks.json search_tasks "image classification" --limit 5
```

**Arguments:**

-   `query` (str, required) – free-text search query for tasks
-   `limit` (int, default 50) – maximum results to return

**Output:** A dict with pagination and `results` list:

```
{
  "count": 10,
  "results": [
    {
      "id": "image-classification",
      "name": "Image Classification",
      "description": "Assigning a label or category to an image...",
      "image": "https://paperswithcode.com/media/tasks/image-classification.png",
      "task_category": "Computer Vision",
      "is_competition": false,
      "source_dataset": {"id": "imagenet", "name": "ImageNet"}
    }
  ]
}
```

**Extracting task IDs for chaining:**
```bash
cat ./tasks.json | jq -r '.results[].id'
```

---

## 2. `get_task` — Get task details

Retrieves detailed information about a specific ML task, including its
description, associated papers, and reference to the SOTA leaderboard.

```bash
uv run scripts/pwc_api.py ./task.json get_task "image-classification"
```

**Arguments:**

-   `task_id` (str, required) – task slug (e.g. `image-classification`)

**Output:** A dict with task details:

```
{
  "id": "image-classification",
  "name": "Image Classification",
  "description": "Assigning a label or category to an image...",
  "image": "https://paperswithcode.com/media/tasks/image-classification.png",
  "task_category": "Computer Vision",
  "is_competition": false,
  "source_dataset": {"id": "imagenet", "name": "ImageNet"},
  "papers": [
    {"id": "deep-residual-learning-for-image-recognition", "title": "Deep Residual Learning..."},
    ...
  ]
}
```

**Chaining to get the leaderboard:**
```bash
uv run scripts/pwc_api.py ./task.json get_task "image-classification"
TASK_ID=$(cat ./task.json | jq -r '.id')
uv run scripts/pwc_api.py ./leaderboard.json get_task_leaderboard "$TASK_ID"
```

---

## 3. `get_task_leaderboard` — Get SOTA leaderboard for a task

Retrieves the state-of-the-art leaderboard for a given task. Results are
ordered by rank (best first) and include the model name, paper, dataset used,
and reported metrics.

```bash
uv run scripts/pwc_api.py ./leaderboard.json get_task_leaderboard "image-classification"
```

**Arguments:**

-   `task_id` (str, required) – task slug

**Output:** A dict with `count` and `results`:

```
{
  "count": 50,
  "results": [
    {
      "rank": 1,
      "model": "SomeModel-v2",
      "paper": {
        "id": "some-paper-slug",
        "title": "Some Paper Title"
      },
      "dataset": {
        "id": "imagenet",
        "name": "ImageNet"
      },
      "metrics": [
        {"name": "Top 1 Accuracy", "value": "91.8"}
      ],
      "task": {"id": "image-classification", "name": "Image Classification"},
      "url": "https://paperswithcode.com/sota/image-classification-on-imagenet"
    },
    ...
  ]
}
```

**Slimming to top results:**
```bash
cat ./leaderboard.json | jq '[.results[:5] | .[] | {rank, model, dataset: .dataset.name, metric: .metrics[0].value}]'
```

**Getting the best metric from the top result:**
```bash
cat ./leaderboard.json | jq '.results[0] | {model, dataset: .dataset.name, metric: .metrics[0]}'
```
