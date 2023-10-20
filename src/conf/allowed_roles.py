from src.services.roles import RoleAccess
from src.database.models import UserRole


all_users = RoleAccess([UserRole.ADMIN, UserRole.MODERATOR])
moderators_admin = RoleAccess([UserRole.ADMIN, UserRole.MODERATOR])
admin = RoleAccess([UserRole.ADMIN])
only_users = RoleAccess([UserRole.USER])
