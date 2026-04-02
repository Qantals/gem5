import pandas as pd
import numpy as np
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def load_data(csv_path):
    df = pd.read_csv(csv_path)

    feature_cols = [
        "freq_cpu",
        "freq_gpu",
    ]

    X = df[feature_cols].values
    y = df["ms"].values

    return X, y, feature_cols


def build_model(degree=2):
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("poly", PolynomialFeatures(degree=degree, include_bias=False)),
            ("reg", Ridge()),
        ]
    )
    return model


def train_model(model, X_train, y_train):
    param_grid = {"reg__alpha": [0.01, 0.1, 1, 10, 100]}

    grid = GridSearchCV(
        model, param_grid, cv=5, scoring="neg_mean_squared_error", n_jobs=-1
    )

    grid.fit(X_train, y_train)

    return grid


def evaluate(model, X_test, y_test):
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n===== Evaluation Results =====")
    print(f"MAE  : {mae:.6f}")
    print(f"RMSE : {rmse:.6f}")
    print(f"R2   : {r2:.6f}")

    return y_pred


def print_coefficients(model, feature_names):
    poly = model.named_steps["poly"]
    reg = model.named_steps["reg"]

    poly_feature_names = poly.get_feature_names_out(feature_names)
    coefficients = reg.coef_

    print("\n===== Model Coefficients =====")
    for name, coef in sorted(
        zip(poly_feature_names, coefficients),
        key=lambda x: abs(x[1]),
        reverse=True,
    ):
        print(f"{name:25s} {coef:.6f}")

    print(f"\nIntercept: {reg.intercept_:.6f}")


def main():

    csv_path = Path("m5out_movFreqFixLat/results.csv")
    degree = 4
    save_model = csv_path.parent / "freq_all.pkl"

    print("Loading data...")
    X, y, feature_names = load_data(csv_path)

    print(f"Total samples: {len(X)}")
    print(f"Number of features: {len(feature_names)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = build_model(degree=degree)

    print("Training model with cross-validation...")
    grid = train_model(model, X_train, y_train)

    best_model = grid.best_estimator_

    print(f"\nBest alpha: {grid.best_params_['reg__alpha']}")

    evaluate(best_model, X_test, y_test)

    # print_coefficients(best_model, feature_names)

    if save_model:
        joblib.dump(best_model, save_model)
        print(f"\nModel saved to {save_model}")

        model = joblib.load(save_model)
        sample = np.array([[2.5, 1.0]])
        prediction = model.predict(sample)
        print("Predicted time cost (ms):", prediction[0])


if __name__ == "__main__":
    main()
