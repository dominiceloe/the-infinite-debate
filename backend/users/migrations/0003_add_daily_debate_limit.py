# Generated manually for Beta Simplification
# Adds daily_debate_limit field and updates default credits from 15 to 10

from django.db import migrations, models


def backfill_daily_debate_limit(apps, schema_editor):
    """
    Backfill daily_debate_limit for existing users.
    Trial users: 2/day (enforced limit)
    Paid users: 999/day (effectively unlimited)
    """
    User = apps.get_model('users', 'User')

    # Set unlimited (999) for existing paid subscribers
    User.objects.filter(
        subscription_tier__in=['starter', 'pro', 'enterprise']
    ).update(daily_debate_limit=999)

    # Trial users already get 2 from default value


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_stripe_payment_method_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='daily_debate_limit',
            field=models.IntegerField(
                default=2,
                help_text='Maximum debates per day (2 for trial, 999 for paid tiers = unlimited)'
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='credits_remaining',
            field=models.IntegerField(
                default=10,
                help_text='Credits available this billing period (10 for trial, 30 for starter)'
            ),
        ),
        migrations.RunPython(backfill_daily_debate_limit, migrations.RunPython.noop),
    ]
