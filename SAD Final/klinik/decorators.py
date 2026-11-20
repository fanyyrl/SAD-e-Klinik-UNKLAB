from functools import wraps
from django.shortcuts import render
from django.http import HttpResponseForbidden


def role_required(allowed_roles):
    """
    Decorator untuk membatasi akses view berdasarkan peran pengguna.
    Mengembalikan HTTP 403 Forbidden jika pengguna tidak memiliki hak akses.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.shortcuts import redirect
                from django.conf import settings
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")

            # Superuser memiliki akses khusus untuk pemeliharaan/admin
            user_role = getattr(request.user, 'role_akses', None)
            if user_role in allowed_roles or (request.user.is_superuser and 'staf_klinik' in allowed_roles):
                return view_func(request, *args, **kwargs)

            # Jika peran tidak diizinkan, kembalikan HTTP 403 Forbidden
            context = {
                'judul': '403 Akses Ditolak',
                'pesan': f"Akses ditolak: Peran Anda ({request.user.get_role_akses_display() if hasattr(request.user, 'get_role_akses_display') else request.user.username}) tidak memiliki izin untuk mengakses halaman ini.",
                'peran_diizinkan': [('Staf Klinik' if r == 'staf_klinik' else 'Dokter') for r in allowed_roles]
            }
            return render(request, 'errors/403.html', context, status=403)
        return _wrapped_view
    return decorator
