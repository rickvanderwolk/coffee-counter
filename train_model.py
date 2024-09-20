import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

data = pd.read_csv('power_log.csv')

data = data[data['coffee_brewed'] != 'undefined']

data['coffee_brewed'] = data['coffee_brewed'].map({'yes': 1, 'no': 0})

data['mean_last_15'] = data['power'].rolling(window=15).mean()
data['max_last_15'] = data['power'].rolling(window=15).max()
data['min_last_15'] = data['power'].rolling(window=15).min()

data = data.dropna()

X = data[['power', 'mean_last_15', 'max_last_15', 'min_last_15']]
y = data['coffee_brewed']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

joblib.dump(model, 'coffee_model.pkl')
print("Trained model has been saved as 'coffee_model.pkl'.")
