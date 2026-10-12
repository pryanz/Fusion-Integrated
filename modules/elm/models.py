from django.db import models
from django.contrib.auth import get_user_model

from fusion_auth.user_profile import UserProfile  # noqa – extended profile helper

User = get_user_model()


LEAVE_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]


class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    max_days_per_year = models.PositiveIntegerField(default=12)
    carry_forward = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "elm_leave_type"

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leave_balances")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField()
    total_days = models.PositiveIntegerField(default=0)
    used_days = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "elm_leave_balance"
        unique_together = ("user", "leave_type", "year")

    @property
    def remaining_days(self):
        return self.total_days - self.used_days

    def __str__(self):
        return f"{self.user} - {self.leave_type} ({self.year})"


class LeaveRequest(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=LEAVE_STATUS_CHOICES, default="pending")
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_leaves"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "elm_leave_request"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"
