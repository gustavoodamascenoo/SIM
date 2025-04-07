from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, DiarioManutencao, Equipment
from forms import DiarioManutencaoForm
import os
import io
from datetime import datetime

# Criação do Blueprint para o Diário de Manutenção
diario_bp = Blueprint('diario', __name__, url_prefix='/diario')

@diario_bp.route('/')
@login_required
def index():
    """Exibe lista de todas as entradas do Diário de Manutenção"""
    # Obter todos os registros, ordenados por data (mais recentes primeiro)
    registros = DiarioManutencao.query.order_by(DiarioManutencao.data_criacao.desc()).all()
    return render_template('diario/index.html', registros=registros)

@diario_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    """Adicionar nova entrada no Diário de Manutenção"""
    form = DiarioManutencaoForm()
    
    # Preencher as opções de equipamentos
    form.equipment_id.choices = [(0, 'Nenhum')] + [(e.id, f"{e.identification_number} - {e.model}") 
                                for e in Equipment.query.all()]
    
    if form.validate_on_submit():
        try:
            # Criar nova entrada no diário
            diario = DiarioManutencao(
                user_id=current_user.id,
                titulo=form.titulo.data,
                conteudo=form.conteudo.data,
                data_criacao=datetime.utcnow()
            )
            
            # Verificar se um equipamento foi selecionado (e não é a opção "Nenhum")
            if form.equipment_id.data and form.equipment_id.data > 0:
                diario.equipment_id = form.equipment_id.data
            
            # Processar o arquivo anexado, se houver
            if form.arquivo.data:
                arquivo = form.arquivo.data
                # Salvar informações do arquivo
                diario.arquivo_nome = secure_filename(arquivo.filename)
                diario.arquivo_tipo = arquivo.content_type
                diario.arquivo_dados = arquivo.read()  # Ler os dados binários do arquivo
            
            # Salvar no banco de dados
            db.session.add(diario)
            db.session.commit()
            
            flash('Registro adicionado ao Diário de Manutenção com sucesso!', 'success')
            return redirect(url_for('diario.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar registro: {str(e)}', 'danger')
            print(f"Erro ao salvar registro no diário: {str(e)}")
    
    return render_template('diario/adicionar.html', form=form)

@diario_bp.route('/<int:registro_id>')
@login_required
def visualizar(registro_id):
    """Visualizar detalhes de uma entrada no Diário de Manutenção"""
    registro = DiarioManutencao.query.get_or_404(registro_id)
    return render_template('diario/visualizar.html', registro=registro)

@diario_bp.route('/<int:registro_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(registro_id):
    """Editar uma entrada no Diário de Manutenção"""
    registro = DiarioManutencao.query.get_or_404(registro_id)
    
    # Verificar permissão (apenas o autor ou administrador pode editar)
    if registro.user_id != current_user.id and not current_user.is_admin():
        flash('Você não tem permissão para editar este registro.', 'danger')
        return redirect(url_for('diario.index'))
    
    form = DiarioManutencaoForm(obj=registro)
    
    # Preencher as opções de equipamentos
    form.equipment_id.choices = [(0, 'Nenhum')] + [(e.id, f"{e.identification_number} - {e.model}") 
                                for e in Equipment.query.all()]
    
    if form.validate_on_submit():
        try:
            # Atualizar os dados do registro
            registro.titulo = form.titulo.data
            registro.conteudo = form.conteudo.data
            
            # Verificar se um equipamento foi selecionado (e não é a opção "Nenhum")
            if form.equipment_id.data and form.equipment_id.data > 0:
                registro.equipment_id = form.equipment_id.data
            else:
                registro.equipment_id = None
            
            # Processar o arquivo anexado, se houver um novo
            if form.arquivo.data:
                arquivo = form.arquivo.data
                # Salvar informações do arquivo
                registro.arquivo_nome = secure_filename(arquivo.filename)
                registro.arquivo_tipo = arquivo.content_type
                registro.arquivo_dados = arquivo.read()  # Ler os dados binários do arquivo
            
            # Salvar no banco de dados
            db.session.commit()
            
            flash('Registro do Diário de Manutenção atualizado com sucesso!', 'success')
            return redirect(url_for('diario.visualizar', registro_id=registro.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar registro: {str(e)}', 'danger')
            print(f"Erro ao atualizar registro no diário: {str(e)}")
    
    return render_template('diario/editar.html', form=form, registro=registro)

@diario_bp.route('/<int:registro_id>/excluir', methods=['POST'])
@login_required
def excluir(registro_id):
    """Excluir uma entrada do Diário de Manutenção"""
    registro = DiarioManutencao.query.get_or_404(registro_id)
    
    # Verificar permissão (apenas o autor ou administrador pode excluir)
    if registro.user_id != current_user.id and not current_user.is_admin():
        flash('Você não tem permissão para excluir este registro.', 'danger')
        return redirect(url_for('diario.index'))
    
    try:
        db.session.delete(registro)
        db.session.commit()
        flash('Registro excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir registro: {str(e)}', 'danger')
    
    return redirect(url_for('diario.index'))

@diario_bp.route('/<int:registro_id>/arquivo')
@login_required
def baixar_arquivo(registro_id):
    """Baixar o arquivo anexado a uma entrada do Diário de Manutenção"""
    registro = DiarioManutencao.query.get_or_404(registro_id)
    
    # Verificar se existe um arquivo
    if not registro.arquivo_dados:
        flash('Este registro não possui arquivo anexado.', 'warning')
        return redirect(url_for('diario.visualizar', registro_id=registro.id))
    
    # Retornar o arquivo como um stream
    return send_file(
        io.BytesIO(registro.arquivo_dados),
        mimetype=registro.arquivo_tipo,
        as_attachment=True,
        download_name=registro.arquivo_nome or 'anexo.bin'
    )