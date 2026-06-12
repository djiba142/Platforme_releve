from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from etudiants.models import Etudiant, Departement, Niveau, Session, ProfilAdmin
from notes.models import Note, ImportNotes
from demandes.models import Demande
from releves.models import Releve
from etudiants.permissions import est_admin, est_directeur, est_chef_dept, get_filiere_admin
from releves.utils.generate_pdf import generer_releve


# ── Helpers d'accès ──────────────────────────

def _get_profil(user):
    try:   return user.profiladmin
    except: return None

def _est_super_admin(user):
    if not user.is_authenticated or not user.is_staff: return False
    if user.is_superuser: return True
    try: return user.profiladmin.role == 'admin'
    except: return False

def _est_direction(user):
    """DG ou DGA."""
    try: return user.profiladmin.role in ['dg', 'dga']
    except: return False

def _est_chef(user):
    """Chef de département."""
    try: return user.profiladmin.role in ['chef_ntic', 'chef_dl']
    except: return False

def _filiere_chef(user):
    try:
        role = user.profiladmin.role
        if role == 'chef_ntic': return '6642', 'NTIC'
        if role == 'chef_dl':   return '6644', 'DL'
    except: pass
    return None, None


# ═══════════════════════════════════════════════
# DASHBOARD SUPER ADMIN (Centre Informatique)
# ═══════════════════════════════════════════════
@login_required
def admin_dashboard(request):
    if not _est_super_admin(request.user):
        messages.error(request, 'Accès réservé au Centre Informatique.')
        return redirect('accueil')

    profil = _get_profil(request.user)
    cadres = ProfilAdmin.objects.select_related('user').all().order_by('role', 'nom')

    total_etudiants      = Etudiant.objects.count()
    etudiants_actifs     = Etudiant.objects.filter(est_valide=True).count()
    etudiants_att_chef   = Etudiant.objects.filter(est_valide=False, valide_par_chef=False).count()
    etudiants_att_dg     = Etudiant.objects.filter(est_valide=False, valide_par_chef=True).count()
    total_demandes       = Demande.objects.count()
    demandes_en_attente  = Demande.objects.filter(statut='en_attente').count()
    demandes_validees    = Demande.objects.filter(statut='validee').count()
    total_releves        = Releve.objects.count()
    total_notes          = Note.objects.count()
    dernieres_demandes   = Demande.objects.select_related('etudiant__user').order_by('-date_demande')[:8]

    return render(request, 'administration/dashboard.html', {
        'profil': profil, 'cadres': cadres,
        'nb_dg':   cadres.filter(role='dg').count(),
        'nb_dga':  cadres.filter(role='dga').count(),
        'nb_chef': cadres.filter(role__startswith='chef').count(),
        'nb_comptes_actifs': cadres.filter(user__is_active=True).count(),
        'nb_etudiants': total_etudiants,
        'nb_actifs': etudiants_actifs,
        'nb_att_chef': etudiants_att_chef,
        'nb_att_dg':   etudiants_att_dg,
        'nb_demandes': total_demandes,
        'nb_attente':  demandes_en_attente,
        'nb_validees': demandes_validees,
        'nb_releves':  total_releves,
        'nb_notes':    total_notes,
        'dernières_demandes': dernieres_demandes,
        'role_choices': ProfilAdmin.ROLE_CHOICES,
    })


