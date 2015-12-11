"""This module provides the views for the explorer interface."""

import json
from django.shortcuts import render_to_response
from django.template import RequestContext
from mpcontribs.rest.rester import MPContribsRester

def get_endpoint():
    from django.core.urlresolvers import reverse
    return reverse('mpcontribs_rest_index')[:-1]

def index(request, collection=None):
    ctx = RequestContext(request)
    fields = ['identifiers', 'projects', 'cids']
    if request.user.is_authenticated():
        if collection in ['materials', 'compositions']:
            API_KEY = request.user.api_key
            ENDPOINT = request.build_absolute_uri(get_endpoint())
            with MPContribsRester(API_KEY, endpoint=ENDPOINT) as mpr:
                if request.method == 'GET':
                    options = dict((field, set()) for field in fields)
                    docs = mpr.query_contributions(collection=collection)
                    if docs:
                        for doc in docs:
                            for project, contribs in doc.iteritems():
                                if project == '_id':
                                    # contribs = mp-id or composition
                                    options[fields[0]].add(str(contribs))
                                else:
                                    options[fields[1]].add(str(project))
                                    # contribs = contributions for specific project
                                    for cid in contribs:
                                        options[fields[2]].add(str(cid))
                    else:
                        ctx.update({'alert': 'No {} available!'.format(collection)})
                    options = dict((k, list(v)) for k,v in options.iteritems())
                    selection = dict((field, []) for field in fields)
                elif request.method == 'POST':
                    options, selection = (
                        dict(
                            (field, [str(el) for el in json.loads(
                                request.POST['_'.join([prefix, field])]
                            )]) for field in fields
                        ) for prefix in ['options', 'selection']
                    )
                    mode = request.POST['submit']
                    if mode == "Find":
                        criteria, keys = {}, ['mp_cat_id', 'project']
                        for idx, key in enumerate(keys):
                            if selection[fields[idx]]:
                                criteria.update({
                                    key: {'$in': selection[fields[idx]]}
                                })
                        urls = [
                            '/'.join([
                                request.path, doc['mp_cat_id'], doc['project'], doc['_id']
                            ]) for doc in mpr.query_contributions(
                                criteria=criteria,
                                projection=dict((key, 1) for key in keys),
                                collection='contributions'
                            )
                        ]
                    else:
                        pass # TODO mpr request for mode == 'Show'
        else:
            ctx.update({'alert': 'Collection {} does not exist!'.format(collection)})
    else:
        ctx.update({'alert': 'Please log in!'})
    return render_to_response("mpcontribs_explorer_index.html", locals(), ctx)

def contribution(request, collection, identifier, project, cid):
    if request.user.is_authenticated():
        material = {}
        API_KEY = request.user.api_key
        ENDPOINT = request.build_absolute_uri(get_endpoint())
        with MPContribsRester(API_KEY, endpoint=ENDPOINT) as mpr:
            material['contributed_data'] = mpr.query_contributions(
                criteria={'_id': identifier}, collection=collection,
                projection={'_id': 0, '.'.join([project, cid]): 1}
            )[0][project][cid]
        material['pretty_formula'] = identifier
    else:
        material = {k: identifier for k in ['pretty_formula']}
    ctx = RequestContext(request, {'material': jsanitize(material)})
    return render_to_response("mpcontribs_explorer_contribution.html", locals(), ctx)

# Instead of
# from monty.json import jsanitize
# use the following to fix UnicodeEncodeError
# and play nice with utf-8 encoding
from bson import SON
def jsanitize(obj):
    if isinstance(obj, (list, tuple)):
        return [jsanitize(i) for i in obj]
    elif isinstance(obj, dict):
        return SON([
            (unicode(k).encode('utf-8'), jsanitize(v))
            for k, v in obj.items()
        ])
    elif isinstance(obj, (int, float)):
        return obj
    elif obj is None:
        return None
    else:
        return unicode(obj).encode('utf-8')
