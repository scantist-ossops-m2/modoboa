# coding: utf-8

"""
This module contains extra functions/shortcuts used to render HTML.
"""
import sys
import re
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response
from django.template.loader import render_to_string
from django import template
from django.conf import settings


def _render_to_string(request, tpl, user_context):
    """Custom rendering function.

    Just a wrapper which automatically adds a RequestContext instance
    (useful to use settings variables like STATIC_URL inside templates)
    """
    return render_to_string(tpl, user_context,
                            context_instance=template.RequestContext(request))


def _render_error(request, errortpl="error", user_context=None):
    if user_context is None:
        user_context = {}
    return render(
        request, "common/%s.html" % errortpl, user_context
    )


def render_actions(actions):
    t = template.Template("""{% load lib_tags %}
{% for a in actions %}{% render_link a %}{% endfor %}
""")
    return t.render(template.Context(dict(actions=actions)))


def getctx(status, level=1, callback=None, **kwargs):
    if not callback:
        callername = sys._getframe(level).f_code.co_name
    else:
        callername = callback
    ctx = {"status": status, "callback": callername}
    for kw, v in kwargs.iteritems():
        ctx[kw] = v
    return ctx


def ajax_response(request, status="ok", respmsg=None,
                  url=None, ajaxnav=False, norefresh=False, 
                  template=None, **kwargs):
    """Ajax response shortcut

    Simple shortcut that sends an JSON response. If a template is
    provided, a 'content' field will be added to the response,
    containing the result of this template rendering.

    :param request: a Request object
    :param status: the response status ('ok' or 'ko)
    :param respmsg: the message that will displayed in the interface
    :param url: url to display after receiving this response
    :param ajaxnav:
    :param norefresh: do not refresh the page after receiving this response
    :param template: eventual template's path
    :param kwargs: dict used for template rendering
    """
    ctx = {}
    for k, v in kwargs.iteritems():
        ctx[k] = v
    if template is not None:
        content = _render_to_string(request, template, ctx)
    elif kwargs.has_key("content"):
        content = kwargs["content"]
    else:
        content = ""
    jsonctx = {"status": status, "content": content}
    if respmsg is not None:
        jsonctx["respmsg"] = respmsg
    if ajaxnav:
        jsonctx["ajaxnav"] = True
    if url is not None:
        jsonctx["url"] = url
    jsonctx["norefresh"] = norefresh
    return HttpResponse(json.dumps(jsonctx), mimetype="application/json")


def render_to_json_response(context, **response_kwargs):
    """Simple shortcut to render a JSON response.

    :param dict context: response content
    :return: ``HttpResponse`` object
    """
    data = json.dumps(context)
    response_kwargs['content_type'] = 'application/json'
    return HttpResponse(data, **response_kwargs)


def static_url(path):
    """Returns the correct static url for a given file

    :param path: the targeted static media
    """
    if path.startswith("/"):
        path = path[1:]
    return "%s%s" % (settings.STATIC_URL, path)


def size2integer(value):
    """Try to convert a string representing a size to an integer value
    in bytes.

    Supported formats:
    * K|k for KB
    * M|m for MB
    * G|g for GB

    :param value: the string to convert
    :return: the corresponding integer value
    """
    m = re.match("(\d+)\s*(\w+)", value)
    if m is None:
        if re.match("\d+", value):
            return int(value)
        return 0
    if m.group(2)[0] in ["K", "k"]:
        return int(m.group(1)) * 2 ** 10
    if m.group(2)[0] in ["M", "m"]:
        return int(m.group(1)) * 2 ** 20
    if m.group(2)[0] in ["G", "g"]:
        return int(m.group(1)) * 2 ** 30
    return 0


@login_required
def topredirection(request):
    """Simple view to redirect the request when no application is specified.

    The default "top redirection" can be specified in the *Admin >
    Settings* panel. It is the application that will be launched by
    default. Users that are not allowed to access this application
    will be redirected to the "User preferences" application.

    This feature only applies to simple users.

    :param request: a Request object
    """
    from modoboa.lib import parameters
    from modoboa.core.extensions import exts_pool

    topredir = parameters.get_admin("DEFAULT_TOP_REDIRECTION", app="core")
    infos = exts_pool.get_extension_infos(topredir)
    path = infos["url"] if infos["url"] else infos["name"]
    return HttpResponseRedirect(path)
