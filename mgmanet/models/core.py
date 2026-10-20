"""Stable placeholder for the future public model builder."""

class CoreNotReleasedError(NotImplementedError):
    """The requested research functionality is not part of this release."""


def build_model(*args, **kwargs):
    """Reserved API. No baseline or dummy predictions are substituted."""
    raise CoreNotReleasedError(
        "The MGMANet research model is withheld in this pre-release. "
        "Its implementation and weights are planned for release after paper acceptance. "
        "Evaluation and visualization of existing prediction files are available now."
    )
