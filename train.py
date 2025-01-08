import pandas as pd
import numpy as np
import regex as re
import datetime as dt

import matplotlib.pyplot as plt
import seaborn as sns

# Scikit-learn
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

import warnings
warnings.filterwarnings('ignore')


def count_outliers(df, features):
    outlier_counts = {}
    for feature in features:
        Q1 = df[feature].quantile(0.25)
        Q3 = df[feature].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = df[(df[feature] < lower_bound) | (df[feature] > upper_bound)]
        outlier_counts[feature] = outliers.shape[0]
    return outlier_counts

def generate_baseline_result(models, X, y, metric='neg_mean_squared_error', cv=5):
    kfold = KFold(n_splits=cv, shuffle=True, random_state=2024)
    results = []
    for model in models:
        model_name = model.__class__.__name__
        scores = cross_val_score(model, X, y, cv=kfold, scoring=metric)
        for fold_idx, score in enumerate(scores):
            results.append((model_name, fold_idx, -score))

    cv_results = pd.DataFrame(results, columns=['model_name', 'fold_id', 'score'])
    mean = cv_results.groupby('model_name')['score'].mean()
    std = cv_results.groupby('model_name')['score'].std()

    baseline_results = pd.concat([mean, std], axis=1, ignore_index=True)
    baseline_results.columns = ['Mean', 'Standard Deviation']
    baseline_results.sort_values(by='Mean', ascending=False, inplace=True)
    return baseline_results

