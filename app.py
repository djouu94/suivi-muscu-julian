import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import json
import plotly.graph_objects as go
import os

# Configuration de la page
st.set_page_config(
    page_title="Suivi Muscu",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour le thème sombre et moderne
st.markdown("""
<style>
    /* Thème sombre global */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Style des cartes statistiques */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #333;
    }
    
    /* Style du tableau */
    .dataframe {
        background-color: #1E1E1E;
        color: white;
    }
    
    /* Style des en-têtes de section */
    h1, h2, h3 {
        color: #FAFAFA;
    }
    
    /* Style des liens dans la barre latérale */
    .css-1d391kg {
        padding-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# Programme d'entraînement
WORKOUT_PROGRAM = {
    'PUSH (Lundi)': {
        'echauffement': ['Tapis (5 min)', 'Élastique'],
        'exercices': [
            'Pec deck - 2 séries',
            'Développé couché machine convergente - 3 séries',
            'Biceps corde à la poulie (prise marteau) - 3 séries',
            'Décliné à la machine convergente - 2 séries',
            'Curl biceps unilatéral poulie - 3 séries',
            'Dips - 3 séries',
            'Curl biceps machine - 3 séries',
            'Développé militaire machine - 3 séries',
            'Élévation frontale haltère - 3 séries',
            'Élévation latérale machine - 3 séries'
        ],
        'finisher': 'Tapis (20 min de marche)'
    },
    'PULL (Mardi)': {
        'echauffement': ['Tapis (5 min)', 'Élastique'],
        'exercices': [
            'Tirage vertical - 3 séries',
            'Tirage vertical (prise serrée) - 3 séries',
            'Extension triceps unilatéral poulie haute - 3 séries',
            'Tirage horizontal (coude levé, arrière d\'épaule) - 3 séries',
            'Tirage horizontal (coude collé) - 3 séries',
            'Extension triceps nuque poulie - 3 séries',
            'Extension triceps unilatéral poulie (prise marteau) - 3 séries'
        ],
        'finisher': 'Tapis (20 min de marche)'
    },
    'LEG (Mercredi)': {
        'echauffement': ['Vélo (10 min)', 'Échauffement cheville, genou, hanche'],
        'exercices': [
            'Leg extension unilatéral - 4 séries',
            'Belt squat - 3 séries',
            'Hip thrust - 3 séries',
            'Presse - 3 séries',
            'Abdos - 3 séries',
            'Lombaires - 3 séries'
        ],
        'finisher': 'Tapis (20 min de marche)'
    },
    'PUSH (Jeudi)': {
        'echauffement': ['Tapis (5 min)', 'Élastique'],
        'exercices': [
            'Pec deck - 3 séries',
            'Curl biceps machine - 3 séries',
            'Développé incliné machine convergente - 4 séries',
            'Curl biceps (prise marteau) - 4 séries',
            'Dips - 3 séries',
            'Développé militaire haltères - 3 séries',
            'Élévation frontale haltère - 3 séries',
            'Élévation latérale poulie - 3 séries'
        ],
        'finisher': 'Tapis (20 min de marche)'
    },
    'PULL (Vendredi)': {
        'echauffement': ['Tapis (5 min)', 'Élastique'],
        'exercices': [
            'Tirage vertical unilatéral - 3 séries',
            'Extension triceps unilatéral poulie - 3 séries',
            'Tirage horizontal (prise marteau) - 3 séries',
            'Extension triceps nuque poulie - 3 séries',
            'Oiseau à la machine - 3 séries',
            'Extension triceps à la poulie vis-à-vis - 3 séries'
        ],
        'finisher': 'Tapis (20 min de marche)'
    },
    'LEG (Samedi)': {
        'echauffement': ['Vélo (10 min)', 'Échauffement cheville, genou, hanche'],
        'exercices': [
            'Leg extension - 3 séries',
            'Presse - 3 séries',
            'Fentes - 3 séries',
            'Ischios - 4 séries',
            'Hip thrust - 3 séries',
            'Abdos - 3 séries',
            'Lombaires - 3 séries'
        ],
        'finisher': 'Tapis (20 min de marche)'
    }
}

def init_database():
    conn = sqlite3.connect('workout.db')
    c = conn.cursor()
    
    # Table des sessions
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            type TEXT,
            notes TEXT
        )
    ''')
    
    # Table des exercices
    c.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            name TEXT,
            weight REAL,
            reps INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')
    
    # Table des échauffements
    c.execute('''
        CREATE TABLE IF NOT EXISTS warmups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            activity TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')
    
    # Table des finishers
    c.execute('''
        CREATE TABLE IF NOT EXISTS finishers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            activity TEXT,
            duration INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialisation de la base de données au démarrage
init_database()

def save_session(session_type, exercises_data, warmup_data, finisher_data):
    session_id = None
    try:
        conn = sqlite3.connect('workout.db')
        c = conn.cursor()
        
        # Enregistrer la séance
        c.execute('INSERT INTO sessions (date, type, notes) VALUES (?, ?, ?)',
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), session_type, ''))
        session_id = c.lastrowid
        
        # Enregistrer les activités d'échauffement
        for activity in warmup_data:
            c.execute('''
                INSERT INTO warmups (session_id, activity)
                VALUES (?, ?)
            ''', (session_id, activity['name']))
        
        # Enregistrer les exercices
        for exercise in exercises_data:
            c.execute('''
                INSERT INTO exercises (session_id, name, weight, reps)
                VALUES (?, ?, ?, ?)
            ''', (session_id, exercise['name'], exercise['weight'], exercise['reps']))
        
        # Enregistrer l'activité de finisher
        if finisher_data:
            c.execute('''
                INSERT INTO finishers (session_id, activity, duration)
                VALUES (?, ?, ?)
            ''', (session_id, finisher_data['name'], finisher_data['duration']))
        
        conn.commit()
        return session_id
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement de la séance : {str(e)}")
        return None
    finally:
        conn.close()

def get_sessions_history(days_filter=None, session_type=None):
    try:
        conn = sqlite3.connect('workout.db')
        
        # Construire la requête de base
        query = """
            SELECT 
                s.id,
                s.date,
                s.type,
                GROUP_CONCAT(DISTINCT w.activity) as warmups,
                GROUP_CONCAT(DISTINCT e.name || ' (' || e.weight || 'kg x ' || e.reps || ')') as exercises,
                GROUP_CONCAT(DISTINCT f.activity || ' (' || f.duration || ' min)') as finishers
            FROM sessions s
            LEFT JOIN warmups w ON s.id = w.session_id
            LEFT JOIN exercises e ON s.id = e.session_id
            LEFT JOIN finishers f ON s.id = f.session_id
        """
        
        conditions = []
        params = []
        
        # Ajouter les conditions de filtrage
        if days_filter:
            conditions.append("s.date >= datetime('now', '-' || ? || ' days')")
            params.append(str(days_filter))
        
        if session_type and session_type != "Toutes":
            conditions.append("s.type = ?")
            params.append(session_type)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " GROUP BY s.id, s.date, s.type ORDER BY s.date DESC"
        
        # Exécuter la requête
        df = pd.read_sql_query(query, conn, params=params)
        
        # Convertir les résultats en liste de dictionnaires
        sessions = []
        for _, row in df.iterrows():
            session = {
                'date': row['date'],
                'type': row['type'],
                'warmups': row['warmups'].split(',') if row['warmups'] else [],
                'exercises': row['exercises'].split(',') if row['exercises'] else [],
                'finishers': row['finishers'].split(',') if row['finishers'] else []
            }
            sessions.append(session)
        
        return sessions
        
    except Exception as e:
        st.error(f"Erreur lors de la récupération de l'historique : {str(e)}")
        return []
    finally:
        conn.close()

def get_exercise_max_weight(exercise_name):
    try:
        conn = sqlite3.connect('workout.db')
        # Récupérer le poids max et le nombre de répétitions maximum à ce poids
        query = """
            SELECT weight, MAX(reps) as max_reps
            FROM exercises
            WHERE name = ?
            GROUP BY weight
            ORDER BY weight DESC
            LIMIT 1
        """
        cursor = conn.cursor()
        cursor.execute(query, (exercise_name,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {'max_weight': result[0], 'max_reps': result[1]}
        return None
    except Exception as e:
        st.error(f"Erreur lors de la récupération du poids max : {str(e)}")
        return None

# Barre latérale
with st.sidebar:
    st.title("🏋️ Suivi Muscu")
    
    st.markdown("### 📍 Navigation")
    selected_page = st.radio(
        "",
        ["🏠 Accueil", "💪 Musculation", "🎯 CrossFit", "📊 Historique"],
        label_visibility="collapsed"
    )

# Page principale
if selected_page == "🏠 Accueil":
    st.title("Bienvenue sur ton Suivi Muscu")
    
    # Statistiques rapides
    st.markdown("### 📊 Statistiques Rapides")
    col1, col2, col3 = st.columns(3)
    
    # Récupérer les statistiques depuis la base de données
    conn = sqlite3.connect('workout.db')
    c = conn.cursor()
    
    # Nombre total de séances
    c.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = c.fetchone()[0]
    
    # Nombre total d'exercices effectués
    c.execute("SELECT COUNT(*) FROM exercises")
    total_exercises = c.fetchone()[0]
    
    # Record de poids
    c.execute("SELECT MAX(weight) FROM exercises")
    max_weight = c.fetchone()[0] or 0
    
    with col1:
        st.metric("Nombre total de séances", total_sessions)
    with col2:
        st.metric("Nombre total d'exercices effectués", total_exercises)
    with col3:
        st.metric("Record de poids", f"{max_weight} kg")
    
    # Dernières performances
    st.markdown("### 🎯 Dernières Performances")

    # Récupérer les dernières performances
    try:
        conn = sqlite3.connect('workout.db')
        c = conn.cursor()
        
        c.execute("""
            SELECT exercises.name, exercises.weight, exercises.reps, sessions.date
            FROM exercises
            JOIN sessions ON exercises.session_id = sessions.id
            ORDER BY sessions.date DESC
            LIMIT 10
        """)
        performances = c.fetchall()
        
        # Créer un DataFrame pour afficher les performances
        if performances:
            df = pd.DataFrame(performances, columns=['Exercice', 'Poids (kg)', 'Répétitions', 'Date'])
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%d/%m/%Y')
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucune performance enregistrée pour le moment.")
    
    except sqlite3.Error as e:
        st.error(f"Erreur lors de la récupération des données : {str(e)}")
    finally:
        conn.close()

elif selected_page == "💪 Musculation":
    st.title("Nouvelle Séance")
    
    # Sélection de la séance
    session_type = st.selectbox(
        "Type de séance",
        list(WORKOUT_PROGRAM.keys())
    )
    
    if session_type:
        workout = WORKOUT_PROGRAM[session_type]
        
        # Afficher les détails du programme
        with st.expander("Détails du programme", expanded=True):
            st.subheader("Échauffement")
            for item in workout['echauffement']:
                st.write(f"• {item}")
            
            st.subheader("Exercices")
            for item in workout['exercices']:
                st.write(f"• {item}")
            
            st.subheader("Finisher")
            st.write(f"• {workout['finisher']}")
        
        if not st.session_state.get('workout_started', False):
            if st.button("Commencer la séance"):
                st.session_state['workout_started'] = True
                st.session_state['current_workout'] = WORKOUT_PROGRAM[session_type]
                st.session_state['exercises_data'] = {}  
                st.session_state['warmup_data'] = []
                st.session_state['finisher_data'] = None
                st.session_state['series_count'] = {}
                
                # Initialiser les listes pour chaque exercice
                for exercise in WORKOUT_PROGRAM[session_type]['exercices']:
                    exercise_name = exercise.split(' - ')[0]
                    num_sets = int(exercise.split(' - ')[1].split()[0])
                    st.session_state['series_count'][exercise_name] = num_sets
                    st.session_state['exercises_data'][exercise_name] = []  
                
                st.rerun()
        
        if st.session_state.get('workout_started', False):
            workout = st.session_state['current_workout']
            
            # Suivi de l'échauffement
            st.subheader("Échauffement")
            warmup_data = []
            for activity in workout['echauffement']:
                with st.expander(f" {activity}", expanded=True):
                    default_time = int(activity.split('(')[1].split()[0]) if '(' in activity else 5
                    duration = st.number_input(f"Durée (minutes)", 
                                            min_value=1, 
                                            value=default_time,
                                            key=f"warmup_{activity}")
                    notes = st.text_input("Notes", key=f"warmup_notes_{activity}")
                    warmup_data.append({
                        'name': activity,
                        'duration': duration,
                        'notes': notes
                    })
            
            # Suivi des exercices
            st.subheader("Exercices")
            
            for idx, exercise in enumerate(workout['exercices'], 1):
                exercise_name = exercise.split(' - ')[0]
                num_sets = int(exercise.split(' - ')[1].split()[0])
                
                # Créer un style CSS personnalisé pour le titre de l'exercice
                st.markdown(f"""
                    <div style='
                        background-color: #1E1E1E;
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 5px;
                    '>
                        <h3 style='
                            color: white;
                            margin: 0;
                            font-size: 1.5em;
                        '>
                            Exercice {idx} - {exercise_name} ({num_sets} séries)
                        </h3>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander("", expanded=True):
                    # Afficher le poids max historique en haut de l'exercice
                    max_data = get_exercise_max_weight(exercise_name)
                    if max_data:
                        st.markdown(
                            f"<div style='text-align: right; color: gold;'>Record : {max_data['max_weight']} kg × {max_data['max_reps']} reps</div>",
                            unsafe_allow_html=True
                        )
                    
                    # Boutons pour ajouter/supprimer des séries
                    col_add, col_del = st.columns([1, 1])
                    with col_add:
                        if st.button(f"➕ Ajouter une série", key=f"add_{exercise_name}"):
                            st.session_state.series_count[exercise_name] += 1
                            st.rerun()
                    
                    with col_del:
                        if st.button(f"➖ Supprimer une série", key=f"del_{exercise_name}"):
                            if st.session_state.series_count[exercise_name] > 1:
                                st.session_state.series_count[exercise_name] -= 1
                                if len(st.session_state.exercises_data[exercise_name]) >= st.session_state.series_count[exercise_name]:
                                    st.session_state.exercises_data[exercise_name].pop()
                                st.rerun()
                    
                    # Afficher les séries
                    for set_num in range(1, st.session_state.series_count[exercise_name] + 1):
                        st.markdown(f"**Série {set_num}**")
                        
                        # Créer des clés uniques sans espaces ni caractères spéciaux
                        safe_exercise_name = exercise_name.replace(" ", "_").replace("(", "").replace(")", "").lower()
                        weight_key = f"weight_{safe_exercise_name}_{set_num}"
                        reps_key = f"reps_{safe_exercise_name}_{set_num}"
                        
                        # Vérifier si cette série a déjà été validée
                        set_data = None
                        if exercise_name in st.session_state.exercises_data:
                            if len(st.session_state.exercises_data[exercise_name]) >= set_num:
                                set_data = st.session_state.exercises_data[exercise_name][set_num - 1]
                        
                        # Colonnes pour le poids et les répétitions
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            weight = st.number_input(
                                "Poids (kg)",
                                min_value=0.0,
                                value=float(set_data['weight']) if set_data and set_data.get('weight') else 0.0,
                                step=1.25,
                                key=weight_key
                            )
                        
                        with col2:
                            reps = st.number_input(
                                "Répétitions",
                                min_value=0,
                                value=int(set_data['reps']) if set_data and set_data.get('reps') else 0,
                                step=1,
                                key=reps_key
                            )
                        
                        with col3:
                            validate_key = f"validate_{safe_exercise_name}_{set_num}"
                            if weight > 0 and reps > 0:
                                if st.button("✓", key=validate_key):
                                    # Initialiser la liste si elle n'existe pas
                                    if exercise_name not in st.session_state.exercises_data:
                                        st.session_state.exercises_data[exercise_name] = []
                                    
                                    # S'assurer que la liste a assez d'éléments
                                    while len(st.session_state.exercises_data[exercise_name]) < set_num:
                                        st.session_state.exercises_data[exercise_name].append(None)
                                    
                                    # Mettre à jour la série
                                    st.session_state.exercises_data[exercise_name][set_num - 1] = {
                                        'name': exercise_name,
                                        'weight': weight,
                                        'reps': reps
                                    }
                                    st.rerun()
                    
                    # Afficher les séries validées pour cet exercice
                    if exercise_name in st.session_state.exercises_data:
                        st.markdown("### Séries validées")
                        for idx, set_data in enumerate(st.session_state.exercises_data[exercise_name], 1):
                            if set_data:
                                st.success(f"Série {idx}: {set_data['weight']} kg × {set_data['reps']} reps")

            # Suivi du finisher
            st.subheader("Finisher")
            with st.expander(f" {workout['finisher']}", expanded=True):
                default_time = int(workout['finisher'].split('(')[1].split()[0]) if '(' in workout['finisher'] else 20
                finisher_duration = st.number_input(f"Durée (minutes)", 
                                              min_value=1, 
                                              value=default_time,
                                              key="finisher_duration")
                finisher_notes = st.text_input("Notes", key="finisher_notes")
                finisher_data = {
                    'name': workout['finisher'],
                    'duration': finisher_duration,
                    'notes': finisher_notes
                }
            
            # Bouton de sauvegarde
            if st.button("Sauvegarder la séance"):
                # Rassembler toutes les données validées
                all_exercises_data = []
                for exercise_data in st.session_state.exercises_data.values():
                    all_exercises_data.extend([set_data for set_data in exercise_data if set_data])
                
                if not all_exercises_data:
                    st.error("Aucun exercice n'a été validé. Veuillez valider au moins un exercice avant de sauvegarder.")
                else:
                    session_id = save_session(session_type, all_exercises_data, warmup_data, finisher_data)
                    if session_id:
                        st.success(f"Séance sauvegardée avec succès !")
                        # Réinitialiser tous les états
                        for key in list(st.session_state.keys()):
                            if key in ['series_count', 'exercises_data', 'workout_started']:
                                del st.session_state[key]
                        st.rerun()

elif selected_page == "🎯 CrossFit":
    st.title("CrossFit")
    
    # Sous-onglets CrossFit
    crossfit_tab1, crossfit_tab2, crossfit_tab3 = st.tabs(["📝 WOD", "🏋️ Exercices", "📊 Stats"])
    
    with crossfit_tab1:
        st.header("WOD (Workout of the Day)")
        
        # Type de WOD
        wod_type = st.selectbox(
            "Type de WOD",
            ["AMRAP", "For Time", "EMOM", "Tabata", "Chipper"]
        )
        
        # Configuration du WOD
        col1, col2 = st.columns(2)
        with col1:
            time_cap = st.number_input("Time Cap (minutes)", min_value=1, value=20)
        with col2:
            if wod_type in ["AMRAP", "For Time"]:
                rounds = st.number_input("Rounds", min_value=1, value=1)
        
        # Sélection des exercices
        st.subheader("Exercices")
        
        # TODO: Ajouter la sélection d'exercices depuis la base de données
        
    with crossfit_tab2:
        st.header("Base de données d'exercices")
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        with col1:
            category_filter = st.selectbox(
                "Catégorie",
                ["Tous", "Gymnastique", "Haltérophilie", "Cardio", "Mobilité"]
            )
        with col2:
            skill_filter = st.selectbox(
                "Niveau",
                ["Tous", "Débutant", "Intermédiaire", "Avancé"]
            )
        with col3:
            equipment_filter = st.selectbox(
                "Équipement",
                ["Tous", "Poids du corps", "Barre", "Haltères", "Kettlebell", "Machine"]
            )
        
        # TODO: Afficher les exercices filtrés depuis la base de données
        
    with crossfit_tab3:
        st.header("Statistiques")
        # TODO: Ajouter les statistiques CrossFit

elif selected_page == "📊 Historique":
    st.title("Historique des Séances")
    
    # Filtres
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        days_filter = st.selectbox(
            "Période",
            [7, 30, 90, 180, 365, None],
            format_func=lambda x: "Tout" if x is None else f"Derniers {x} jours",
            index=1
        )
    
    with col_filter2:
        session_type_filter = st.selectbox(
            "Type de séance",
            ["Toutes"] + list(WORKOUT_PROGRAM.keys())
        )
    
    # Récupérer et afficher l'historique
    history = get_sessions_history(
        days_filter=days_filter,
        session_type=None if session_type_filter == "Toutes" else session_type_filter
    )
    
    if history:
        for session in history:
            with st.expander(f"Séance du {session['date']} - {session['type']}"):
                if session['warmups']:
                    st.markdown("**Échauffement:**")
                    for warmup in session['warmups']:
                        st.markdown(f"- {warmup}")
                
                if session['exercises']:
                    st.markdown("**Exercices:**")
                    for exercise in session['exercises']:
                        st.markdown(f"- {exercise}")
                
                if session['finishers']:
                    st.markdown("**Finisher:**")
                    for finisher in session['finishers']:
                        st.markdown(f"- {finisher}")
    else:
        st.info("Aucune séance enregistrée pour le moment.")