# ── Créer / Désactiver utilisateurs cadres ──
@login_required
def creer_utilisateur(request):
    if not _est_super_admin(request.user):
        return redirect('accueil')
    if request.method != 'POST':
        return redirect('admin_dashboard')

    nom=request.POST.get('nom','').strip(); prenom=request.POST.get('prenom','').strip()
    email=request.POST.get('email','').strip(); telephone=request.POST.get('telephone','').strip()
    role=request.POST.get('role',''); password=request.POST.get('password','')

    if not all([nom,prenom,email,role,password]):
        messages.error(request,'Tous les champs obligatoires doivent être remplis.')
        return redirect('admin_dashboard')
    if User.objects.filter(email=email).exists():
        messages.error(request,f'Un compte avec l\'email {email} existe déjà.')
        return redirect('admin_dashboard')

    username = f"{prenom.lower()}.{nom.lower()}".replace(' ','').replace('-','')
    if User.objects.filter(username=username).exists():
        username = f"{username}{User.objects.count()}"

    try:
        user = User.objects.create_user(username=username,email=email,password=password,
                                        first_name=prenom,last_name=nom,is_staff=True)
        ProfilAdmin.objects.create(user=user,role=role,nom=nom,prenom=prenom,
                                   email=email,telephone=telephone)
        messages.success(request,
            f'Compte créé : {prenom} {nom} ({dict(ProfilAdmin.ROLE_CHOICES).get(role)}). '
            f'Identifiant : {username}')
    except Exception as e:
        messages.error(request,f'Erreur : {e}')
    return redirect('admin_dashboard')


@login_required
def toggle_utilisateur(request, user_id):
    if not _est_super_admin(request.user): return redirect('accueil')
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        messages.warning(request,'Vous ne pouvez pas désactiver votre propre compte.')
        return redirect('admin_dashboard')
    target.is_active = not target.is_active; target.save()
    messages.success(request,f'Compte {"activé" if target.is_active else "désactivé"}.')
    return redirect('admin_dashboard')

# ═══════════════════════════════════════════════
# DASHBOARD CHEF DE DÉPARTEMENT
# ═══════════════════════════════════════════════
@login_required
def dashboard_chef(request):
    if not _est_chef(request.user):
        messages.error(request,'Accès réservé aux Chefs de Département.')
        return redirect('accueil')

    profil = _get_profil(request.user)
    prefix, filiere_label = _filiere_chef(request.user)

    etudiants_att  = Etudiant.objects.filter(est_valide=False, valide_par_chef=False)
    etudiants_tous = Etudiant.objects.all()
    if prefix:
        etudiants_att  = etudiants_att.filter(matricule__startswith=prefix)
        etudiants_tous = etudiants_tous.filter(matricule__startswith=prefix)

    notes_imports = ImportNotes.objects.filter(depose_par=request.user).order_by('-date_depot')[:5]

    return render(request, 'dashboards/chef.html', {
        'profil':        profil,
        'filiere':       filiere_label or 'Toutes filières',
        'etudiants_att': etudiants_att,
        'nb_att':        etudiants_att.count(),
        'nb_etudiants':  etudiants_tous.count(),
        'nb_valides':    etudiants_tous.filter(est_valide=True).count(),
        'notes_imports': notes_imports,
    })


# ── Validation par le chef ──
@login_required
def prevalider_inscription(request, etudiant_id):
    """Chef de département pré-valide → passe en attente DG."""
    if not _est_chef(request.user):
        return redirect('accueil')

    etudiant = get_object_or_404(Etudiant, id=etudiant_id, est_valide=False, valide_par_chef=False)
    prefix, _ = _filiere_chef(request.user)
    # Vérifier que l'étudiant appartient bien à la filière du chef
    if prefix and not etudiant.matricule.startswith(prefix):
        messages.error(request,"Cet étudiant n'appartient pas à votre département.")
        return redirect('dashboard_chef')

    etudiant.valide_par_chef = True
    etudiant.save()
    messages.success(request,
        f"✅ Inscription de {etudiant.prenom} {etudiant.nom} ({etudiant.matricule}) "
        f"pré-validée. Elle attend maintenant l'activation par la Direction.")
    return redirect('dashboard_chef')


@login_required
def rejeter_inscription_chef(request, etudiant_id):
    """Chef de département rejette → supprime le compte."""
    if not _est_chef(request.user):
        return redirect('accueil')

    etudiant = get_object_or_404(Etudiant, id=etudiant_id, est_valide=False, valide_par_chef=False)
    prefix, _ = _filiere_chef(request.user)
    if prefix and not etudiant.matricule.startswith(prefix):
        messages.error(request,"Cet étudiant n'appartient pas à votre département.")
        return redirect('dashboard_chef')

    nom_complet = etudiant.nom_complet
    user = etudiant.user
    etudiant.delete(); user.delete()
    messages.warning(request,f"❌ Inscription de {nom_complet} rejetée et supprimée.")
    return redirect('dashboard_chef')


