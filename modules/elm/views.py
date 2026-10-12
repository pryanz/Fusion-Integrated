from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.utils.pagination import StandardResultsSetPagination  # assumed helper path

from .models import LeaveType, LeaveBalance, LeaveRequest
from .serializers import (
    LeaveTypeSerializer,
    LeaveBalanceSerializer,
    LeaveRequestSerializer,
    LeaveApprovalSerializer,
)
from .permissions import IsHR, IsManagerOrHR, IsOwnerOrHR


class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated, IsHR]


class LeaveBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        from .permissions import get_user_role
        role = get_user_role(user)
        if role in ("hr", "admin", "HR", "Admin"):
            return LeaveBalance.objects.select_related("user", "leave_type").all()
        return LeaveBalance.objects.filter(user=user).select_related("leave_type")


class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        from .permissions import get_user_role
        role = get_user_role(user)
        qs = LeaveRequest.objects.select_related("employee", "leave_type", "reviewed_by")
        if role in ("hr", "admin", "HR", "Admin"):
            return qs.all()
        if role in ("manager", "Manager"):
            return qs.all()
        return qs.filter(employee=user)

    def get_permissions(self):
        if self.action in ["retrieve", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrHR()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsManagerOrHR])
    def approve_reject(self, request, pk=None):
        leave = self.get_object()
        serializer = LeaveApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action_val = serializer.validated_data["action"]
        if action_val == "approve":
            leave.status = "approved"
        else:
            leave.status = "rejected"

        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.save()

        # TODO: deduct leave balance, send notification email
        pass

        return Response({"status": leave.status}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsHR])
    def pending(self, request):
        qs = LeaveRequest.objects.filter(status="pending").select_related("employee", "leave_type")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
