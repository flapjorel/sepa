import streamlit as st
import sqlite3
import random
from collections import defaultdict
from datetime import date, timedelta

# --------------------
# Banco de dados
# --------------------
conn = sqlite3.connect("alunos.db")
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                disponibilidade TEXT NOT NULL
            )""")
conn.commit()

# --------------------
# Funções auxiliares
# --------------------
DAYS = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
SHIFTS = ["Manhã","Tarde","Noite"]

def salvar_aluno(nome, disp):
    disp_str = ";".join([f"{d}-{s}" for d,s in disp])
    c.execute("INSERT INTO alunos (nome, disponibilidade) VALUES (?,?)", (nome, disp_str))
    conn.commit()

def listar_alunos():
    c.execute("SELECT * FROM alunos")
    return c.fetchall()

def deletar_aluno(aluno_id):
    c.execute("DELETE FROM alunos WHERE id=?", (aluno_id,))
    conn.commit()

def atualizar_aluno(aluno_id, nome, disp):
    disp_str = ";".join([f"{d}-{s}" for d,s in disp])
    c.execute("UPDATE alunos SET nome=?, disponibilidade=? WHERE id=?", (nome, disp_str, aluno_id))
    conn.commit()

def gerar_escala(alunos, week_start):
    assignments = {(d,s): [] for d in range(7) for s in range(3)}
    student_count = defaultdict(int)
    max_per_week = 3          # máximo de turnos por aluno/semana
    vacancies_per_shift = 4   # até 4 alunos por turno

    for day in range(7):
        for shift in range(3):
            # Regra: sábado (day=5) só tem manhã (shift=0)
            if day == 5 and shift > 0:
                continue

            candidates = [
                a for a in alunos 
                if f"{day}-{shift}" in a["disp"] and student_count[a["nome"]] < max_per_week
            ]
            random.shuffle(candidates)
            for _ in range(vacancies_per_shift):
                if not candidates: break
                chosen = candidates.pop()
                assignments[(day,shift)].append(chosen["nome"])
                student_count[chosen["nome"]] += 1
    return assignments

# --------------------
# Interface Streamlit
# --------------------
st.title("📅 Sistema de Escalas Semanais")

menu = st.sidebar.radio("Menu", ["Cadastrar Aluno","Gerenciar Alunos","Gerar Escala"])

if menu == "Cadastrar Aluno":
    st.header("Cadastrar novo aluno")
    nome = st.text_input("Nome do aluno")
    disponibilidade = []
    for d_idx, d in enumerate(DAYS):
        st.subheader(d)
        for s_idx, s in enumerate(SHIFTS):
            # Regra: sábado (d_idx=5) só tem manhã (s_idx=0)
            if d_idx == 5 and s_idx > 0:
                continue
            if st.checkbox(f"{d} - {s}", key=f"{d}-{s}"):
                disponibilidade.append((d_idx,s_idx))
    if st.button("Salvar"):
        if nome and disponibilidade:
            salvar_aluno(nome, disponibilidade)
            st.success("Aluno salvo com sucesso!")

elif menu == "Gerenciar Alunos":
    st.header("Lista de alunos")
    alunos = listar_alunos()
    for aluno in alunos:
        aid, nome, disp = aluno
        st.write(f"**{nome}** - Disponibilidade: {disp}")
        col1, col2 = st.columns(2)
        if col1.button("Editar", key=f"edit{aid}"):
            novo_nome = st.text_input("Novo nome", value=nome, key=f"nome{aid}")
            nova_disp = []
            for d_idx, d in enumerate(DAYS):
                for s_idx, s in enumerate(SHIFTS):
                    # Regra: sábado só manhã
                    if d_idx == 5 and s_idx > 0:
                        continue
                    marcado = f"{d_idx}-{s_idx}" in disp.split(";")
                    if st.checkbox(f"{d} - {s}", key=f"edit{aid}-{d}-{s}", value=marcado):
                        nova_disp.append((d_idx,s_idx))
            if st.button("Salvar alterações", key=f"save{aid}"):
                atualizar_aluno(aid, novo_nome, nova_disp)
                st.success("Aluno atualizado! Recarregue a página.")
        if col2.button("Excluir", key=f"del{aid}"):
            deletar_aluno(aid)
            st.warning("Aluno excluído! Recarregue a página.")

elif menu == "Gerar Escala":
    st.header("Gerar escala semanal")
    alunos_db = listar_alunos()
    alunos = []
    for aid, nome, disp in alunos_db:
        alunos.append({"nome": nome, "disp": disp.split(";")})
    if alunos:
        week_start = date.today()
        escala = gerar_escala(alunos, week_start)
        for day in range(7):
            day_date = week_start + timedelta(days=day)
            st.subheader(f"{DAYS[day]} ({day_date})")
            for shift in range(3):
                # Regra: sábado só manhã
                if day == 5 and shift > 0:
                    continue
                st.write(f"- {SHIFTS[shift]}: {', '.join(escala[(day,shift)]) or '---'}")
    else:
        st.info("Nenhum aluno cadastrado ainda.")
