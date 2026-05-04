from __future__ import annotations

from abc import ABC, abstractmethod

from risk_dashboard.modules.home_onboarding.domain.entities import HomeState, OnboardingProfile, OnboardingSession


class OnboardingSessionRepository(ABC):
    @abstractmethod
    def create(self) -> OnboardingSession:
        raise NotImplementedError

    @abstractmethod
    def get(self, session_id: str) -> OnboardingSession | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, session: OnboardingSession) -> OnboardingSession:
        raise NotImplementedError


class OnboardingProfileRepository(ABC):
    @abstractmethod
    def save(self, profile: OnboardingProfile) -> OnboardingProfile:
        raise NotImplementedError

    @abstractmethod
    def get(self, session_id: str) -> OnboardingProfile | None:
        raise NotImplementedError


class HomeStateRepository(ABC):
    @abstractmethod
    def save(self, state: HomeState) -> HomeState:
        raise NotImplementedError

    @abstractmethod
    def get(self, session_id: str) -> HomeState | None:
        raise NotImplementedError
