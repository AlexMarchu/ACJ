from rest_framework import permissions


class IsAdminOrTeacher(permissions.BasePermission):
    
    def has_permission(self, request, view):
        return request.user.role.role in ['teacher', 'admin']
