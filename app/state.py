from enum import Enum 
from datetime import datetime, timedelta
from app.config import settings
SUBSCRIPTION_PERIOD = settings.subscription_period_days
TRIAL_PERIOD = settings.trial_period_days
GRACE_PERIOD_DAYS = settings.grace_period_days
class SubscriptionState(str, Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    GRACE = "grace"
    CANCELED = "canceled"

class Subscription:
    """
    Subscription state machine. 
    States: TRIALING | ACTIVE | GRACE | CANCELED
    Transitions: Trialing -> Active (on payment success), 
                Trialing -> Canceled (on payment failure after trial period ends + 1 day grace period), 
                Active -> Grace (on payment failure after period end date), 
                Grace -> Active (on payment success), 
                Grace -> Canceled (on payment failure after period end date),
                Any state -> Canceled (on cancel)
    """
    def __init__(self,id: str, period_end_at: datetime, state: SubscriptionState = SubscriptionState.TRIALING):
        """Initialize a subscription from the database as a state machine instance.
            Args: id: subscription id
                state: subscription state
                period_end_at: the end date of the current subscription period. Will be calculated and given by a service. 
            When a subscription is created it starts in the trial period, hence the default state is Trialing 
        """
        self.state = state
        self.id = id
        self.period_end_at = period_end_at
    def cancel(self):
        """
        State -> Cancelled unconditionally, even if the subscription is in trialing or active state.
        """
        if self.state == SubscriptionState.CANCELED:
            raise ValueError(f"Subscription is already cancelled. Subscription id: {self.id}")
        self.state = SubscriptionState.CANCELED
 
    def handle_payment_success(self, event_timestamp: datetime):
        """
        Trialing -> Active, Grace -> Active, Canceled -> Canceled (payment success should not change the state of a canceled subscription)
        """
        if self.state == SubscriptionState.CANCELED:
            """
            A cancelled subscription will not be reactivated.
            When a user wants to reactivate a subscription we can create a new subscription. 
            Maybe in this scenario where a user cancelled their subscription and a payment went trough we can log this event and start a refund process.

            """
            raise ValueError(f"Payment success event received for a cancelled subscription. Subscription id: {self.id}")
            return
        if self.state in [SubscriptionState.TRIALING, SubscriptionState.GRACE, SubscriptionState.ACTIVE]:
            self.state = SubscriptionState.ACTIVE
            if event_timestamp < self.period_end_at: # we do not steal days out of the subscription period if the payment was made before the current period ended
                self.period_end_at = self.period_end_at + timedelta(days=SUBSCRIPTION_PERIOD) 
            else:
                self.period_end_at = event_timestamp + timedelta(days=SUBSCRIPTION_PERIOD)
    def handle_payment_failure(self, event_timestamp: datetime):
        """
        Trialing -> Grace 
        Active -> Grace 
        Grace -> Canceled (if payment failure happens after period end date)

        """
        if self.state == SubscriptionState.CANCELED:
            """
            A cancelled subscription will not change state on payment failure, it will remain cancelled.
            """
            # send notification to payment service to cancel the subscription in the payment provider as well, if not already done.
            return
        if self.state == SubscriptionState.TRIALING or self.state == SubscriptionState.ACTIVE:
            self.state = SubscriptionState.GRACE
            self.period_end_at = max(event_timestamp, self.period_end_at) + timedelta(days=GRACE_PERIOD_DAYS)
            
        elif self.state == SubscriptionState.GRACE and event_timestamp > self.period_end_at:
            self.state = SubscriptionState.CANCELED
