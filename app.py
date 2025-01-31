import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import json
import plotly.graph_objects as go
import os

# Configuration de la page
st.set_page_config(
    page_title="Suivi d'Entraînement",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Programme d'entraînement
WORKOUT_PROGRAM = {
    'PUSH (Lundi)': {
        'echauffement': ['Tapis (5 min)', 'Élastique'],
        'exercices': [
            'Pec deck - 2 séries',
            'Développé couché - 4 séries',
            'Développé incliné - 4 séries',
            'Développé militaire - 4 séries',
            'Extension triceps poulie haute - 3 séries',
            'Extension triceps overhead - 3 séries'
        ],
        'finisher': 'Gainage (1 min)'
    },
    'PULL (Mercredi)': {
        'echauffement': ['Tapis (5 min)', 'Élastique'],
        'exercices': [
            'Tirage vertical - 4 séries',
            'Rowing barre - 4 séries',
            'Rowing un bras - 3 séries',
            'Curl biceps barre - 3 séries',
            'Curl biceps pupitre - 3 séries',
            'Curl marteau - 3 séries'
        ],
        'finisher': 'Planche (1 min)'
    },
    'LEGS (Vendredi)': {
        'echauffement': ['Tapis (5 min)', 'Mobilité hanches', 'Mobilité cheville'],
        'exercices': [
            'Squat - 4 séries',
            'Presse - 4 séries',
            'Leg extension - 3 séries',
            'Leg curl - 3 séries',
            'Mollets debout - 3 séries',
            'Mollets assis - 3 séries'
        ],
        'finisher': 'Corde à sauter (2 min)'
    }
}

# Initialisation de la base de données
def init_database():
    conn = sqlite3.connect('workout.db')
    c = conn.cursor()
    
    # Table des sessions
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT NOT NULL,
                  type TEXT NOT NULL)''')
    
    # Table des exercices
    c.execute('''CREATE TABLE IF NOT EXISTS exercises
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER,
                  name TEXT NOT NULL,
                  sets INTEGER,
                  reps INTEGER,
                  weight REAL,
                  FOREIGN KEY (session_id) REFERENCES sessions(id))''')
    
    # Table des échauffements
    c.execute('''CREATE TABLE IF NOT EXISTS warmups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER,
                  name TEXT NOT NULL,
                  duration INTEGER,
                  FOREIGN KEY (session_id) REFERENCES sessions(id))''')
    
    # Table des finishers
    c.execute('''CREATE TABLE IF NOT EXISTS finishers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER,
                  name TEXT NOT NULL,
                  duration INTEGER,
                  FOREIGN KEY (session_id) REFERENCES sessions(id))''')
    
    conn.commit()
    conn.close()

# Initialisation de la base de données au démarrage
init_database()

# Fonction pour sauvegarder une session
def save_session(session_type, exercises_data, warmup_data, finisher_data):
    conn = sqlite3.connect('workout.db')
    c = conn.cursor()
    
    # Insérer la session
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO sessions (date, type) VALUES (?, ?)',
              (current_date, session_type))
    session_id = c.lastrowid
    
    # Insérer les exercices
    for exercise in exercises_data:
        c.execute('''INSERT INTO exercises (session_id, name, sets, reps, weight)
                     VALUES (?, ?, ?, ?, ?)''',
                  (session_id, exercise['name'], exercise['sets'],
                   exercise['reps'], exercise['weight']))
    
    # Insérer les échauffements
    for warmup in warmup_data:
        c.execute('''INSERT INTO warmups (session_id, name, duration)
                     VALUES (?, ?, ?)''',
                  (session_id, warmup['name'], warmup.get('duration', 0)))
    
    # Insérer le finisher
    if finisher_data:
        c.execute('''INSERT INTO finishers (session_id, name, duration)
                     VALUES (?, ?, ?)''',
                  (session_id, finisher_data['name'], finisher_data['duration']))
    
    conn.commit()
    conn.close()
    return session_id

# Fonction pour récupérer l'historique des sessions
def get_sessions_history(days_filter=30, session_type=None):
    conn = sqlite3.connect('workout.db')
    c = conn.cursor()
    
    # Construire la requête SQL de base
    query = '''
    SELECT 
        s.id,
        s.date,
        s.type,
        GROUP_CONCAT(DISTINCT w.name || ' (' || w.duration || ' min)') as warmups,
        GROUP_CONCAT(DISTINCT e.name || ' - ' || e.sets || 'x' || e.reps || ' @ ' || e.weight || 'kg') as exercises,
        GROUP_CONCAT(DISTINCT f.name || ' (' || f.duration || ' min)') as finishers
    FROM sessions s
    LEFT JOIN warmups w ON s.id = w.session_id
    LEFT JOIN exercises e ON s.id = e.session_id
    LEFT JOIN finishers f ON s.id = f.session_id
    '''
    
    # Ajouter les conditions de filtrage
    conditions = []
    params = []
    
    if days_filter:
        conditions.append("date('now', '-' || ? || ' days') <= date(s.date)")
        params.append(days_filter)
    
    if session_type:
        conditions.append("s.type = ?")
        params.append(session_type)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " GROUP BY s.id ORDER BY s.date DESC"
    
    # Exécuter la requête
    c.execute(query, params)
    results = c.fetchall()
    
    # Convertir les résultats en liste de dictionnaires
    sessions = []
    for row in results:
        session = {
            'id': row[0],
            'date': row[1],
            'type': row[2],
            'warmups': row[3].split(',') if row[3] else [],
            'exercises': row[4].split(',') if row[4] else [],
            'finishers': row[5].split(',') if row[5] else []
        }
        sessions.append(session)
    
    conn.close()
    return sessions

# Fonction pour récupérer le poids maximum pour un exercice
def get_exercise_max_weight(exercise_name):
    conn = sqlite3.connect('workout.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT e.weight, e.reps, s.date
        FROM exercises e
        JOIN sessions s ON e.session_id = s.id
        WHERE e.name = ?
        ORDER BY e.weight DESC, s.date DESC
        LIMIT 1
    ''', (exercise_name,))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'weight': result[0],
            'reps': result[1],
            'date': result[2]
        }
    return None

