"""
AI/ML Module for StellarNexus
Predictive Analytics and Machine Learning for GitHub Repository Analysis
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings("ignore")


class GitHubPredictor:
    """AI-powered predictor for GitHub repository growth"""

    def __init__(self, data_path: str = "data"):
        self.data_path = data_path
        self.models = {}
        self.scaler = StandardScaler()
        self.ensure_data_directory()

    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(f"{self.data_path}/predictions", exist_ok=True)

    def load_historical_data(self) -> pd.DataFrame:
        """Load and preprocess historical repository data"""
        try:
            # Load current data
            with open(f"{self.data_path}/github_top_20250907_124243.json", "r") as f:
                current_data = json.load(f)

            # Extract items from the API response
            if "items" in current_data:
                current_repos = current_data["items"]
            else:
                current_repos = current_data

            # Convert to DataFrame
            df_current = pd.DataFrame(current_repos)

            # Load historical data if exists
            try:
                with open(f"{self.data_path}/top_repos_history.json", "r") as f:
                    history_data = json.load(f)
                    df_history = pd.DataFrame(history_data)
            except FileNotFoundError:
                df_history = pd.DataFrame()

            # Process data for ML
            return self._process_data_for_ml(df_current, df_history)

        except FileNotFoundError:
            print("Historical data not found. Please run data collection first.")
            return pd.DataFrame()

    def _process_data_for_ml(
        self, current_df: pd.DataFrame, history_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Process data for machine learning models"""
        # Add time-based features - handle timezone issues
        current_df["created_at"] = pd.to_datetime(
            current_df["created_at"], utc=True
        ).dt.tz_localize(None)
        now = pd.Timestamp.now()
        current_df["days_since_creation"] = current_df["created_at"].apply(
            lambda x: (now - x).days
        )
        current_df["stars_per_day"] = current_df["stargazers_count"] / current_df[
            "days_since_creation"
        ].clip(lower=1)

        # Add growth rate features
        current_df["growth_rate"] = current_df["stargazers_count"] / (
            current_df["days_since_creation"] + 1
        )

        # Language encoding
        language_map = {
            "JavaScript": 1,
            "Python": 2,
            "Java": 3,
            "TypeScript": 4,
            "C++": 5,
            "C#": 6,
            "PHP": 7,
            "Ruby": 8,
            "Go": 9,
            "Rust": 10,
            "Other": 11,
        }
        current_df["language_encoded"] = (
            current_df["language"].map(language_map).fillna(11)
        )

        # Add repository quality features
        current_df["has_description"] = current_df["description"].notna().astype(int)
        current_df["description_length"] = (
            current_df["description"].fillna("").str.len()
        )

        return current_df

    def train_growth_prediction_model(self, df: pd.DataFrame) -> Dict:
        """Train model to predict future star growth"""
        if df.empty:
            return {"error": "No data available for training"}

        # Features for prediction
        features = [
            "days_since_creation",
            "stars_per_day",
            "growth_rate",
            "language_encoded",
            "has_description",
            "description_length",
        ]

        # Target: predict stars in 30 days
        target = "stargazers_count"

        # Prepare data
        X = df[features].fillna(0)
        y = df[target]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train multiple models
        models = {
            "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
            "GradientBoosting": GradientBoostingRegressor(
                n_estimators=100, random_state=42
            ),
            "LinearRegression": LinearRegression(),
        }

        results = {}

        for name, model in models.items():
            # Train model
            model.fit(X_train_scaled, y_train)

            # Predictions
            y_pred = model.predict(X_test_scaled)

            # Metrics
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            results[name] = {
                "model": model,
                "mae": mae,
                "mse": mse,
                "r2": r2,
                "predictions": y_pred[:5].tolist(),  # Sample predictions
                "actual": y_test[:5].tolist(),
            }

            self.models[name] = model

        # Save best model (highest R²)
        best_model_name = max(results.keys(), key=lambda x: results[x]["r2"])
        self.save_model(best_model_name, results[best_model_name]["model"])

        return {
            "best_model": best_model_name,
            "results": results,
            "feature_importance": self.get_feature_importance(
                best_model_name, features
            ),
        }

    def predict_future_growth(
        self, repository_data: Dict, days_ahead: int = 30
    ) -> Dict:
        """Predict future growth for a specific repository"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame([repository_data])

            # Process features
            df["days_since_creation"] = (
                pd.Timestamp.now() - pd.to_datetime(df["created_at"])
            ).dt.days
            df["stars_per_day"] = df["stargazers_count"] / df[
                "days_since_creation"
            ].clip(lower=1)
            df["growth_rate"] = df["stargazers_count"] / (df["days_since_creation"] + 1)

            # Language encoding
            language_map = {
                "JavaScript": 1,
                "Python": 2,
                "Java": 3,
                "TypeScript": 4,
                "C++": 5,
                "C#": 6,
                "PHP": 7,
                "Ruby": 8,
                "Go": 9,
                "Rust": 10,
            }
            df["language_encoded"] = df["language"].map(language_map).fillna(11)

            df["has_description"] = df["description"].notna().astype(int)
            df["description_length"] = df["description"].fillna("").str.len()

            # Features for prediction
            features = [
                "days_since_creation",
                "stars_per_day",
                "growth_rate",
                "language_encoded",
                "has_description",
                "description_length",
            ]

            X = df[features].fillna(0)
            X_scaled = self.scaler.transform(X)

            # Load best model
            best_model = self.load_best_model()
            if best_model is None:
                return {"error": "No trained model available"}

            # Make prediction
            current_stars = repository_data["stargazers_count"]
            predicted_stars = best_model.predict(X_scaled)[0]

            # Calculate growth metrics
            predicted_growth = predicted_stars - current_stars
            growth_rate = (
                (predicted_growth / current_stars) * 100 if current_stars > 0 else 0
            )

            # Confidence intervals (simplified)
            confidence_interval = predicted_stars * 0.15  # 15% confidence interval

            return {
                "repository": repository_data["name"],
                "current_stars": int(current_stars),
                "predicted_stars_30d": int(predicted_stars),
                "predicted_growth": int(predicted_growth),
                "growth_rate_percent": round(growth_rate, 2),
                "confidence_interval": {
                    "lower": int(predicted_stars - confidence_interval),
                    "upper": int(predicted_stars + confidence_interval),
                },
                "days_ahead": days_ahead,
                "prediction_date": (
                    datetime.now() + timedelta(days=days_ahead)
                ).strftime("%Y-%m-%d"),
            }

        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}

    def get_feature_importance(self, model_name: str, features: List[str]) -> Dict:
        """Get feature importance for the model"""
        if model_name not in self.models:
            return {}

        model = self.models[model_name]

        if hasattr(model, "feature_importances_"):
            importance = model.feature_importances_
            return dict(zip(features, importance))
        elif hasattr(model, "coef_"):
            importance = np.abs(model.coef_)
            return dict(zip(features, importance))

        return {}

    def save_model(self, model_name: str, model):
        """Save trained model"""
        import joblib

        os.makedirs(f"{self.data_path}/models", exist_ok=True)
        joblib.dump(model, f"{self.data_path}/models/{model_name}.joblib")

    def load_best_model(self):
        """Load the best performing model"""
        import joblib

        model_path = f"{self.data_path}/models"

        if not os.path.exists(model_path):
            return None

        # Find model with highest R² (this is simplified - in practice you'd store metadata)
        model_files = [f for f in os.listdir(model_path) if f.endswith(".joblib")]

        if not model_files:
            return None

        # Load first available model (in practice, load the best one based on metadata)
        best_model_path = f"{model_path}/{model_files[0]}"
        return joblib.load(best_model_path)

    def analyze_trends(self, df: pd.DataFrame) -> Dict:
        """Analyze trends and patterns in repository data"""
        if df.empty:
            return {"error": "No data available for analysis"}

        # Language distribution
        language_dist = df["language"].value_counts().head(10).to_dict()

        # Growth rate analysis
        high_growth = df[df["growth_rate"] > df["growth_rate"].quantile(0.75)]
        low_growth = df[df["growth_rate"] < df["growth_rate"].quantile(0.25)]

        # Age vs growth correlation
        correlation = df["days_since_creation"].corr(df["growth_rate"])

        return {
            "language_distribution": language_dist,
            "high_growth_repos": len(high_growth),
            "low_growth_repos": len(low_growth),
            "avg_growth_rate": df["growth_rate"].mean(),
            "median_growth_rate": df["growth_rate"].median(),
            "age_growth_correlation": correlation,
            "top_performers": high_growth[["name", "stargazers_count", "growth_rate"]]
            .head(5)
            .to_dict("records"),
            "insights": self._generate_insights(df),
        }

    def _generate_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate AI-powered insights"""
        insights = []

        # Language insights
        top_language = df["language"].value_counts().index[0]
        insights.append(
            f"🔥 {top_language} repositories dominate with highest growth potential"
        )

        # Growth insights
        avg_growth = df["growth_rate"].mean()
        if avg_growth > 10:
            insights.append(
                "📈 High growth environment - excellent opportunities for new projects"
            )
        elif avg_growth < 5:
            insights.append("📊 Mature ecosystem - focus on quality over quantity")

        # Age insights
        young_repos = df[df["days_since_creation"] < 365]
        if len(young_repos) > len(df) * 0.3:
            insights.append("🌱 Young ecosystem - great time for early adoption")

        return insights

    def predict_top_performers(self, df: pd.DataFrame, top_n: int = 10) -> List[Dict]:
        """Predict which repositories will be top performers in the future"""
        if df.empty:
            return []

        predictions = []

        for _, repo in df.iterrows():
            pred = self.predict_future_growth(repo.to_dict())
            if "error" not in pred:
                predictions.append(pred)

        # Sort by predicted growth rate
        predictions.sort(key=lambda x: x["growth_rate_percent"], reverse=True)

        return predictions[:top_n]


