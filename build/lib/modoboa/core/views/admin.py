"""
Views available to super administrators only.
"""

from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from django.contrib.auth.decorators import (
    login_required, user_passes_test
)


from modoboa.core.models import Extension, Log
from modoboa.core.utils import new_version_available
from modoboa.lib import events, parameters
from modoboa.lib.listing import get_sort_order, get_listing_page
from modoboa.lib.webutils import (
    _render_to_string, render_to_json_response
)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewsettings(request, tplname='core/settings_header.html'):
    return render(request, tplname, {
        "selection": "settings"
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewparameters(request, tplname='core/parameters.html'):
    return render_to_json_response({
        "left_selection": "parameters",
        "content": _render_to_string(request, tplname, {
            "forms": parameters.get_admin_forms
        })
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def saveparameters(request):
    for formdef in parameters.get_admin_forms(request.POST):
        form = formdef["form"]
        if form.is_valid():
            form.save()
            form.to_django_settings()
            continue
        return render_to_json_response(
            {'form_errors': form.errors, 'prefix': form.app}, status=400
        )
    return render_to_json_response(_("Parameters saved"))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewextensions(request, tplname='core/extensions.html'):
    """List available extensions."""
    from modoboa.core.extensions import exts_pool

    exts = exts_pool.list_all()
    for ext in exts:
        try:
            dbext = Extension.objects.get(name=ext["id"])
            ext["selection"] = dbext.enabled
        except Extension.DoesNotExist:
            dbext = Extension()
            dbext.name = ext["id"]
            dbext.enabled = False
            dbext.save()
            ext["selection"] = False

    return render_to_json_response({
        "callback": "extensions",
        "content": _render_to_string(request, tplname, {"extensions": exts})
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def saveextensions(request):
    """Enable of disable extension(s)."""
    actived_exts = Extension.objects.filter(enabled=True)
    found = []
    for k in request.POST.keys():
        if k.startswith("select_"):
            parts = k.split("_", 1)
            dbext = Extension.objects.get(name=parts[1])
            if not dbext in actived_exts:
                dbext.on()
            else:
                found += [dbext]
    for ext in actived_exts:
        if not ext in found:
            ext.off()

    return render_to_json_response(_("Modifications applied."))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def information(request, tplname="core/information.html"):
    return render_to_json_response({
        "content": render_to_string(tplname, {
            "new_version": new_version_available(request)
        }),
    })


def get_logs_page(request, page_id=None):
    """Return a page of logs."""
    sort_order, sort_dir = get_sort_order(
        request.GET, "date_created",
        allowed_values=['date_created', 'level', 'logger', 'message']
    )
    if page_id is None:
        page_id = request.GET.get("page", None)
        if page_id is None:
            return None
    return get_listing_page(
        Log.objects.all().order_by("%s%s" % (sort_dir, sort_order)),
        page_id
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def logs(request, tplname="core/logs.html"):
    """Return a list of log entries.

    This view is only called the first time the page is displayed.

    """
    page = get_logs_page(request, 1)
    return render_to_json_response({
        "callback": "logs",
        "content": render_to_string(tplname, {"logs": page.object_list}),
        "page": page.number
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def logs_page(request, tplname="core/logs_page.html"):
    """Return a page containing logs."""
    page = get_logs_page(request)
    if page is None:
        context = {"length": 0}
    else:
        context = {
            "rows": render_to_string(tplname, {"logs": page.object_list}),
            "pages": [page.number]
        }
    return render_to_json_response(context)


@login_required
def check_top_notifications(request):
    """
    AJAX service to check for new top notifications to display.
    """
    return render_to_json_response(
        events.raiseQueryEvent("TopNotifications", request, True)
    )
