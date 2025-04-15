# popular_banco.py
from app import app, db
from models import Equipment, User, MaintenancePlan, ChecklistTemplate, ChecklistItem, MaintenanceSchedule, MaintenanceRecord, Notification, DiarioManutencao
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random

with app.app_context():
    # Limpa e recria todas as tabelas (cuidado: isso apaga tudo)
    db.drop_all()
    db.create_all()

    # === Usuários ===
    usuarios = [
        User(username="admin", email="admin@empresa.com", first_name="Admin", last_name="User", phone="(00) 0000-0000", role="admin", password_hash=generate_password_hash("admin123")),
        User(username="carlos", email="carlos@empresa.com", first_name="Carlos", last_name="Silva", phone="(61) 98765-4321", role="supervisor", password_hash=generate_password_hash("123456")),
        User(username="joao", email="joao@empresa.com", first_name="João", last_name="Santos", phone="(61) 91234-5678", role="technician", password_hash=generate_password_hash("123456")),
        User(username="ana", email="ana@empresa.com", first_name="Ana", last_name="Pereira", phone="(61) 92345-6789", role="technician", password_hash=generate_password_hash("123456")),
    ]
    db.session.add_all(usuarios)

    # === Equipamentos ===
    equipamentos = [
        Equipment(identification_number="CH-001", model="RTWD 150", manufacturer="Trane", power=180, installation_date=datetime(2023, 6, 1), location_building="Sede", location_floor=1, location_room="CAG", location_details="Sala de máquinas", serial_number="CH001-TRANE", warranty_end_date=datetime(2025, 6, 1), status="active"),
        Equipment(identification_number="CH-002", model="RTWD 150", manufacturer="Trane", power=180, installation_date=datetime(2023, 6, 2), location_building="Sede", location_floor=1, location_room="CAG", location_details="Sala de máquinas", serial_number="CH002-TRANE", warranty_end_date=datetime(2025, 6, 2), status="active"),
        Equipment(identification_number="FCP-001", model="CyberAir 3PRO DX", manufacturer="Stulz", power=32.5, installation_date=datetime(2023, 5, 10), location_building="Sede", location_floor=3, location_room="CPD", location_details="Corredor frio", serial_number="FCP001-STULZ", warranty_end_date=datetime(2025, 5, 10), status="active"),
        Equipment(identification_number="SC-001", model="Millennium MAXA", manufacturer="Hitachi", power=120, installation_date=datetime(2022, 3, 18), location_building="Sede", location_floor=1, location_room="Auditório", location_details="Teto técnico", serial_number="SC001-HITACHI", warranty_end_date=datetime(2024, 3, 18), status="active"),
        Equipment(identification_number="VRF-001", model="Multi V 5", manufacturer="LG", power=90, installation_date=datetime(2023, 1, 25), location_building="Sede", location_floor=5, location_room="Diretoria", location_details="Cobertura técnica", serial_number="VRF001-LG", warranty_end_date=datetime(2025, 1, 25), status="active"),
        Equipment(identification_number="FCP-002", model="InRow RP DX", manufacturer="APC", power=28.7, installation_date=datetime(2023, 8, 20), location_building="Sede", location_floor=3, location_room="CPD", location_details="Rack 15-18", serial_number="FCP002-APC", warranty_end_date=datetime(2025, 8, 20), status="active"),
        Equipment(identification_number="FCP-003", model="InRow RP DX", manufacturer="APC", power=28.7, installation_date=datetime(2023, 8, 21), location_building="Sede", location_floor=3, location_room="CPD", location_details="Rack 25-28", serial_number="FCP003-APC", warranty_end_date=datetime(2025, 8, 21), status="active"),
        Equipment(identification_number="FCP-004", model="Precision AC P2020", manufacturer="Vertiv", power=35.0, installation_date=datetime(2022, 11, 5), location_building="Sede", location_floor=2, location_room="Telecom", location_details="Parede leste", serial_number="FCP004-VERTIV", warranty_end_date=datetime(2024, 11, 5), status="active"),
        Equipment(identification_number="FC-001", model="VFAS 2500", manufacturer="Carrier", power=15.0, installation_date=datetime(2023, 2, 10), location_building="Sede", location_floor=1, location_room="Atendimento", location_details="Teto técnico", serial_number="FC001-CARRIER", warranty_end_date=datetime(2025, 2, 10), status="active"),
        Equipment(identification_number="FC-002", model="VFAS 1800", manufacturer="Carrier", power=12.5, installation_date=datetime(2023, 2, 10), location_building="Sede", location_floor=2, location_room="Escritórios A", location_details="Teto técnico", serial_number="FC002-CARRIER", warranty_end_date=datetime(2025, 2, 10), status="active"),
    ]
    db.session.add_all(equipamentos)
    db.session.commit()

    # === Planos e Checklists ===
    planos = [
        MaintenancePlan(equipment_id=i.id, name=f"Plano Equipamento {i.identification_number}", description="Plano preventivo mensal", frequency_days=30)
        for i in equipamentos
    ]
    db.session.add_all(planos)
    db.session.commit()

    checklists = []
    itens_checklist = [
        "Verificar nível de óleo",
        "Verificar pressão do compressor",
        "Inspecionar vazamentos",
        "Checar temperatura de saída",
        "Verificar corrente elétrica",
        "Limpeza dos filtros",
        "Lubrificar partes móveis",
        "Verificar ruídos anormais",
        "Verificar sistema de drenagem",
        "Verificar painel de controle"
    ]

    for plano in planos:
        template = ChecklistTemplate(
            maintenance_plan_id=plano.id,
            name=f"Checklist {plano.name}",
            description=f"Checklist completo para {plano.name}"
        )
        db.session.add(template)
        db.session.commit()
        for i, item in enumerate(itens_checklist, 1):
            checklists.append(ChecklistItem(template_id=template.id, description=item, is_required=True, order=i))

    db.session.add_all(checklists)
    db.session.commit()

    # === Agendamentos ===
    agendamento = MaintenanceSchedule(
        equipment_id=1,
        maintenance_plan_id=planos[0].id,
        scheduled_date=datetime.now() + timedelta(days=2),
        status="scheduled",
        notes="Manutenção mensal do Chiller"
    )
    db.session.add(agendamento)
    db.session.commit()

    # === Registro de manutenção realizada ===
    registro = MaintenanceRecord(
        equipment_id=1,
        technician_id=3,
        schedule_id=agendamento.id,
        start_time=datetime.now() - timedelta(days=30),
        end_time=datetime.now() - timedelta(days=30, hours=-2),
        status="completed",
        notes="Manutenção completa",
        issues_found="Nenhum problema encontrado.",
        actions_taken="Rotina preventiva executada com sucesso."
    )
    db.session.add(registro)

    # === Notificações ===
    notificacao = Notification(
        user_id=3,
        schedule_id=agendamento.id,
        title="Manutenção agendada",
        message="Você tem uma manutenção do Chiller agendada para daqui 2 dias.",
        read=False
    )
    db.session.add(notificacao)

    # === Diário de Manutenção ===
    diarios = []
    for i in range(1, 16):
        diarios.append(DiarioManutencao(
            user_id=random.choice([3, 4]),
            equipment_id=random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
            titulo=f"Registro técnico #{i}",
            conteudo=f"Realizada vistoria técnica no equipamento. Verificação e ajustes padrão. Log #{i:03d}.",
            data_criacao=datetime.now() - timedelta(days=i)
        ))
    db.session.add_all(diarios)

    # Finaliza
    print("Populando banco com dados fictícios...")
    db.session.commit()
    print("Concluído!")
