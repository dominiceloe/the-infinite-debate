"""
Utility functions for debate management and credit calculation.
"""
from rest_framework.exceptions import ValidationError


def calculate_debate_credits(num_participants, max_rounds, depth_level):
    """
    Calculate required credits for a debate based on configuration.

    Credit costs based on debate size:
    - Small (2-3 people, ≤5 rounds, introductory): 1 credit (~$0.15 API cost)
    - Medium (4-6 people, ≤7 rounds, intermediate): 3 credits (~$0.45 cost)
    - Large (7-10 people, ≤10 rounds, advanced): 8 credits (~$1.20 cost)
    - XL (11-15 people, ≤15 rounds, advanced): 20 credits (~$3.00 cost, Enterprise only)

    Args:
        num_participants (int): Number of participants in the debate
        max_rounds (int): Maximum number of debate rounds
        depth_level (str): Depth level - 'introductory', 'intermediate', or 'advanced'

    Returns:
        int: Number of credits required

    Raises:
        ValidationError: If parameters are invalid or outside allowed ranges
    """
    # Validate inputs
    if not isinstance(num_participants, int) or num_participants < 2:
        raise ValidationError("Number of participants must be at least 2.")

    if num_participants > 15:
        raise ValidationError("Maximum 15 participants allowed per debate.")

    if not isinstance(max_rounds, int) or max_rounds < 1:
        raise ValidationError("Number of rounds must be at least 1.")

    if max_rounds > 15:
        raise ValidationError("Maximum 15 rounds allowed per debate.")

    if depth_level not in ['introductory', 'intermediate', 'advanced']:
        raise ValidationError(
            f"Invalid depth level '{depth_level}'. "
            "Must be 'introductory', 'intermediate', or 'advanced'."
        )

    # Calculate credits based on debate size
    # Priority: Check for XL first, then work down to smaller sizes

    # XL Debate: 11-15 participants, ≤15 rounds, advanced
    if num_participants >= 11 and max_rounds <= 15 and depth_level == 'advanced':
        return 20

    # Large Debate: 7-10 participants, ≤10 rounds, advanced
    if num_participants >= 7 and num_participants <= 10 and max_rounds <= 10 and depth_level == 'advanced':
        return 8

    # Medium Debate: 4-6 participants, ≤7 rounds, intermediate
    if num_participants >= 4 and num_participants <= 6 and max_rounds <= 7 and depth_level == 'intermediate':
        return 3

    # Small Debate: 2-3 participants, ≤5 rounds, introductory
    if num_participants >= 2 and num_participants <= 3 and max_rounds <= 5 and depth_level == 'introductory':
        return 1

    # For configurations that don't match predefined tiers,
    # calculate credits based on a formula
    # Base credit calculation: complexity factor
    base_credits = 1

    # Participant multiplier
    if num_participants <= 3:
        participant_factor = 1.0
    elif num_participants <= 6:
        participant_factor = 2.5
    elif num_participants <= 10:
        participant_factor = 6.0
    else:  # 11-15
        participant_factor = 15.0

    # Rounds multiplier
    if max_rounds <= 5:
        rounds_factor = 1.0
    elif max_rounds <= 7:
        rounds_factor = 1.3
    elif max_rounds <= 10:
        rounds_factor = 1.5
    else:  # 11-15
        rounds_factor = 2.0

    # Depth multiplier
    depth_factors = {
        'introductory': 1.0,
        'intermediate': 1.2,
        'advanced': 1.5,
    }
    depth_factor = depth_factors.get(depth_level, 1.0)

    # Calculate total credits
    calculated_credits = base_credits * participant_factor * rounds_factor * depth_factor

    # Round up to nearest integer
    import math
    return math.ceil(calculated_credits)


def validate_user_credits(user, required_credits):
    """
    Validate if user has sufficient credits and active subscription.

    Args:
        user: User instance
        required_credits (int): Number of credits required

    Returns:
        tuple: (bool, str) - (can_proceed, error_message)
            - If can_proceed is True, error_message is None
            - If can_proceed is False, error_message explains why
    """
    # Check if subscription is active
    if user.subscription_status != 'active':
        return False, f"Subscription is {user.subscription_status}. Please activate your subscription."

    # Check if trial has expired
    if user.is_trial_expired():
        return False, "Trial period has expired. Please upgrade to a paid plan."

    # Check if user has enough credits
    if user.credits_remaining < required_credits:
        return False, (
            f"Insufficient credits. You need {required_credits} credits but only have "
            f"{user.credits_remaining} remaining. "
            f"Your credits will reset on {user.credits_reset_date or 'upgrade to paid plan'}."
        )

    # Check XL debate tier restriction (Enterprise only)
    if required_credits >= 20 and user.subscription_tier != 'enterprise':
        return False, (
            "XL debates (11-15 participants with advanced depth) require an Enterprise subscription. "
            "Please upgrade or create a smaller debate."
        )

    return True, None


def get_debate_size_name(num_participants, max_rounds, depth_level):
    """
    Get a human-readable name for the debate size category.

    Args:
        num_participants (int): Number of participants
        max_rounds (int): Maximum rounds
        depth_level (str): Depth level

    Returns:
        str: Size category name (e.g., "Small", "Medium", "Large", "XL", or "Custom")
    """
    if num_participants >= 11 and max_rounds <= 15 and depth_level == 'advanced':
        return "XL"
    elif num_participants >= 7 and num_participants <= 10 and max_rounds <= 10 and depth_level == 'advanced':
        return "Large"
    elif num_participants >= 4 and num_participants <= 6 and max_rounds <= 7 and depth_level == 'intermediate':
        return "Medium"
    elif num_participants >= 2 and num_participants <= 3 and max_rounds <= 5 and depth_level == 'introductory':
        return "Small"
    else:
        return "Custom"
