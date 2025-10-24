import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session

# --- Configuration de l'application Flask ---
app = Flask(__name__)

# La cle secrete est OBLIGATOIRE pour utiliser les sessions (securite)
# Nous la recuperons depuis les variables d'environnement de Render pour plus de securite
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_dev')

# --- Configuration de l'authentification (Recuperation des variables d'environnement (render)) ---
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'mohamed.cyber@hotmail') # Le nom d'utilisateur est stocke sur Render
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'default_password')

# --- Chemin du fichier de donnees JSON (Stockage temporaire) ---
DATA_FILE = 'students.json'

# --- Fonctions de Gestion de Donnees (CRUD - JSON) ---

def get_students_data():
    """
    Lis les donnees des etudiants depuis le fichier JSON.
    Gere les erreurs si le fichier n'existe pas ou s'il est mal formate (vide).
    """
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            # L'encodage 'utf-8' est necessaire pour supporter les accents français
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # En cas d'erreur (fichier non trouve ou vide), retourne une liste vide
        return []

def save_students_data(data):
    """
    enregistre les donnees des etudiants dans le fichier JSON.
    """
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        # indent=4 pour un formatage lisible par l'homme
        # ensure_ascii=False pour afficher les caracteres accentues sans encodage unicode
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Decorateur de Securite ---

def login_required(func):
    """
    Decorateur qui verifie si l'utilisateur est connecte avant d'autoriser l'acces à la route.
    """
    def wrapper(*args, **kwargs):
        # Verifie si la session ne contient pas 'logged_in' ou si la valeur est False
        if 'logged_in' not in session or not session['logged_in']:
            flash("Veuillez vous connecter pour acceder à cette page.", 'error')
            # Redirige vers la page de connexion
            return redirect(url_for('login'))
        
        # Si la connexion est valide, execute la fonction de route originale
        return func(*args, **kwargs)
        
    # Corrige le nom de la fonction pour Flask (pour change le nome de les fonction avec (@login_required) )
    wrapper.__name__ = func.__name__ 
    return wrapper

# --- Routes de l'Application ---

@app.route('/')
def index():
    """
    Affiche la page d'accueil.
    """
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Gere la connexion de l'administrateur.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Verification des identifiants
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True 
            flash('Connexion reussie !', 'success')
            return redirect(url_for('show_students'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
    
    # Affiche la page de connexion (pour la methode GET ou en cas d'echec)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Vous avez ete deconnecte.', 'success')
    return redirect(url_for('index'))

@app.route('/students')
@login_required #  Application du decorateur de securite
def show_students():
    students = get_students_data()
    return render_template('students_table.html', students=students)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Gere l'enregistrement d'un nouvel etudiant.
    """
    students = get_students_data()

    if request.method == 'POST':
        # Recuperation des donnees du formulaire
        new_id = request.form.get('id')
        new_email = request.form.get('email')
        
        # --- Verification d'unicite ---
        id_exists = any(s['id'] == new_id for s in students)
        email_exists = any(s['email'] == new_email for s in students)

        if id_exists:
            flash(f"Erreur : L'ID '{new_id}' est dejà utilise.", 'error')
        elif email_exists:
            flash(f"Erreur : L'Email '{new_email}' est dejà utilise.", 'error')
        else:
            # Creation du nouvel etudiant
            new_student = {
                'id': new_id,
                'name': request.form.get('name'),
                'email': new_email,
                'major': request.form.get('major')
            }
            
            students.append(new_student)
            save_students_data(students)
            
            flash("etudiant enregistre avec succes !", 'success')
            return redirect(url_for('show_students'))

    return render_template('register.html')


@app.route('/edit/<student_id>', methods=['GET', 'POST'])
@login_required #  Route protegee
def edit_student(student_id):
    """
    Affiche et gere la modification des donnees d'un etudiant specifique.
    """
    students = get_students_data()
    
    # Recherche de l'etudiant à modifier
    student = next((s for s in students if s['id'] == student_id), None)

    if student is None:
        flash("Erreur : etudiant non trouve.", 'error')
        return redirect(url_for('show_students'))
    
    if request.method == 'POST':
        new_email = request.form.get('email')
        
        # Verification d'unicite de l'email (doit etre unique sauf pour l'etudiant actuel)
        email_exists = any(s['email'] == new_email and s['id'] != student_id for s in students)

        if email_exists:
            flash(f"Erreur : L'Email '{new_email}' est dejà utilise par un autre etudiant.", 'error')
        else:
            # Mise à jour des donnees
            student['name'] = request.form.get('name')
            student['email'] = new_email
            student['major'] = request.form.get('major')
            
            save_students_data(students)
            flash(f"Donnees de {student['name']} mises à jour avec succes !", 'success')
            return redirect(url_for('show_students'))

    return render_template('edit_student.html', student=student)

@app.route('/delete/<student_id>')
@login_required # Route protegee
def delete_student(student_id):

    students = get_students_data()
    
    # Creation d'une nouvelle liste excluant l'etudiant à supprimer
    initial_length = len(students)
    students = [s for s in students if s['id'] != student_id]
    
    if len(students) < initial_length:
        # Si la longueur a change, l'etudiant a ete supprime
        save_students_data(students)
        flash("etudiant supprime avec succes.", 'success')
    else:
        flash("Erreur : Impossible de trouver l'etudiant à supprimer.", 'error')
        
    return redirect(url_for('show_students'))

# --- Demarrage de l'Application ---
if __name__ == '__main__':
    # Demarre l'application Flask
    app.run(debug=True)