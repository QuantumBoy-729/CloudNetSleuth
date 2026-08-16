"""Process lifecycle state used by the readiness probe."""

from dataclasses import dataclass


@dataclass
class ServiceState:
    """Tracks whether the process should receive traffic.

    ``ready`` is flipped off as the first step of shutdown so the readiness
    probe fails and Kubernetes removes the pod from the Service endpoints
    before in-flight connections are drained.
    """

    ready: bool = False
    shutting_down: bool = False

    def mark_ready(self) -> None:
        """Mark the process as able to serve traffic."""
        self.ready = True
        self.shutting_down = False

    def mark_draining(self) -> None:
        """Mark the process as shutting down and no longer ready."""
        self.ready = False
        self.shutting_down = True


service_state = ServiceState()
