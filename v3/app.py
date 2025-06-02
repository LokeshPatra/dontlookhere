from flask import Flask, jsonify, render_template, send_file
import pandas as pd
import random
import os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = 'scheme.csv'
LOG_FILE = 'winners_log.csv'

# Load and clean data
df = pd.read_csv(DATA_FILE)
data = df.to_dict('records')

seen = set()
unique_data = []
for entry in data:
    key = (entry['name'].strip().lower(), entry['urc'].strip().upper())
    if key not in seen:
        seen.add(key)
        unique_data.append({'name': entry['name'].strip(), 'urc': entry['urc'].strip().upper()})

# Final 3 winners (positions 43–45)
final_winners = [
    {'name': 'Suraj', 'urc': 'ABC001', 'prize': 'electric_scooter'},  # 3rd
    {'name': 'Shankar', 'urc': 'DEF002', 'prize': 'bike'},            # 2nd
    {'name': 'Biswa', 'urc': 'GHI003', 'prize': 'car'}                # 1st
]

# Assign prizes to first 42 entries
def assign_prizes(shuffled):
    prize_mapping = {
        range(0, 10): 'silver_coin',         # 45–36
        range(10, 18): 'dinner_set',         # 35–28
        range(18, 26): 'microwave',          # 27–20
        range(26, 32): 'washing_machine',    # 19–14
        range(32, 37): 'led_tv',             # 13–9
        range(37, 42): 'refrigerator',       # 8–4
    }
    for i, entry in enumerate(shuffled[:42]):
        for rng, prize_key in prize_mapping.items():
            if i in rng:
                entry['prize'] = prize_key
                break
    return shuffled[:42]

# Generate full draw sequence (first 42 + final 3)
def get_sequence():
    sequence = unique_data[:]
    random.shuffle(sequence)
    first_42 = assign_prizes(sequence)
    return first_42 + final_winners

full_sequence = get_sequence()
current_index = 0

@app.route('/')
def index():
    return render_template('index.html', total=len(full_sequence), year=datetime.now().year)  # ✅ Pass dynamic year

@app.route('/generate')
def generate():
    global current_index
    if current_index >= len(full_sequence):
        return jsonify({'status': 'done'})

    entry = full_sequence[current_index]
    prize_key = entry.get('prize', '')
    prize_name = prize_key.replace('_', ' ').title()
    count = current_index + 1
    current_index += 1

    with open(LOG_FILE, 'a') as f:
        f.write(f"{count},{entry['name']},{entry['urc']},{prize_name}\n")

    return jsonify({
        'status': 'ok',
        'name': entry['name'],
        'urc': entry['urc'],
        'index': count,
        'prize': prize_key
    })

@app.route('/previous')
def previous():
    global current_index
    if current_index <= 1:
        return jsonify({'status': 'error'})
    current_index -= 1
    entry = full_sequence[current_index - 1]
    return jsonify({
        'status': 'ok',
        'name': entry['name'],
        'urc': entry['urc'],
        'index': current_index,
        'prize': entry.get('prize', '')
    })

@app.route('/reset')
def reset():
    global current_index, full_sequence
    current_index = 0
    full_sequence = get_sequence()
    with open(LOG_FILE, 'w') as f:
        f.write("count,name,urc,prize\n")
    return jsonify({'status': 'ok'})

@app.route('/download')
def download():
    if os.path.exists(LOG_FILE):
        return send_file(LOG_FILE, as_attachment=True)
    return "No log file found.", 404

if __name__ == '__main__':
    app.run(debug=True)