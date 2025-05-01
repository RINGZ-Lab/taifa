import csv
import os
import logging

logger = logging.getLogger(__name__)

def calculate_absolute_difference(ordered_list, expert_list):
    logger.debug(f"Calculating difference between user list: {ordered_list} and expert list: {expert_list}")
    differences = []
    for item in ordered_list:
        user_pos = ordered_list.index(item)
        expert_pos = expert_list.index(item)
        diff = abs(user_pos - expert_pos)
        differences.append(diff)
        logger.debug(f"Item: {item}, User pos: {user_pos}, Expert pos: {expert_pos}, Diff: {diff}")
    
    absolute_number = sum(differences)
    logger.debug(f"Total absolute difference: {absolute_number}")
    return absolute_number


def save_csv(channel_name, participants, task_file, absolute_difference,score, csv_file='evaluation_results.csv'):
    fieldnames = ['channel_name', 'participants', 'task_file', 'absolute_difference','score']
    logger.debug(f"Saving evaluation to {csv_file}"
                 f" with data: channel_name={channel_name},"
                 f" participants={participants}, task_file={task_file},"
                 f" absolute_difference={absolute_difference}")
    write_header = not os.path.exists(csv_file)

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        writer.writerow({
            'channel_name': channel_name,
            'participants': ', '.join(participants),
            'task_file': task_file,
            'absolute_difference': absolute_difference,
            'score':score
        })

def calculate_score(absolute_number, n=7):
    max_difference = sum(abs(i - (n-1-i)) for i in range(n))
    logger.debug(f"Max possible difference for {n} items: {max_difference}")
    absolute_number = min(max(absolute_number, 0), max_difference)
    score = 100 * (1 - (absolute_number / max_difference))
    score = max(0, min(score, 100))
    logger.debug(f"Final calculated score: {score}")
    return round(score, 2)