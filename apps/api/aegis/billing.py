"""Disabled commercial boundary. No payment provider implementation or SDK."""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class SubscriptionPlan:
    code: str
    title: str

@dataclass(frozen=True)
class PricingPolicy:
    currency: str = 'EGP'
    enabled: bool = False

@dataclass(frozen=True)
class BillingAccount:
    organization_id: str

@dataclass(frozen=True)
class RemediationQuote:
    scope: str
    amount_minor: int
    currency: str

@dataclass(frozen=True)
class InvoiceRecord:
    reference: str
    status: str = 'draft'

@dataclass(frozen=True)
class PaymentEvent:
    reference: str
    provider: str

class PaymentProvider(Protocol):
    def create_checkout(self, account: BillingAccount): ...

class DisabledPaymentProvider:
    def create_checkout(self, account):
        raise RuntimeError('Payment processing is disabled in this build.')
