
from app import app, db
from sqlalchemy import text

def migrate_db():
    with app.app_context():
        # Adicionar colunas à tabela checklist_results
        db.session.execute(text("""
            ALTER TABLE checklist_results 
            ADD COLUMN IF NOT EXISTS arquivo_nome VARCHAR(255),
            ADD COLUMN IF NOT EXISTS arquivo_dados BYTEA,
            ADD COLUMN IF NOT EXISTS arquivo_tipo VARCHAR(100)
        """))
        db.session.commit()
        print("Migração concluída com sucesso!")

if __name__ == '__main__':
    migrate_db()
