# -*- coding: utf-8 -*-
"""
TG Portal - REST API Routes
Version: v1
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.core import User
from app.models.ik import Calisan, Departman
from app.models.filo import Arac
from app.models.tedarikci import Tedarikci
from app.models.base import CalisanDurumu, AracDurumu
from app.utils import permission_required

api_bp = Blueprint('api', __name__)


# ==================== HEALTH CHECK ====================

@api_bp.route('/health')
def health():
    """API health check"""
    return jsonify({
        'status': 'ok',
        'version': 'v1',
        'service': 'tg-portal'
    })


# ==================== AUTH ====================

@api_bp.route('/me')
@login_required
def me():
    """Mevcut kullanıcı bilgileri"""
    return jsonify(current_user.to_dict())


# ==================== ÇALIŞANLAR ====================

@api_bp.route('/calisanlar')
@login_required
@permission_required('ik.view')
def calisanlar_liste():
    """Çalışan listesi API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    aktif = request.args.get('aktif', '1')
    
    query = Calisan.query.filter_by(is_deleted=False)
    
    if aktif == '1':
        query = query.filter(Calisan.durum == CalisanDurumu.AKTIF)
    
    pagination = query.order_by(Calisan.ad).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@api_bp.route('/calisanlar/<int:id>')
@login_required
@permission_required('ik.view')
def calisan_detay(id):
    """Çalışan detay API"""
    calisan = Calisan.query.get_or_404(id)
    return jsonify(calisan.to_dict())


# ==================== ARAÇLAR ====================

@api_bp.route('/araclar')
@login_required
@permission_required('filo.view')
def araclar_liste():
    """Araç listesi API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Arac.query.filter_by(is_deleted=False)
    
    pagination = query.order_by(Arac.plaka).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@api_bp.route('/araclar/<int:id>')
@login_required
@permission_required('filo.view')
def arac_detay(id):
    """Araç detay API"""
    arac = Arac.query.get_or_404(id)
    return jsonify(arac.to_dict())


# ==================== TEDARİKÇİLER ====================

@api_bp.route('/tedarikciler')
@login_required
@permission_required('tedarikci.view')
def tedarikciler_liste():
    """Tedarikçi listesi API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    tip = request.args.get('tip')
    
    query = Tedarikci.query.filter_by(is_deleted=False, aktif=True)
    
    if tip:
        from app.models.base import TedarikciTipi
        query = query.filter(Tedarikci.tip == TedarikciTipi(tip))
    
    pagination = query.order_by(Tedarikci.unvan).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@api_bp.route('/tedarikciler/<int:id>')
@login_required
@permission_required('tedarikci.view')
def tedarikci_detay(id):
    """Tedarikçi detay API"""
    tedarikci = Tedarikci.query.get_or_404(id)
    return jsonify(tedarikci.to_dict_full())


# ==================== DEPARTMANLAR ====================

@api_bp.route('/departmanlar')
@login_required
def departmanlar_liste():
    """Departman listesi API"""
    departmanlar = Departman.query.filter_by(aktif=True).order_by(Departman.ad).all()
    return jsonify([
        {'id': d.id, 'ad': d.ad, 'kod': d.kod}
        for d in departmanlar
    ])


# ==================== STATS ====================

@api_bp.route('/stats')
@login_required
def stats():
    """Genel istatistikler"""
    return jsonify({
        'calisanlar': {
            'aktif': Calisan.query.filter_by(is_deleted=False, durum=CalisanDurumu.AKTIF).count(),
            'toplam': Calisan.query.filter_by(is_deleted=False).count()
        },
        'araclar': {
            'aktif': Arac.query.filter_by(is_deleted=False, durum=AracDurumu.AKTIF).count(),
            'toplam': Arac.query.filter_by(is_deleted=False).count()
        },
        'tedarikciler': {
            'aktif': Tedarikci.query.filter_by(is_deleted=False, aktif=True).count(),
            'toplam': Tedarikci.query.filter_by(is_deleted=False).count()
        }
    })
