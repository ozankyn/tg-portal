# -*- coding: utf-8 -*-
"""
TG Portal - Application Entry Point
Team Guerilla ERP Sistemi
"""

import os
from app import create_app, db

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Flask shell için context"""
    from app.models import (
        User, Role, Permission,
        Calisan, Departman, Pozisyon,
        Arac, FiloIslem,
        Tedarikci
    )
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'Permission': Permission,
        'Calisan': Calisan,
        'Departman': Departman,
        'Pozisyon': Pozisyon,
        'Arac': Arac,
        'FiloIslem': FiloIslem,
        'Tedarikci': Tedarikci
    }


if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
