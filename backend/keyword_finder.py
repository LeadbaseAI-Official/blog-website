import requests
import csv

def get_suggestions(phrase):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&hl=en&q={phrase}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()[1]
    except requests.exceptions.RequestException:
        return []

def get_expanded_suggestions(initial_phrase):
    all_suggestions = set()
    initial_suggestions = get_suggestions(initial_phrase)
    all_suggestions.update(initial_suggestions)
    for suggestion in initial_suggestions:
        further_suggestions = get_suggestions(suggestion)
        all_suggestions.update(further_suggestions)
    return list(all_suggestions)


if __name__ == "__main__":
    phrases_to_process = []
    try:
        with open('phrase.csv', mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            for row in reader:
                if row: # Ensure row is not empty
                    phrases_to_process.append(row[0]) # Assuming phrase is in the first column
    except FileNotFoundError:
        print("Error: phrase.csv not found.")
        exit()
    except Exception as e:
        print(f"Error reading phrase.csv: {e}")
        exit()

    try:
        with open('kd.csv', mode='a', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            for phrase in phrases_to_process:
                print(f"Processing phrase: {phrase}")
                expanded_list = get_expanded_suggestions(phrase)
                for keyword in expanded_list:
                    writer.writerow([keyword])
        print("Keywords appended to kd.csv successfully.")
    except Exception as e:
        print(f"Error writing to kd.csv: {e}")