# Global predictor instance
predictor = GitHubPredictor()


def get_ml_insights() -> Dict:
    """Get comprehensive ML insights for the dashboard"""
    df = predictor.load_historical_data()

    if df.empty:
        return {"error": "No data available"}

    # Train model if not exists
    if not predictor.models:
        training_results = predictor.train_growth_prediction_model(df)
    else:
        training_results = {"message": "Using existing trained model"}

    # Get predictions for top repos
    top_predictions = predictor.predict_top_performers(df)

    # Get trend analysis
    trends = predictor.analyze_trends(df)

    return {
        "training_results": training_results,
        "top_predictions": top_predictions,
        "trends": trends,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    # Example usage
    print("🚀 StellarNexus AI/ML Predictor")
    print("=" * 50)

    # Load and analyze data
    predictor = GitHubPredictor()
    df = predictor.load_historical_data()

    if not df.empty:
        print(f"📊 Loaded {len(df)} repositories for analysis")

        # Train model
        print("\n🤖 Training ML models...")
        results = predictor.train_growth_prediction_model(df)

        if "best_model" in results:
            print(f"✅ Best model: {results['best_model']}")
            print(
                f"📊 Training MAE: {results['results'][results['best_model']]['mae']:.3f}"
            )
            print(
                f"🎯 Training R²: {results['results'][results['best_model']]['r2']:.3f}"
            )
        # Get insights
        print("\n🔍 Analyzing trends...")
        trends = predictor.analyze_trends(df)
        print(f"📈 Average growth rate: {trends['avg_growth_rate']:.2f}")
        print(f"🏆 Top language: {list(trends['language_distribution'].keys())[0]}")

        # Make prediction for first repo
        if len(df) > 0:
            first_repo = df.iloc[0].to_dict()
            print(f"\n🔮 Predicting growth for: {first_repo['name']}")
            prediction = predictor.predict_future_growth(first_repo)
            if "error" not in prediction:
                print(f"📊 Current stars: {prediction['current_stars']}")
                print(f"🎯 Predicted in 30 days: {prediction['predicted_stars_30d']}")
                print(
                    f"📈 Growth: {prediction['predicted_growth']} ({prediction['growth_rate_percent']}%)"
                )

    else:
        print("❌ No data available. Please run data collection first.")