# ═══════════════════════════════════════════════
# DASHBOARD DGA
# ═══════════════════════════════════════════════
@login_required
def dashboard_dga(request):
    if not _est_direction(request.user):
        messages.error(request,'Accès réservé à la Direction.')
        return redirect('accueil')

    profil = _get_profil(request.user)

    # DGA voit les inscriptions pré-validées par le chef (en attente DG)
    inscriptions_att = Etudiant.objects.filter(est_valide=False, valide_par_chef=True).select_related('user','departement','niveau')
    imports_att      = ImportNotes.objects.filter(statut='depose').order_by('-date_depot')

    return render(request, 'dashboards/dga.html', {
        'profil':           profil,
        'inscriptions_att': inscriptions_att,
        'nb_att_dg':        inscriptions_att.count(),
        'imports_att':      imports_att,
        'nb_imports_att':   imports_att.count(),
        'nb_etudiants':     Etudiant.objects.filter(est_valide=True).count(),
    })


@login_required
def valider_inscription_dga(request, etudiant_id):
    """DGA active le compte étudiant."""
    if not _est_direction(request.user):
        return redirect('accueil')

    etudiant = get_object_or_404(Etudiant, id=etudiant_id, est_valide=False, valide_par_chef=True)
    etudiant.est_valide = True
    etudiant.save()
    messages.success(request,
        f"✅ Compte de {etudiant.nom_complet} ({etudiant.matricule}) activé. "
        f"Il peut désormais se connecter.")
    return redirect('dashboard_dga')


@login_required
def rejeter_inscription_dga(request, etudiant_id):
    """DGA rejette → supprime."""
    if not _est_direction(request.user):
        return redirect('accueil')

    etudiant = get_object_or_404(Etudiant, id=etudiant_id, est_valide=False)
    nom_complet = etudiant.nom_complet
    user = etudiant.user
    etudiant.delete(); user.delete()
    messages.warning(request,f"❌ Inscription de {nom_complet} rejetée.")
    return redirect('dashboard_dga')


# ═══════════════════════════════════════════════
# DASHBOARD DG
# ═══════════════════════════════════════════════
@login_required
def dashboard_dg(request):
    if not _est_direction(request.user):
        messages.error(request,'Accès réservé à la Direction.')
        return redirect('accueil')

    profil = _get_profil(request.user)
    return render(request, 'dashboards/dg.html', {
        'profil':          profil,
        'nb_etudiants':    Etudiant.objects.filter(est_valide=True).count(),
        'nb_demandes':     Demande.objects.count(),
        'nb_att_dg':       Etudiant.objects.filter(est_valide=False, valide_par_chef=True).count(),
        'imports_att_dg':  ImportNotes.objects.filter(statut='valide_dga').order_by('-date_depot'),
        'nb_imports_dg':   ImportNotes.objects.filter(statut='valide_dga').count(),
    })


# ═══════════════════════════════════════════════
# GESTION INSCRIPTIONS (Direction)
# ═══════════════════════════════════════════════
@login_required
def gestion_inscriptions(request):
    """Liste unifiée : direction voit tout, chef voit son dept."""
    if not est_admin(request.user):
        return redirect('login_admin')

    profil = _get_profil(request.user)

    if _est_chef(request.user):
        prefix, _ = _filiere_chef(request.user)
        inscriptions = Etudiant.objects.filter(
            est_valide=False, valide_par_chef=False,
            matricule__startswith=prefix if prefix else ''
        ).select_related('user','departement','niveau').order_by('-date_inscription')
    else:
        # Direction voit les pré-validés par les chefs
        inscriptions = Etudiant.objects.filter(
            est_valide=False, valide_par_chef=True
        ).select_related('user','departement','niveau').order_by('-date_inscription')

    return render(request,'administration/inscriptions.html',{
        'inscriptions': inscriptions,
        'profil': profil,
        'est_directeur': _est_direction(request.user),
        'est_chef': _est_chef(request.user),
    })