# Onglets principaux
tab_workout, tab_history = st.tabs([" Entraînement", " Historique"])

with tab_workout:
    st.title("Nouvelle Séance")
    
    # Sélection de la séance
    session_type = st.selectbox(
        "Type de séance",
        list(WORKOUT_PROGRAM.keys())
    )
    
    # Bouton pour commencer l'entraînement
    if not st.session_state.get('workout_started', False):
        if st.button("Commencer l'entraînement"):
            st.session_state['workout_started'] = True
            st.session_state['current_workout'] = WORKOUT_PROGRAM[session_type]
            st.session_state['exercises_data'] = []
            st.session_state['warmup_data'] = []
            st.session_state['finisher_data'] = None
            st.session_state['series_count'] = {}
            
            # Initialiser le compteur de séries pour chaque exercice
            for exercise in WORKOUT_PROGRAM[session_type]['exercices']:
                exercise_name = exercise.split(' - ')[0]
                num_sets = int(exercise.split(' - ')[1].split()[0])
                st.session_state['series_count'][exercise_name] = num_sets
            
            st.experimental_rerun()
    
    # Affichage de l'entraînement
    if st.session_state.get('workout_started', False):
        workout = st.session_state['current_workout']
        
        # Suivi de l'échauffement
        st.subheader("Échauffement")
        with st.expander("Échauffement", expanded=True):
            warmup_data = []
            for warmup in workout['echauffement']:
                st.markdown(f"**{warmup}**")
                if '(' in warmup:
                    default_time = int(warmup.split('(')[1].split()[0])
                    duration = st.number_input(f"Durée {warmup}", 
                                            min_value=1,
                                            value=default_time,
                                            step=1,
                                            key=f"warmup_{warmup}")
                    warmup_data.append({
                        'name': warmup,
                        'duration': duration
                    })
                else:
                    warmup_data.append({
                        'name': warmup,
                        'duration': 0
                    })
            st.session_state['warmup_data'] = warmup_data
        
        # Suivi des exercices
        st.subheader("Exercices")
        exercises_data = []
        
        for idx, exercise in enumerate(workout['exercices'], 1):
            exercise_name = exercise.split(' - ')[0]
            num_sets = int(exercise.split(' - ')[1].split()[0])
            
            # Créer un style CSS personnalisé pour le titre de l'exercice
            st.markdown(
                f"""
                <div style="
                    background-color: #1E1E1E;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                ">
                    <h3 style="margin: 0; color: white;">{idx}. {exercise_name}</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            with st.expander("", expanded=True):
                # Afficher le poids max historique en haut de l'exercice
                max_data = get_exercise_max_weight(exercise_name)
                if max_data:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #2E2E2E;
                            padding: 5px;
                            border-radius: 3px;
                            margin: 5px 0;
                        ">
                            <p style="margin: 0; color: #FFD700;">
                                Record: {max_data['weight']}kg × {max_data['reps']} reps 
                                ({datetime.strptime(max_data['date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')})
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                exercise_sets = []
                
                for set_num in range(1, st.session_state.series_count[exercise_name] + 1):
                    st.markdown(f"**Série {set_num}**")
                    
                    # Vérifier si cette série a déjà été validée
                    set_data = None
                    if 'exercises_data' in st.session_state:
                        for ex in st.session_state['exercises_data']:
                            if ex['name'] == exercise_name and ex['set'] == set_num:
                                set_data = ex
                                break
                    
                    # Afficher les champs de saisie
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        weight = st.number_input('Poids (kg)',
                                               min_value=0.0,
                                               value=float(set_data['weight']) if set_data else 0.0,
                                               step=0.5,
                                               key=f"{exercise_name}_weight_{set_num}")
                    with col2:
                        reps = st.number_input('Répétitions',
                                             min_value=0,
                                             value=int(set_data['reps']) if set_data else 0,
                                             step=1,
                                             key=f"{exercise_name}_reps_{set_num}")
                    with col3:
                        if st.button('Valider', key=f"{exercise_name}_validate_{set_num}"):
                            exercise_sets.append({
                                'set': set_num,
                                'weight': weight,
                                'reps': reps
                            })
                            
                            # Mettre à jour exercises_data dans la session
                            if 'exercises_data' not in st.session_state:
                                st.session_state['exercises_data'] = []
                            
                            # Supprimer l'ancienne entrée si elle existe
                            st.session_state['exercises_data'] = [
                                ex for ex in st.session_state['exercises_data']
                                if not (ex['name'] == exercise_name and ex['set'] == set_num)
                            ]
                            
                            # Ajouter la nouvelle entrée
                            st.session_state['exercises_data'].append({
                                'name': exercise_name,
                                'set': set_num,
                                'weight': weight,
                                'reps': reps
                            })
                            
                            st.success(f'Série {set_num} validée!')
                            
                if exercise_sets:
                    exercises_data.append({
                        'name': exercise_name,
                        'sets': len(exercise_sets),
                        'reps': exercise_sets[-1]['reps'],
                        'weight': exercise_sets[-1]['weight']
                    })
        
        # Suivi du finisher
        st.subheader("Finisher")
        with st.expander(f" {workout['finisher']}", expanded=True):
            default_time = int(workout['finisher'].split('(')[1].split()[0]) if '(' in workout['finisher'] else 20
            finisher_duration = st.number_input(f"Durée (minutes)", 
                                              min_value=1,
                                              value=default_time,
                                              step=1,
                                              key="finisher_duration")
            
            if st.button("Valider le finisher"):
                st.session_state['finisher_data'] = {
                    'name': workout['finisher'],
                    'duration': finisher_duration
                }
                st.success('Finisher validé!')
        
        # Bouton pour terminer la séance
        if st.button("Terminer la séance"):
            if st.session_state.get('exercises_data'):
                # Préparer les données des exercices
                exercises_summary = []
                exercise_counts = {}
                
                for exercise in st.session_state['exercises_data']:
                    name = exercise['name']
                    if name not in exercise_counts:
                        exercise_counts[name] = {
                            'name': name,
                            'sets': 0,
                            'reps': exercise['reps'],
                            'weight': exercise['weight']
                        }
                    exercise_counts[name]['sets'] += 1
                
                exercises_summary = list(exercise_counts.values())
                
                # Sauvegarder la session
                save_session(
                    session_type,
                    exercises_summary,
                    st.session_state['warmup_data'],
                    st.session_state['finisher_data']
                )
                
                # Réinitialiser l'état
                st.session_state['workout_started'] = False
                st.session_state['current_workout'] = None
                st.session_state['exercises_data'] = []
                st.session_state['warmup_data'] = []
                st.session_state['finisher_data'] = None
                st.session_state['series_count'] = {}
                
                st.success('Session sauvegardée avec succès!')
                st.experimental_rerun()
            else:
                st.error('Aucun exercice n\'a été validé!')

with tab_history:
    st.title("Historique des Séances")
    
    # Filtres
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        days_filter = st.selectbox(
            "Période",
            [7, 30, 90, 180, 365, None],
            format_func=lambda x: "Tout" if x is None else f"Derniers {x} jours",
            index=1  # 30 jours par défaut
        )
    
    with col_filter2:
        session_type_filter = st.selectbox(
            "Type de séance",
            ["Toutes"] + list(WORKOUT_PROGRAM.keys()),
            format_func=lambda x: x if x != "Toutes" else "Toutes les séances"
        )
    
    # Récupérer l'historique filtré
    history = get_sessions_history(
        days_filter=days_filter,
        session_type=None if session_type_filter == "Toutes" else session_type_filter
    )
    
    # Afficher l'historique
    if history:
        for session in history:
            with st.expander(f"{session['type']} - {datetime.strptime(session['date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')}"):
                # Échauffement
                if session['warmups']:
                    st.markdown("**Échauffement:**")
                    for warmup in session['warmups']:
                        st.markdown(f"- {warmup}")
                
                # Exercices
                if session['exercises']:
                    st.markdown("**Exercices:**")
                    for exercise in session['exercises']:
                        st.markdown(f"- {exercise}")
                
                # Finisher
                if session['finishers']:
                    st.markdown("**Finisher:**")
                    for finisher in session['finishers']:
                        st.markdown(f"- {finisher}")
    else:
        st.info("Aucune séance trouvée pour les filtres sélectionnés.")
