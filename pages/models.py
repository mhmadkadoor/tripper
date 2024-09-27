from django.db import models
from django.contrib.auth.models import User



class Trip(models.Model):
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True,)
    date = models.DateField()
    leader = models.ForeignKey(User, on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='joined_trips', blank=True)
    has_ended = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    def total_amount_paid(self):
        return sum(item.amount_paid for item in self.items.filter(is_paid=True))

    def total_items(self):
        return self.items.count()
    
    def total_confirmed(self):
        return self.members.filter(payment_confirmed=True).count()
    
    def total_members(self):
        return self.members.count()

    def paid_items(self):
        return self.items.filter(is_paid=True).count()

    def complete_ratio(self):
        if self.total_items() == 0:
            return 0
        return (self.paid_items() / self.total_items()) * 100
    
    def confirmed_ratio(self):
        if self.total_confirmed == 0:
            return 0
        return (self.total_confirmed() / self.total_members()) * 100

    def split_bill(self):
        total_paid = self.total_amount_paid()
        members_count = self.participants.count()
        if members_count == 0:
            return {}

        split_amount = total_paid / members_count
        balance = {}
        for member in self.participants.all():
            member_paid = sum(item.amount_paid for item in self.items.filter(payer=member, is_paid=True))
            balance[member] = {
                'paid': member_paid,
                'owes': split_amount - member_paid if member_paid < split_amount else 0,
                'collects': member_paid - split_amount if member_paid > split_amount else 0,
                'payment_confirmed': TripMember.objects.get(trip=self, member=member).payment_confirmed
            }
        return balance


class Item(models.Model):
    trip = models.ForeignKey(Trip, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    payer = models.ForeignKey(User, related_name="paid_items", null=True, blank=True, on_delete=models.SET_NULL)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

class TripMember(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='members')
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_confirmed = models.BooleanField(default=False)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    iban = models.CharField(max_length=34, blank=True)
    bank_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'