@login_required
def valider_inscription(request, etudiant_id):
    if not _est_direction(request.user):
        return redirect('admin_dashboard')
    etudiant = get_object_or_404(Etudiant, id=etudiant_id, est_valide=False)
    etudiant.est_valide = True; etudiant.save()
    messages.success(request,f"✅ Compte de {etudiant.nom_complet} activé.")
    return redirect('gestion_inscriptions')


@login_required
def rejeter_inscription(request, etudiant_id):
    if not _est_direction(request.user):
        return redirect('admin_dashboard')
    etudiant = get_object_or_404(Etudiant, id=etudiant_id, est_valide=False)
    nom = etudiant.nom_complet; user = etudiant.user
    etudiant.delete(); user.delete()
    messages.warning(request,f"❌ Inscription de {nom} rejetée.")
    return redirect('gestion_inscriptions')


# ═══════════════════════════════════════════════
# ÉTUDIANTS
# ═══════════════════════════════════════════════
@login_required
def liste_etudiants(request):
    if not est_admin(request.user): return redirect('login_admin')
    profil  = _get_profil(request.user)
    prefix  = get_filiere_admin(request.user)
    qs = Etudiant.objects.select_related('user','departement','niveau').order_by('matricule')
    if prefix: qs = qs.filter(matricule__startswith=prefix)
    return render(request,'administration/liste_etudiants.html',{
        'etudiants': qs, 'profil': profil,
        'est_directeur': est_directeur(request.user),
        'est_chef': est_chef_dept(request.user),
    })


@login_required
def ajouter_etudiant(request):
    if not est_admin(request.user): return redirect('login_admin')
    if request.method == 'POST':
        matricule = request.POST.get('matricule','').strip().upper()
        nom       = request.POST.get('nom','').strip()
        prenom    = request.POST.get('prenom','').strip()
        dept_id   = request.POST.get('departement','').strip()
        niv_id    = request.POST.get('niveau','').strip()
        password  = request.POST.get('password','').strip() or 'changeme123'

        if Etudiant.objects.filter(matricule=matricule).exists():
            messages.error(request,f'Le matricule {matricule} existe déjà.')
            return redirect('ajouter_etudiant')
        try:
            user = User.objects.create_user(username=matricule, password=password)
            Etudiant.objects.create(user=user,matricule=matricule,nom=nom,prenom=prenom,
                departement_id=dept_id or None,niveau_id=niv_id or None,est_valide=True,valide_par_chef=True)
            messages.success(request,f'Étudiant {prenom} {nom} ajouté.')
            return redirect('liste_etudiants')
        except Exception as e:
            messages.error(request,f'Erreur : {e}')

    return render(request,'administration/ajouter_etudiant.html',{
        'departements': Departement.objects.all(),
        'niveaux': Niveau.objects.all(),
        'profil': _get_profil(request.user),
    })


@login_required
def supprimer_etudiant(request, etudiant_id):
    if not _est_super_admin(request.user): return redirect('accueil')
    etudiant = get_object_or_404(Etudiant, id=etudiant_id)
    nom = etudiant.nom_complet; user = etudiant.user
    etudiant.delete(); user.delete()
    messages.success(request,f'Étudiant {nom} supprimé.')
    return redirect('liste_etudiants')


# ═══════════════════════════════════════════════
# NOTES
# ═══════════════════════════════════════════════
@login_required
def gestion_notes(request):
    if not est_admin(request.user): return redirect('login_admin')
    profil  = _get_profil(request.user)
    prefix  = get_filiere_admin(request.user)
    imports = ImportNotes.objects.order_by('-date_depot')
    notes   = Note.objects.select_related('etudiant','session').order_by('-id')[:50]
    # Étudiants actifs pour le formulaire d'ajout manuel
    etudiants_qs = Etudiant.objects.filter(est_valide=True).select_related('departement','niveau').order_by('matricule')
    if prefix:
        imports = imports.filter(filiere=('NTIC' if prefix=='6642' else 'DL'))
        notes   = notes.filter(etudiant__matricule__startswith=prefix)
        etudiants_qs = etudiants_qs.filter(matricule__startswith=prefix)
    sessions_all = Session.objects.all()
    return render(request,'administration/gestion_notes.html',{
        'profil': profil, 'imports': imports, 'notes': notes,
        'sessions': sessions_all,
        'etudiants': etudiants_qs,
        'est_directeur': _est_direction(request.user),
        'est_chef': _est_chef(request.user),
    })


