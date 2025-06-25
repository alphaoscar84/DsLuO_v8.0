import pandas as pd
from itertools import combinations
import sys
import time
import os

# === Settings ===
file_path = "players_Cs3drziI.csv"  # Update path if needed
SALARY_CAP = 100000
TOP_N_TEAMS = 100
PROGRESS_UPDATE_INTERVAL = 5000  # Progress print frequency

# === Load and Prepare Data ===
df = pd.read_csv(file_path)
df = df[df['Playing Status'] == 'CONFIRMED IN TEAM TO PLAY'].copy()
df['AvgScore'] = df[['FPPG', 'Form']].mean(axis=1)

def assign_ids(group, prefix):
    group = group.sort_values(by='AvgScore', ascending=False).reset_index(drop=True)
    group['ID'] = [f"{prefix}{i+1}" for i in range(len(group))]
    return group

defs = assign_ids(df[df['Position'] == 'DEF'], 'D')
mids = assign_ids(df[df['Position'] == 'MID'], 'M')
fwds = assign_ids(df[df['Position'] == 'FWD'], 'F')
rucks = assign_ids(df[df['Position'] == 'RK'], 'R')

# === Generate combinations ===
def_indices = list(combinations(defs.index, 2))
mid_indices = list(combinations(mids.index, 4))
fwd_indices = list(combinations(fwds.index, 2))
ruck_indices = list(combinations(rucks.index, 1))

total_combos = len(def_indices) * len(mid_indices) * len(fwd_indices) * len(ruck_indices)
valid_teams = []

start_time = time.time()
count = 0

# === Main Loop with pruning and progress bar ===
for d in def_indices:
    defs_selected = defs.loc[list(d)]
    def_salary = defs_selected['Salary'].sum()

    for m in mid_indices:
        mids_selected = mids.loc[list(m)]
        mid_salary = mids_selected['Salary'].sum()

        # Prune early if DEF + MID already over budget
        if def_salary + mid_salary > SALARY_CAP:
            continue

        for f in fwd_indices:
            fwds_selected = fwds.loc[list(f)]
            fwd_salary = fwds_selected['Salary'].sum()

            if def_salary + mid_salary + fwd_salary > SALARY_CAP:
                continue

            for r in ruck_indices:
                count += 1

                if count % PROGRESS_UPDATE_INTERVAL == 0 or count == total_combos:
                    elapsed = time.time() - start_time
                    percent = count / total_combos
                    eta = (elapsed / percent) - elapsed if percent > 0 else 0
                    mins, secs = divmod(eta, 60)
                    sys.stdout.write(f"\rProgress: {percent*100:.2f}% | ETA: {int(mins)}m {int(secs)}s")
                    sys.stdout.flush()

                rucks_selected = rucks.loc[list(r)]
                total_salary = def_salary + mid_salary + fwd_salary + rucks_selected['Salary'].sum()

                if total_salary > SALARY_CAP:
                    continue

                team = pd.concat([defs_selected, mids_selected, fwds_selected, rucks_selected])

                if team['Name'].duplicated().any():
                    continue

                total_score = team['Score'].sum()
                total_avg = team['AvgScore'].sum()

                team_ids = list(team['ID'])
                valid_teams.append((total_score, total_avg, total_salary, team_ids))

# Sort by actual total score and export top N
valid_teams.sort(reverse=True, key=lambda x: x[0])
top_teams = valid_teams[:TOP_N_TEAMS]

# === Export CSV ===
rows = []
for idx, (score, avg, salary, ids) in enumerate(top_teams, 1):
    rows.append({
        'Rank': idx,
        'Total Score': score,
        'Total AvgScore': avg,
        'Total Salary': salary,
        'Players': ', '.join(ids)
    })

output_df = pd.DataFrame(rows)
output_path = os.path.join(os.getcwd(), '/home/AlphaOscar/LCv6/top_teams_nth_car.csv')
output_df.to_csv(output_path, index=False)

# Completion time
end_time = time.time()
duration = end_time - start_time
hrs, rem = divmod(duration, 3600)
mins, secs = divmod(rem, 60)
print(f"\n\n✅ Exported to: {output_path}")
print(f"⏱️ Completed in {int(hrs)}h {int(mins)}m {int(secs)}s")
