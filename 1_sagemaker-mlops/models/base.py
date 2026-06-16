from abc import ABC, abstractmethod
import pickle
import tarfile
from pathlib import Path
from typing import Any, Dict

class BaseModel(ABC):
    """Abstract base class for all models."""

    def __init__(self):
        self.model = None
        self.metadata = {}

    @abstractmethod
    def train(self, X, y, **kwargs):
        """Train the model on data X with labels y."""
        pass

    @abstractmethod
    def predict(self, X):
        """Generate predictions for data X."""
        pass

    def save(self, path: str) -> None:
        """
        Save model to a tarball at the given path.
        Tarballs should contain:
        - model.pkl: The trained model object
        - metadata.pkl: Model metadata (name, hyperparameters, etc.)
        """
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Create temp directory for tarball contents
        temp_dir = path_obj.parent / f"{path_obj.stem}_temp"
        temp_dir.mkdir(exist_ok=True)

        try:
            # Save model and metadata
            with open(temp_dir / "model.pkl", "wb") as f:
                pickle.dump(self.model, f)
            with open(temp_dir / "metadata.pkl", "wb") as f:
                pickle.dump(self.metadata, f)

            # Create tarball
            with tarfile.open(path, "w:gz") as tar:
                tar.add(temp_dir / "model.pkl", arcname="model.pkl")
                tar.add(temp_dir / "metadata.pkl", arcname="metadata.pkl")
        finally:
            # Cleanup temp directory
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def load(self, path: str) -> None:
        """
        Load model from a tarball at the given path.
        """
        path_obj = Path(path)
        temp_dir = path_obj.parent / f"{path_obj.stem}_temp"
        temp_dir.mkdir(exist_ok=True)

        try:
            # Extract tarball
            with tarfile.open(path, "r:gz") as tar:
                tar.extractall(temp_dir)

            # Load model and metadata
            with open(temp_dir / "model.pkl", "rb") as f:
                self.model = pickle.load(f)
            with open(temp_dir / "metadata.pkl", "rb") as f:
                self.metadata = pickle.load(f)
        finally:
            # Cleanup temp directory
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def get_metadata(self) -> Dict[str, Any]:
        """Return model metadata."""
        return self.metadata.copy()

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata key-value pair."""
        self.metadata[key] = value