@login_required
def ajouter_note(request):
    if not est_admin(request.user): return redirect('login_admin')
    if request.method == 'POST':
        # Le select envoie l'ID de l'étudiant
        etudiant_id = request.POST.get('etudiant', '').strip()
        matiere     = request.POST.get('matiere', '').strip()
        note_val    = request.POST.get('note', '0')
        session_id  = request.POST.get('session', '')
        annee       = request.POST.get('annee', '2024-2025').strip()

        if not etudiant_id:
            messages.error(request, 'Veuillez sélectionner un étudiant.')
            return redirect('gestion_notes')
        if not matiere:
            messages.error(request, 'Veuillez sélectionner une matière.')
            return redirect('gestion_notes')

        try:
            etudiant = Etudiant.objects.get(id=int(etudiant_id))
            session  = Session.objects.get(id=session_id)
            note_float = float(str(note_val).replace(',','.'))
            if not (0 <= note_float <= 20):
                messages.error(request, f'La note doit être entre 0 et 20.')
                return redirect('gestion_notes')
            note_obj, created = Note.objects.update_or_create(
                etudiant=etudiant,
                matiere=matiere,
                session=session,
                annee=annee,
                defaults={'note': note_float}
            )
            action = "ajoutée" if created else "mise à jour"
            messages.success(request,
                f'✅ Note {action} : {etudiant.matricule} — {matiere} — {note_float}/20 (Session : {session.nom})')
        except Etudiant.DoesNotExist:
            messages.error(request, 'Étudiant introuvable.')
        except Session.DoesNotExist:
            messages.error(request, 'Session introuvable.')
        except (ValueError, TypeError) as e:
            messages.error(request, f'Valeur de note invalide : {e}')
        except Exception as e:
            messages.error(request, f'Erreur : {e}')
    return redirect('gestion_notes')


# ═══════════════════════════════════════════════
# DEMANDES
# ═══════════════════════════════════════════════
@login_required
def gestion_demandes(request):
    if not est_admin(request.user): return redirect('login_admin')
    profil   = _get_profil(request.user)
    prefix   = get_filiere_admin(request.user)
    demandes = Demande.objects.select_related('etudiant__user').order_by('-date_demande')
    if prefix: demandes = demandes.filter(etudiant__matricule__startswith=prefix)
    return render(request,'administration/gestion_demandes.html',{
        'demandes': demandes, 'profil': profil,
        'est_directeur': _est_direction(request.user),
        'est_chef': _est_chef(request.user),
    })


@login_required
def valider_demande(request, demande_id):
    if not est_admin(request.user): return redirect('login_admin')
    demande = get_object_or_404(Demande, id=demande_id)
    demande.statut = 'validee'; demande.save()
    # Générer PDF immédiatement
    try:
        chemin = generer_releve(demande)
        Releve.objects.update_or_create(demande=demande, defaults={'fichier_pdf': chemin})
    except Exception as e:
        messages.warning(request,f'Demande validée mais erreur génération PDF : {e}')
    messages.success(request,f'✅ Demande de {demande.etudiant.nom_complet} validée, PDF généré.')
    return redirect('gestion_demandes')


@login_required
def rejeter_demande(request, demande_id):
    if not est_admin(request.user): return redirect('login_admin')
    demande = get_object_or_404(Demande, id=demande_id)
    demande.statut = 'rejetee'; demande.save()
    messages.warning(request,f'Demande de {demande.etudiant.nom_complet} rejetée.')
    return redirect('gestion_demandes')
