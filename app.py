from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
import os # 💡 للاستيراد من متغيرات البيئة

# --- إعداد التطبيق والبيئة ---
app = Flask(__name__)
# القراءة من متغيرات البيئة (التي ستضيفها في Render)
app.secret_key = os.environ.get('SECRET_KEY', 'votre_cle_secrete_ici_par_defaut') 

# بيانات الدخول يتم قراءتها من متغيرات البيئة في Render
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

# --- وظائف التعامل مع JSON ---
def get_students_data():
    """Lis les données des étudiants depuis le fichier JSON."""
    try:
        with open('students.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # في حالة عدم العثور على الملف، يتم إنشاء ملف فارغ
        return []

def save_students_data(data):
    """Enregistre les données des étudiants dans le fichier JSON."""
    with open('students.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
# ----------------------------------------
# --- مسارات التطبيق (Routes) ---
# ----------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        
        new_id = request.form.get('id')
        new_email = request.form['email']
        all_students = get_students_data()

        # التحقق من تكرار الـ ID والـ Email
        id_exists = any(str(student.get('id')) == new_id for student in all_students)
        email_exists = any(student.get('email') == new_email for student in all_students)
        
        if id_exists:
            flash(f"Erreur : Le Numéro ID '{new_id}' est déjà utilisé.", 'error')
            return redirect(url_for('register'))
            
        if email_exists:
            flash(f"Erreur : L'Email '{new_email}' est déjà utilisé.", 'error')
            return redirect(url_for('register'))

        # الحفظ
        new_student = {
            'id': new_id, 
            'name': request.form['name'],
            'email': new_email,
            'classe': request.form.get('classe', 'Non spécifiée') 
        }
        
        all_students.append(new_student)
        save_students_data(all_students)
        
        flash("Succès : Étudiant enregistré avec succès!", 'success')
        return redirect(url_for('show_students'))

    return render_template('register.html')

# --- مسارات الدخول والحماية ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 💡 التحقق من بيانات الدخول ضد المتغيرات المخزنة في البيئة
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Succès : Connexion réussie!', 'success')
            return redirect(url_for('show_students'))
        else:
            flash('Erreur : Nom d\'utilisateur ou mot de passe incorrect.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Succès : Vous avez été déconnecté.', 'success')
    return redirect(url_for('index'))

# دالة مساعدة للتحقق من تسجيل الدخول
def login_required(func):
    """Decorator to require login for certain routes."""
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash("Veuillez vous connecter pour accéder à cette page.", 'error')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__ 
    return wrapper

# --- المسارات المحمية ---

@app.route('/students')
@login_required # 💡 تطبيق الحماية
def show_students():
    students = get_students_data()
    return render_template('students_table.html', students=students)


@app.route('/delete/<student_id>', methods=['POST'])
@login_required # 💡 تطبيق الحماية
def delete_student(student_id):
    all_students = get_students_data()
    
    updated_students = [student for student in all_students if str(student.get('id')) != student_id]
    
    if len(updated_students) < len(all_students):
        save_students_data(updated_students)
        flash("Succès : Étudiant supprimé avec succès.", 'success')
    else:
        flash("Erreur : Étudiant non trouvé.", 'error')
        
    return redirect(url_for('show_students'))


@app.route('/edit/<student_id>', methods=['GET'])
@login_required # 💡 تطبيق الحماية
def edit_student(student_id):
    all_students = get_students_data()
    
    student_to_edit = next((student for student in all_students if str(student.get('id')) == student_id), None)
    
    if student_to_edit:
        return render_template('edit_student.html', student=student_to_edit)
    
    flash("Erreur : Étudiant à modifier non trouvé.", 'error')
    return redirect(url_for('show_students'))


@app.route('/update/<student_id>', methods=['POST'])
@login_required # 💡 تطبيق الحماية
def update_student(student_id):
    all_students = get_students_data()
    
    for student in all_students:
        if str(student.get('id')) == student_id:
            
            student['name'] = request.form['name']
            student['email'] = request.form['email']
            student['classe'] = request.form.get('classe', 'Non spécifiée')
            
            save_students_data(all_students)
            flash("Succès : Informations de l'étudiant mises à يوم.", 'success')
            return redirect(url_for('show_students'))
            
    flash("Erreur : Impossible de mettre à jour. Étudiant non trouvé.", 'error')
    return redirect(url_for('show_students'))

if __name__ == '__main__':
    # تأكد أنك لا تستخدم هذا التشغيل في بيئة الإنتاج على Render
    app.run(debug=True)