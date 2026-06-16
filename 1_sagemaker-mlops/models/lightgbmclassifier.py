import lightgbm as lgb
from models.base import BaseModel

class LightGBMClassifier(BaseModel):
    """LightGBM Classifier model."""

    def __init__(self, **kwargs):
        super().__init__()
        params = {
            "n_estimators": kwargs.get("n_estimators", 100),
            "max_depth": kwargs.get("max_depth", 6),
            "learning_rate": kwargs.get("learning_rate", 0.1),
            "random_state": kwargs.get("random_state", 42),
        }
        self.model = lgb.LGBMClassifier(**params)
        self.set_metadata("model_type", "lightgbmclassifier")
        self.set_metadata("hyperparameters", params)

    def train(self, X, y, **kwargs):
        """Train LightGBM classifier."""
        eval_set = kwargs.get("eval_set")
        early_stopping_rounds = kwargs.get("early_stopping_rounds", 10)

        self.model.fit(
            X, y,
            eval_set=eval_set,
            early_stopping_rounds=early_stopping_rounds,
            verbose=True
        )

    def predict(self, X):
        """Generate predictions."""
        return self.model.predict(X)

    def predict_proba(self, X):
        """Generate class probabilities."""
        return self.model.predict_proba(X)
