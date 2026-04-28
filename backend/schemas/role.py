from orm import ORMBase


class RoleBase(ORMBase):
    role_type: str


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase):
    id: int
    user_id: int
