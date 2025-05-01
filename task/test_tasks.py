import json
"""
check each file in the task folder and compare it with the expert_solution.json file
"""
with open("./task3/task.json", "r") as file:
    task_json = json.load(file)
with open("./task3/expert_solution.json", "r") as file:
    expert_solution_json = json.load(file)
salvaged_items = [item["item"] for item in task_json["sections"][1]["content"]]
expert_ranking = expert_solution_json["expert_ranking"]
missing_items = [item for item in salvaged_items if item not in expert_ranking]

if missing_items:
    print("The following items missing in the expert file:")
    for item in missing_items:
        print(f"- {item}")
else:
    print("All items present in the expert file.")