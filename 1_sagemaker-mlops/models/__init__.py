from models.base import BaseModel

__all__ = ["BaseModel", "XGBRegressor", "LightGBMClassifier", "load_model"]

def load_model(model_name: str) -> BaseModel:
    """Dynamically load a model class by name (lazy import)."""
    if model_name == "xgbregressor":
        from models.xgbregressor import XGBRegressor
        return XGBRegressor()
    elif model_name == "lightgbmclassifier":
        from models.lightgbmclassifier import LightGBMClassifier
        return LightGBMClassifier()
    else:
        raise ValueError(f"Unknown model: {model_name}. Available: xgbregressor, lightgbmclassifier")

def __getattr__(name: str):
    """Support direct imports like: from models import XGBRegressor"""
    if name == "XGBRegressor":
        from models.xgbregressor import XGBRegressor
        return XGBRegressor
    elif name == "LightGBMClassifier":
        from models.lightgbmclassifier import LightGBMClassifier
        return LightGBMClassifier
    raise AttributeError(f"module 'models' has no attribute '{name}'")
