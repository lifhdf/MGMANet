"""Reserved training and inference entry points."""
from .models import CoreNotReleasedError


def train(config=None):
    """Reserved API; training is unavailable until the core release."""
    raise CoreNotReleasedError(
        "Training is unavailable: the research model and training recipe "
        "are not included in this pre-release."
    )


def predict(input_path=None):
    """Reserved API; this release does not perform model inference."""
    raise CoreNotReleasedError(
        "Inference is unavailable: the research model and weights "
        "are not included in this pre-release. Use existing prediction JSON "
        "with the evaluate or visualize commands."
    )
