from models.base import BaseModel
from models.xgbregressor import XGBRegressor
from models.lightgbmclassifier import LightGBMClassifier
from biblical_qa.analyzer import BiblicalWordAnalyzer

__all__ = ["BaseModel", "XGBRegressor", "LightGBMClassifier", "BiblicalWordAnalyzer"]

def load_model(model_name: str) -> BaseModel:
    """Dynamically load a model class by name."""
    models = {
        "xgbregressor": XGBRegressor,
        "lightgbmclassifier": LightGBMClassifier,
        "biblical_qa": BiblicalWordAnalyzer,
    }
    if model_name not in models:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(models.keys())}")
    return models[model_name]()
