from flask import Flask, render_template, request, redirect, url_for, flash, session # 💡 تم إضافة 'session'
import json
import os

app = Flask(__name__)
# مفتاح سري ضروري لتشغيل flash والجلسات (Sessions)
app.secret_key = 'votre_cle_secrete_ici' 

# 💡 بيانات الدخول (جديدة)
ADMIN_USERNAME = 'mohamed.cyber@hotmail'
ADMIN_PASSWORD = 'MHD#MDH' # ملاحظة: في بيئة العمل الحقيقية، يجب تشفير كلمة المرور!

# --- وظائف التعامل مع JSON ---
def get_students_data():
    """Lis les données des étudiants depuis le fichier JSON."""
    try:
        with open('students.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_students_data(data):
    """Enregistre les données des étudiants dans le fichier JSON."""
    with open('students.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
# ----------------------------------------

# 1. الصفحة الرئيسية
@app.route('/')
def index():
    # تمرير حالة الدخول إلى القالب لتعديل شريط التنقل
    return render_template('index.html')

# 2. صفحة التسجيل 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        
        new_id = request.form.get('id')
        new_email = request.form['email']
        all_students = get_students_data()

        # منطق التحقق من تكرار الـ ID والـ Email
        id_exists = any(str(student.get('id')) == new_id for student in all_students)
        email_exists = any(student.get('email') == new_email for student in all_students)
        
        if id_exists:
            flash(f"Erreur : Le Numéro ID '{new_id}' est déjà utilisé. Veuillez en choisir un autre.", 'error')
            return redirect(url_for('register'))
            
        if email_exists:
            flash(f"Erreur : L'Email '{new_email}' est déjà utilisé. Veuillez en choisir un autre.", 'error')
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

# 3. صفحة عرض الجدول (مُحمية)
@app.route('/students')
def show_students():
    # 💡 التحقق من تسجيل الدخول: إذا لم يكن 'logged_in' في الجلسة، قم بإعادة التوجيه لصفحة الدخول
    if 'logged_in' not in session or not session['logged_in']:
        flash("Veuillez vous connecter pour accéder à la liste des étudiants.", 'error')
        return redirect(url_for('login'))
        
    students = get_students_data()
    return render_template('students_table.html', students=students)


# ----------------------------------------------------
# 💡 الدوال الجديدة: الدخول والخروج
# ----------------------------------------------------

# 4. دالة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Succès : Connexion réussie!', 'success')
            # إعادة التوجيه إلى قائمة الطلاب بعد الدخول الناجح
            return redirect(url_for('show_students'))
        else:
            flash('Erreur : Nom d\'utilisateur ou mot de passe incorrect.', 'error')
            
    # تمرير حالة الدخول إلى القالب لتعديل شريط التنقل
    return render_template('login.html')

# 5. دالة تسجيل الخروج
@app.route('/logout')
def logout():
    session.pop('logged_in', None) # إزالة مفتاح 'logged_in' من الجلسة
    flash('Succès : Vous avez été déconnecté.', 'success')
    return redirect(url_for('index'))


# ----------------------------------------------------
# 💡 الدوال المُعدَّلة: الحذف والتعديل (تتطلب حماية الآن)
# ----------------------------------------------------

@app.route('/delete/<student_id>', methods=['POST'])
def delete_student(student_id):
    # 💡 الحماية
    if 'logged_in' not in session or not session['logged_in']:
        flash("Erreur : Accès refusé. Veuillez vous connecter.", 'error')
        return redirect(url_for('login'))
        
    all_students = get_students_data()
    
    updated_students = [student for student in all_students if str(student.get('id')) != student_id]
    
    if len(updated_students) < len(all_students):
        save_students_data(updated_students)
        flash("Succès : Étudiant supprimé avec succès.", 'success')
    else:
        flash("Erreur : Étudiant non trouvé.", 'error')
        
    return redirect(url_for('show_students'))


@app.route('/edit/<student_id>', methods=['GET'])
def edit_student(student_id):
    # 💡 الحماية
    if 'logged_in' not in session or not session['logged_in']:
        flash("Erreur : Accès refusé. Veuillez vous connecter.", 'error')
        return redirect(url_for('login'))
        
    all_students = get_students_data()
    
    student_to_edit = next((student for student in all_students if str(student.get('id')) == student_id), None)
    
    if student_to_edit:
        return render_template('edit_student.html', student=student_to_edit)
    
    flash("Erreur : Étudiant à modifier non trouvé.", 'error')
    return redirect(url_for('show_students'))


@app.route('/update/<student_id>', methods=['POST'])
def update_student(student_id):
    # 💡 الحماية
    if 'logged_in' not in session or not session['logged_in']:
        flash("Erreur : Accès  refusé. Veuillez vous connecter.", 'error')
        return redirect(url_for('login'))
        
    all_students = get_students_data()
    
    for student in all_students:
        if str(student.get('id')) == student_id:
            
            student['name'] = request.form['name']
            student['email'] = request.form['email']
            student['classe'] = request.form.get('classe', 'Non spécifiée')
            
            save_students_data(all_students)
            flash("Succès : Informations de l'étudiant mises à jour.", 'success')
            return redirect(url_for('show_students'))
            
    flash("Erreur : Impossible de mettre à jour. Étudiant non trouvé.", 'error')
    return redirect(url_for('show_students'))

if __name__ == '__main__':
    app.run(debug=True)