def main():
    # Đọc file CSV (đã được lấy từ Snowflake)
    df = pd.read_csv("marketing_dataset.csv")

    # Thiết lập index (nếu cần)
    # Tuỳ thuộc vào dữ liệu thực tế của bạn. Ở đây giả sử cột "Campaign_ID" tồn tại.
    if "CAMPAIGN_ID" in df.columns:
        df = df.set_index("CAMPAIGN_ID")

    # Kiểm tra cột Duration, chuyển sang số
    if "DURATION" in df.columns:
        df['DURATION'] = df['DURATION'].str.extract(r'(\d+)', expand=False)
        df['DURATION'] = pd.to_numeric(df['DURATION'], errors='coerce')

    # Thống kê thông tin
    print(df.info())

    num_features = df.select_dtypes(include=np.number).columns.tolist()
    print(f"Numerical Features: {num_features}")
    cat_features = df.select_dtypes(exclude=np.number).columns.tolist()
    # Nếu cột 'Date' tồn tại, remove nó khỏi cat_features
    if "Date" in cat_features:
        cat_features.remove("Date")
    print(f"Categorical Features: {cat_features}")

    # Kiểm tra outliers
    print("Outliers:", count_outliers(df, num_features))

    # Feature Engineering: chuyển 'Date' thành datetime, tạo Quarter, Month
    df_copy = df.copy()
    if "DATE" in df_copy.columns:
        df_copy["DATE"] = pd.to_datetime(df_copy["DATE"])
        df_copy["QUARTER"] = df_copy["DATE"].dt.quarter.astype('object')
        df_copy["MONTH"] = df_copy["DATE"].dt.month.astype('object')

    # Thêm các feature CTR, CPC, CPM
    if "CLICKS" in df_copy.columns and "IMPRESSIONS" in df_copy.columns and "ACQUISITION_COST" in df_copy.columns:
        df_copy['CTR'] = round((df_copy['CLICKS'] / df_copy['IMPRESSIONS']) * 100, 2)
        df_copy['CPC'] = round(df_copy['ACQUISITION_COST'] / df_copy['CLICKS'], 2)
        df_copy['CPM'] = round((df_copy['ACQUISITION_COST'] * 1000) / df_copy['IMPRESSIONS'], 2)

    # Chuẩn bị X, y
    # Tuỳ theo cột ROI hay cột target thực tế trong dataset
    # Ở đây giả sử cột target là 'ROI'
    if "ROI" not in df_copy.columns:
        raise ValueError("Không tìm thấy cột 'ROI' trong DataFrame")

    X = df_copy[['TARGET_AUDIENCE', 'CHANNEL_USED', 'ACQUISITION_COST', 'LOCATION', 'LANGUAGE',
             'CLICKS', 'IMPRESSIONS', 'ENGAGEMENT_SCORE', 'CTR', 'CPC',
             'CPM', 'CONVERSION_RATE', 'QUARTER', 'MONTH', 'DURATION']]


    y = df_copy['ROI']

    # Tách feature phân loại & số
    categorical_features = ['TARGET_AUDIENCE', 'CHANNEL_USED', 'LOCATION', 'LANGUAGE', 'QUARTER', 'MONTH']
    numerical_features = ['ACQUISITION_COST', 'CLICKS', 'IMPRESSIONS', 'ENGAGEMENT_SCORE', 'CTR',
                          'CPC', 'CPM', 'CONVERSION_RATE', 'DURATION']

    # Pipeline đơn giản RandomForestRegressor
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
            ('num', 'passthrough', numerical_features)
        ])

    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(random_state=42))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # Đánh giá
    print("RandomForest Regressor Evaluation:")
    print("  Mean Absolute Error (MAE):", mean_absolute_error(y_test, y_pred))
    print("  Mean Squared Error (MSE):", mean_squared_error(y_test, y_pred))
    print("  R-squared Score (R2):", r2_score(y_test, y_pred))

    result_df = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
    print("\nKết quả dự đoán (RandomForest):")
    print(result_df.head())

    # Feature Importance
    importances = model.named_steps['regressor'].feature_importances_
    for feature, importance in zip(X.columns, importances):
        print(f"{feature}: {importance:.4f}")

    # So sánh với một số model khác (baseline)
    regression_models = [
        LinearRegression(),
        Ridge(random_state=2024),
        Lasso(random_state=2024),
        DecisionTreeRegressor(random_state=2024),
        RandomForestRegressor(random_state=2024),
        ExtraTreesRegressor(random_state=2024),
        XGBRegressor(random_state=2024)
    ]

    # Biến đổi X để so sánh baseline
    num_transformer = Pipeline(steps=[('scaler', StandardScaler())])
    cat_transformer = Pipeline(steps=[('onehot', OneHotEncoder())])

    baseline_preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_transformer, numerical_features),
            ('cat', cat_transformer, categorical_features)
        ]
    )

    X_baseline = baseline_preprocessor.fit_transform(X)
    baseline_results = generate_baseline_result(regression_models, X_baseline, y, metric='neg_mean_squared_error', cv=5)
    print("\nBaseline Model Comparison (MSE):")
    print(baseline_results)

    # Main model: Lasso + GridSearch
    final_preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
            ('num', 'passthrough', numerical_features)
        ]
    )

    final_model = Pipeline(steps=[
        ('preprocessor', final_preprocessor),
        ('scaler', StandardScaler()),
        ('regressor', Lasso())
    ])

    param_grid = {
        'regressor__alpha': [0.001, 0.01, 0.1, 1, 10, 100],
        'regressor__max_iter': [1000, 5000, 10000],
        'regressor__tol': [1e-4, 1e-3, 1e-2]
    }

    X_train2, X_test2, y_train2, y_test2 = train_test_split(X, y, test_size=0.2, random_state=42)
    grid_search = GridSearchCV(final_model, param_grid, cv=5, scoring='neg_mean_squared_error')
    grid_search.fit(X_train2, y_train2)

    best_lasso = grid_search.best_estimator_
    y_pred2 = best_lasso.predict(X_test2)

    mae = mean_absolute_error(y_test2, y_pred2)
    mse = mean_squared_error(y_test2, y_pred2)
    r2 = r2_score(y_test2, y_pred2)

    print("\n=== Final Lasso Model with GridSearch ===")
    print("Best Params:", grid_search.best_params_)
    print("Mean Absolute Error (MAE):", mae)
    print("Mean Squared Error (MSE):", mse)
    print("R-squared Score (R2):", r2)

if __name__ == "__main__":
    main()
