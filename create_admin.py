import os
import sys
from app import app, db
from models import User, UserRole

def create_admin():
    """Cria um novo usuário administrador"""
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin123'
    first_name = 'Administrador'
    last_name = 'Sistema'
    
    # Verificar se já existe um usuário admin
    with app.app_context():
        existing_admin = User.query.filter_by(username=username).first()
        if existing_admin:
            print(f"Administrador já existe: {username}")
            return
        
        # Criar novo usuário administrador
        admin = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN.value
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        print(f"Administrador criado com sucesso! Username: {username}, Senha: {password}")

if __name__ == '__main__':
    create_admin()