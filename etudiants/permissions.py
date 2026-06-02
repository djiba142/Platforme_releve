def est_directeur(user):
    """DG ou DGA."""
    try:
        return user.profiladmin.role in ['dg', 'dga']
    except:
        return False


def est_chef_dept(user):
    """Chef de département NTIC ou DL."""
    try:
        return user.profiladmin.role in ['chef_ntic', 'chef_dl']
    except:
        return False


def est_admin(user):
    """Tous les admins."""
    try:
        return user.profiladmin is not None
    except:
        return False


def get_filiere_admin(user):
    """Retourne la filière gérée par le chef de département."""
    try:
        role = user.profiladmin.role
        if role == 'chef_ntic':
            return '6642'
        elif role == 'chef_dl':
            return '6644'
        else:
            return None  # DG/DGA voient tout
    except:
        return None
