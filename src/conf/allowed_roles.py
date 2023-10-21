from src.services.roles import RoleAccess
from src.database.models import UserRole


all_users = RoleAccess([UserRole.admin, UserRole.moderator, UserRole.user])
moderators_admin = RoleAccess([UserRole.admin, UserRole.moderator])
admin = RoleAccess([UserRole.admin])
only_users = RoleAccess([UserRole.user])
