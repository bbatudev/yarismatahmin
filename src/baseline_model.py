import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
import os

# Set up paths
DATA_DIR = '../data/raw'
# Using Men's data for the baseline
SEEDS_FILE = os.path.join(DATA_DIR, 'MNCAATourneySeeds.csv')
COMPACT_RESULTS_FILE = os.path.join(DATA_DIR, 'MRegularSeasonCompactResults.csv')
TOURNEY_RESULTS_FILE = os.path.join(DATA_DIR, 'MNCAATourneyCompactResults.csv')

def load_data():
    seeds = pd.read_csv(SEEDS_FILE)
    reg_results = pd.read_csv(COMPACT_RESULTS_FILE)
    tourney_results = pd.read_csv(TOURNEY_RESULTS_FILE)
    return seeds, reg_results, tourney_results

def process_seeds(seeds):
    # Extract integer seed from strings like 'W01', 'X02a'
    seeds['SeedInt'] = seeds['Seed'].apply(lambda x: int(x[1:3]))
    return seeds

def process_regular_season(reg_results):
    # Calculate win rate for each team per season
    wins = reg_results.groupby(['Season', 'WTeamID']).size().reset_index(name='Wins')
    losses = reg_results.groupby(['Season', 'LTeamID']).size().reset_index(name='Losses')
    
    wins = wins.rename(columns={'WTeamID': 'TeamID'})
    losses = losses.rename(columns={'LTeamID': 'TeamID'})
    
    win_stats = pd.merge(wins, losses, on=['Season', 'TeamID'], how='outer').fillna(0)
    win_stats['TotalGames'] = win_stats['Wins'] + win_stats['Losses']
    win_stats['WinRate'] = win_stats['Wins'] / win_stats['TotalGames']
    
    return win_stats

def create_training_data(tourney_results, seeds, win_stats):
    # Prepare training dataframe
    df = tourney_results.copy()
    
    # We want to randomly swap WTeamID and LTeamID so our model doesn't just learn "Team 1 always wins"
    # because the target is always 1 in the raw data.
    # Convention: predict probability that Team 1 beats Team 2
    # Ensure Team1ID < Team2ID to be consistent with submission format
    
    df['Team1ID'] = np.minimum(df['WTeamID'], df['LTeamID'])
    df['Team2ID'] = np.maximum(df['WTeamID'], df['LTeamID'])
    df['Target'] = (df['WTeamID'] == df['Team1ID']).astype(int)
    
    # Merge seeds
    df = pd.merge(df, seeds[['Season', 'TeamID', 'SeedInt']], left_on=['Season', 'Team1ID'], right_on=['Season', 'TeamID'], how='left').rename(columns={'SeedInt': 'T1_Seed'})
    df = df.drop('TeamID', axis=1)
    df = pd.merge(df, seeds[['Season', 'TeamID', 'SeedInt']], left_on=['Season', 'Team2ID'], right_on=['Season', 'TeamID'], how='left').rename(columns={'SeedInt': 'T2_Seed'})
    df = df.drop('TeamID', axis=1)
    
    # Calculate Seed Diff
    df['SeedDiff'] = df['T1_Seed'] - df['T2_Seed']
    
    # Merge Win Rates
    df = pd.merge(df, win_stats[['Season', 'TeamID', 'WinRate']], left_on=['Season', 'Team1ID'], right_on=['Season', 'TeamID'], how='left').rename(columns={'WinRate': 'T1_WinRate'})
    df = df.drop('TeamID', axis=1)
    df = pd.merge(df, win_stats[['Season', 'TeamID', 'WinRate']], left_on=['Season', 'Team2ID'], right_on=['Season', 'TeamID'], how='left').rename(columns={'WinRate': 'T2_WinRate'})
    df = df.drop('TeamID', axis=1)
    
    # Calculate Win Rate Diff
    df['WinRateDiff'] = df['T1_WinRate'] - df['T2_WinRate']
    
    # Drop NaNs just in case
    df = df.dropna()
    
    features = ['SeedDiff', 'WinRateDiff']
    return df, features

def main():
    print("Loading data...")
    seeds, reg_results, tourney_results = load_data()
    
    print("Processing features...")
    seeds = process_seeds(seeds)
    win_stats = process_regular_season(reg_results)
    
    df, features = create_training_data(tourney_results, seeds, win_stats)
    
    print(f"Training data shape: {df.shape}")
    
    # Cross Validation (Time Series Split)
    # We will use seasons before 2021 as training, and 2021 onwards for validation
    
    train_df = df[df['Season'] < 2021]
    val_df = df[df['Season'] >= 2021]
    
    X_train = train_df[features]
    y_train = train_df['Target']
    X_val = val_df[features]
    y_val = val_df['Target']
    
    print("Training Logistic Regression...")
    model = LogisticRegression()
    model.fit(X_train, y_train)
    
    print("Evaluating...")
    val_preds = model.predict_proba(X_val)[:, 1]
    brier_score = brier_score_loss(y_val, val_preds)
    
    print(f"Validation Brier Score (2021-2024 seasons): {brier_score:.5f}")

if __name__ == "__main__":
    main()
