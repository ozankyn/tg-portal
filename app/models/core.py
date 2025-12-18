# -*- coding: utf-8 -*-
"""
TG Portal - Core Models (User, Role, Permission)
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from app.models.base import TimestampMixin, SoftDeleteMixin


# Many-to-Many: User <-> Role
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

# Many-to-Many: Role <-> Permission
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)


class User(db.Model, UserMixin, TimestampMixin, SoftDeleteMixin):
    """Kullanıcı modeli"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Profil
    ad = db.Column(db.String(50), nullable=False)
    soyad = db.Column(db.String(50), nullable=False)
    telefon = db.Column(db.String(20))
    avatar = db.Column(db.String(255))
    
    # Durum
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    
    # İlişkiler
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))
    
    # Çalışan ile ilişki (opsiyonel)
    calisan_id = db.Column(db.Integer, db.ForeignKey('calisanlar.id'), nullable=True)
    calisan = db.relationship('Calisan', backref='user_account', foreign_keys=[calisan_id])
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    @property
    def full_name(self):
        return f'{self.ad} {self.soyad}'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission_code):
        """Kullanıcının belirli bir yetkisi var mı kontrol eder"""
        if self.is_admin:
            return True
        for role in self.roles:
            for perm in role.permissions:
                # Wildcard desteği: filo.* tüm filo yetkilerini kapsar
                if perm.code == permission_code:
                    return True
                if perm.code.endswith('.*'):
                    module = perm.code[:-2]
                    if permission_code.startswith(module + '.'):
                        return True
                if perm.code == '*':  # Full access
                    return True
        return False
    
    def has_module_access(self, module):
        """Kullanıcının modüle erişimi var mı"""
        if self.is_admin:
            return True
        return self.has_permission(f'{module}.view') or self.has_permission(f'{module}.*')
    
    def get_permissions(self):
        """Kullanıcının tüm yetkilerini döndürür"""
        if self.is_admin:
            return ['*']
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(perm.code)
        return list(perms)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'ad': self.ad,
            'soyad': self.soyad,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'roles': [r.name for r in self.roles],
            'permissions': self.get_permissions()
        }


class Role(db.Model, TimestampMixin):
    """Rol modeli"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_system = db.Column(db.Boolean, default=False)  # Sistem rolleri silinemez
    
    # İlişkiler
    permissions = db.relationship('Permission', secondary=role_permissions, 
                                  backref=db.backref('roles', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'permissions': [p.code for p in self.permissions]
        }


class Permission(db.Model, TimestampMixin):
    """Yetki modeli"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # örn: tedarikci.create
    name = db.Column(db.String(100))  # Görünen ad
    description = db.Column(db.Text)
    module = db.Column(db.String(50))  # Modül adı: tedarikci, filo, ik vs.
    
    def __repr__(self):
        return f'<Permission {self.code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'module': self.module
        }


class AuditLog(db.Model, TimestampMixin):
    """Audit log modeli - tüm değişiklikleri kaydeder"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50))  # create, update, delete, login, logout
    table_name = db.Column(db.String(100))
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} {self.table_name}:{self.record_id}>'
